"""Rumbo al espanõl: aplicação local, monólito modular, sem dependências externas."""
import argparse
from contextlib import contextmanager
import hashlib
import hmac
import json
import mimetypes
import os
import secrets
import threading
import time
import sqlite3
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from content import LESSONS
from curriculum import QUESTIONS as DIAGNOSTIC
import mentoring
import deadlines
from progression import allowed

ROOT = Path(__file__).parent
DB = Path(os.environ.get('FLUENTIA_DB', str(ROOT / 'data' / 'fluentia.sqlite3')))
PUBLIC = ROOT / 'static'
LOGIN_ATTEMPTS = {}
LOGIN_LOCK = threading.Lock()

def login_allowed(email):
    current = time.monotonic()
    with LOGIN_LOCK:
        for key in list(LOGIN_ATTEMPTS):
            if current - LOGIN_ATTEMPTS[key][0] >= 300:
                del LOGIN_ATTEMPTS[key]
        start, count = LOGIN_ATTEMPTS.get(email, (current, 0))
        if count >= 10 or (email not in LOGIN_ATTEMPTS and len(LOGIN_ATTEMPTS) >= 1000):
            return False
        LOGIN_ATTEMPTS[email] = (start, count + 1)
        return True

def now():
    return datetime.now(timezone.utc)

@contextmanager
def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    try:
        with con:
            yield con
    finally:
        con.close()

def init_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with connect() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, level TEXT DEFAULT 'A1', goal TEXT DEFAULT 'Viagem', daily INTEGER DEFAULT 15, diagnosed INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id INTEGER REFERENCES users(id), expires TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), lesson TEXT, score INTEGER, total INTEGER, created TEXT);
        CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), front TEXT, back TEXT, due TEXT, interval INTEGER DEFAULT 0, UNIQUE(user_id,front));
        CREATE TABLE IF NOT EXISTS notes(user_id INTEGER REFERENCES users(id), lesson TEXT, text TEXT, PRIMARY KEY(user_id,lesson));
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), kind TEXT, payload TEXT, created TEXT);
        CREATE TABLE IF NOT EXISTS access_settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        ''')
        mentoring.migrate(con)

def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    return salt + ':' + hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260000).hex()

def public_lesson(lesson):
    return {**lesson, 'questions': [{k: v for k, v in q.items() if k not in ('answer', 'explanation')} for q in lesson['questions']]}

class Handler(BaseHTTPRequestHandler):
    server_version = 'Rumbo/1.0'

    def reply(self, status, body, cookie=None):
        raw = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()

    def handle_request(self):
        try:
            self.dispatch()
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            self.reply(400, {'error': 'Datos no válidos. Revisa los campos enviados.'})
        except Exception:
            import traceback
            traceback.print_exc()
            self.reply(500, {'error': 'No se pudo completar la operación.'})

    def dispatch(self):
        path = urlparse(self.path).path
        if not path.startswith('/api/'):
            if self.command != 'GET':
                return self.reply(405, {'error': 'Método no permitido.'})
            target = (PUBLIC / ('index.html' if path == '/' else path.lstrip('/'))).resolve()
            if not target.is_relative_to(PUBLIC.resolve()) or not target.is_file():
                return self.reply(404, {'error': 'Archivo no encontrado.'})
            raw = target.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; media-src 'self' blob: data:; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'")
            self.end_headers()
            return self.wfile.write(raw)
        data = {}
        if self.command == 'POST':
            # Evita gravações por formulários de outras origens.
            origin = self.headers.get('Origin')
            if origin and urlparse(origin).netloc != self.headers.get('Host'):
                return self.reply(403, {'error': 'Origen no permitido.'})
            if self.headers.get_content_type() != 'application/json':
                return self.reply(415, {'error': 'Envía JSON.'})
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= (2900000 if path=='/api/oral-practice' else 32768):
                return self.reply(413, {'error': 'Solicitud no válida.'})
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError()
        with connect() as con:
            cookies = SimpleCookie(self.headers.get('Cookie', ''))
            token = cookies['session'].value if 'session' in cookies else ''
            user = con.execute('SELECT u.* FROM users u JOIN sessions s ON u.id=s.user_id WHERE s.token=? AND s.expires>?', (token, now().isoformat())).fetchone()
            if self.command == 'POST' and mentoring.recovery(self, con, path, data, now, password_hash):
                return
            if path in ('/api/register', '/api/login') and self.command == 'POST':
                email = str(data.get('email', '')).strip().lower()
                password = str(data.get('password', ''))
                if path.endswith('register'):
                    if con.execute("SELECT 1 FROM access_settings WHERE key='registration_closed' AND value='1'").fetchone():
                        return self.reply(403, {'error': 'El registro está cerrado. Utiliza tu enlace personal para crear tu contraseña.'})
                    name = str(data.get('name', '')).strip()
                    if not name or len(name) > 80 or '@' not in email or len(email) > 254 or not 8 <= len(password) <= 256:
                        return self.reply(400, {'error': 'Indica nombre, correo y contraseña de 8 a 256 caracteres.'})
                    try:
                        role = data.get('role', 'student')
                        if role not in ('student', 'teacher'):
                            raise ValueError()
                        cur = con.execute('INSERT INTO users(name,email,password,role,invite) VALUES(?,?,?,?,?)', (name, email, password_hash(password), role, secrets.token_urlsafe(12) if role == 'teacher' else None))
                        uid = cur.lastrowid
                    except sqlite3.IntegrityError:
                        return self.reply(409, {'error': 'Correo ya registrado. Inicia sesión.'})
                else:
                    if not login_allowed(email):
                        return self.reply(429, {'error': 'Demasiados intentos. Espera cinco minutos antes de volver a entrar.'})
                    found = con.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
                    if len(password) > 256 or not found or not hmac.compare_digest(found['password'], password_hash(password, found['password'].split(':')[0])):
                        return self.reply(401, {'error': 'Correo o contraseña incorrectos.'})
                    uid = found['id']
                    if data.get('role', found['role']) != found['role']:
                        return self.reply(403, {'error': 'Selecciona el tipo de acceso correspondiente a tu cuenta.'})
                session = secrets.token_urlsafe(32)
                con.execute('DELETE FROM sessions WHERE expires<?', (now().isoformat(),))
                con.execute('INSERT INTO sessions VALUES(?,?,?)', (session, uid, (now() + timedelta(days=7)).isoformat()))
                return self.reply(200, {'ok': True}, 'session=' + session + '; HttpOnly; SameSite=Strict; Path=/; Max-Age=604800' + ('; Secure' if os.getenv('FLUENTIA_SECURE_COOKIE') == '1' else ''))
            if not user:
                return self.reply(401, {'error': 'Inicia sesión para continuar.'})
            uid = user['id']
            if self.command == 'GET':
                if path == '/api/state':
                    profile = {k: user[k] for k in ('name', 'email', 'level', 'goal', 'daily', 'diagnosed', 'role', 'invite')}
                    attempts = [dict(r) for r in con.execute('SELECT * FROM attempts WHERE user_id=? ORDER BY id DESC', (uid,))]
                    reviews = [dict(r) for r in con.execute('SELECT * FROM reviews WHERE user_id=? AND due<=? ORDER BY due', (uid, now().isoformat()))]
                    lesson_levels={text:l['level'] for l in LESSONS for _,text in l['dialogue']}
                    lesson_levels.update({front:l['level'] for l in LESSONS for front,_ in l['vocabulary']})
                    reviews=[r for r in reviews if allowed(user,lesson_levels.get(r['front'],'A1'))]
                    if user['role'] == 'student':
                        attempts = [{k:v for k,v in a.items() if k not in ('score','total')} for a in attempts]
                    return self.reply(200, {'profile': profile, 'lessons': [public_lesson(l) for l in LESSONS if allowed(user,l['level'])], 'diagnostic': [{k: v for k,v in q.items() if k not in ('answer','explanation')} for q in DIAGNOSTIC], 'attempts': attempts, 'reviews': reviews, 'notes': {r['lesson']: r['text'] for r in con.execute('SELECT lesson,text FROM notes WHERE user_id=?', (uid,))}, **mentoring.state_extra(con,user)})
                return self.reply(404, {'error': 'Ruta no encontrada.'})
            if path == '/api/logout':
                con.execute('DELETE FROM sessions WHERE token=?', (token,))
                return self.reply(200, {'ok': True}, 'session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
            if mentoring.routes(self, con, user, path, data, now):
                return
            if path == '/api/submit':
                lesson = next((l for l in LESSONS if l['id'] == data.get('lesson')), None)
                if lesson is None:
                    raise ValueError()
                if not allowed(user,lesson['level']):
                    return self.reply(403,{'error':'Este nivel todavía no está disponible.'})
                answers = data.get('answers')
                if not isinstance(answers, list) or len(answers) != len(lesson['questions']) or any(type(a) is not int or a not in range(3) for a in answers):
                    raise ValueError()
                written=data.get('written',[])
                if not isinstance(written,list) or len(written)!=len(lesson.get('written_questions',[])) or any(not isinstance(a,str) or not a.strip() or len(a)>2500 for a in written):
                    raise ValueError()
                results = [{'correct': a == q['answer'], 'answer': q['answer'], 'explanation': q['explanation']} for a,q in zip(answers,lesson['questions'])]
                score = sum(r['correct'] for r in results)
                attempt=con.execute('INSERT INTO attempts(user_id,lesson,score,total,created) VALUES(?,?,?,?,?)', (uid,lesson['id'],score,len(results),now().isoformat()))
                con.execute('INSERT INTO lesson_writings(attempt_id,student_id,lesson,prompts,answers,created) VALUES(?,?,?,?,?,?)',(attempt.lastrowid,uid,lesson['id'],json.dumps(lesson['written_questions'],ensure_ascii=False),json.dumps(written,ensure_ascii=False),now().isoformat()))
                for _,front in lesson['dialogue'][:3]:
                    back = 'Frase del diálogo: escucha y reconstruye el modelo.'
                    con.execute('INSERT OR IGNORE INTO reviews(user_id,front,back,due) VALUES(?,?,?,?)', (uid,front,back,now().isoformat()))
                con.execute('INSERT INTO events(user_id,kind,payload,created) VALUES(?,?,?,?)', (uid,'answer_submitted',json.dumps({'lesson':lesson['id'],'score':score,'answers':answers,'results':results},ensure_ascii=False),now().isoformat()))
                return self.reply(200, {'results': results} if user['role']=='student' else {'score': score, 'total': len(results), 'results': results})
            if path == '/api/review':
                card = con.execute('SELECT * FROM reviews WHERE id=? AND user_id=?', (int(data['id']),uid)).fetchone()
                if not card or type(data.get('remembered')) is not bool:
                    raise ValueError()
                interval = min(60, max(1,card['interval']*2)) if data['remembered'] else 0
                due = now()+ (timedelta(days=interval) if interval else timedelta(minutes=10))
                con.execute('UPDATE reviews SET interval=?,due=? WHERE id=?', (interval,due.isoformat(),card['id']))
                return self.reply(200, {'ok': True})
            if path == '/api/notes':
                if data.get('lesson') not in [l['id'] for l in LESSONS] or not isinstance(data.get('text'),str) or len(data['text']) > 5000:
                    raise ValueError()
                con.execute('INSERT INTO notes VALUES(?,?,?) ON CONFLICT(user_id,lesson) DO UPDATE SET text=excluded.text', (uid,data['lesson'],data['text']))
                return self.reply(200, {'ok': True})
            return self.reply(404, {'error': 'Ruta no encontrada.'})

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    init_db()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    reminder_stop=deadlines.start(connect)
    print(f'Rumbo al espanõl: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        reminder_stop.set()
        server.server_close()
