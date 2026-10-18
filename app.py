"""Rumbo al espanõl: aplicação local, monólito modular, sem dependências externas."""
import argparse
from contextlib import contextmanager
import hashlib
import hmac
import json
import mimetypes
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from content import LESSONS, DIAGNOSTIC

ROOT = Path(__file__).parent
DB = Path(os.environ.get('FLUENTIA_DB', str(ROOT / 'data' / 'fluentia.sqlite3')))
PUBLIC = ROOT / 'static'

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
        ''')

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
            self.reply(400, {'error': 'Dados inválidos. Confira os campos enviados.'})
        except Exception:
            import traceback
            traceback.print_exc()
            self.reply(500, {'error': 'Não foi possível concluir a operação.'})

    def dispatch(self):
        path = urlparse(self.path).path
        if not path.startswith('/api/'):
            if self.command != 'GET':
                return self.reply(405, {'error': 'Método não permitido.'})
            target = (PUBLIC / ('index.html' if path == '/' else path.lstrip('/'))).resolve()
            if not target.is_relative_to(PUBLIC.resolve()) or not target.is_file():
                return self.reply(404, {'error': 'Arquivo não encontrado.'})
            raw = target.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; media-src 'self' blob:; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'")
            self.end_headers()
            return self.wfile.write(raw)
        data = {}
        if self.command == 'POST':
            # Evita gravações por formulários de outras origens.
            origin = self.headers.get('Origin')
            if origin and urlparse(origin).netloc != self.headers.get('Host'):
                return self.reply(403, {'error': 'Origem não permitida.'})
            if self.headers.get_content_type() != 'application/json':
                return self.reply(415, {'error': 'Envie JSON.'})
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 32768:
                return self.reply(413, {'error': 'Corpo de requisição inválido.'})
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError()
        with connect() as con:
            cookies = SimpleCookie(self.headers.get('Cookie', ''))
            token = cookies['session'].value if 'session' in cookies else ''
            user = con.execute('SELECT u.* FROM users u JOIN sessions s ON u.id=s.user_id WHERE s.token=? AND s.expires>?', (token, now().isoformat())).fetchone()
            if path in ('/api/register', '/api/login') and self.command == 'POST':
                email = str(data.get('email', '')).strip().lower()
                password = str(data.get('password', ''))
                if path.endswith('register'):
                    name = str(data.get('name', '')).strip()
                    if not name or len(name) > 80 or '@' not in email or len(email) > 254 or not 8 <= len(password) <= 256:
                        return self.reply(400, {'error': 'Informe nome, e-mail e senha com 8 a 256 caracteres.'})
                    try:
                        cur = con.execute('INSERT INTO users(name,email,password) VALUES(?,?,?)', (name, email, password_hash(password)))
                        uid = cur.lastrowid
                    except sqlite3.IntegrityError:
                        return self.reply(409, {'error': 'E-mail já cadastrado. Entre na sua conta.'})
                else:
                    found = con.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
                    if len(password) > 256 or not found or not hmac.compare_digest(found['password'], password_hash(password, found['password'].split(':')[0])):
                        return self.reply(401, {'error': 'E-mail ou senha incorretos.'})
                    uid = found['id']
                session = secrets.token_urlsafe(32)
                con.execute('DELETE FROM sessions WHERE expires<?', (now().isoformat(),))
                con.execute('INSERT INTO sessions VALUES(?,?,?)', (session, uid, (now() + timedelta(days=7)).isoformat()))
                return self.reply(200, {'ok': True}, 'session=' + session + '; HttpOnly; SameSite=Strict; Path=/; Max-Age=604800')
            if not user:
                return self.reply(401, {'error': 'Entre para continuar.'})
            uid = user['id']
            if self.command == 'GET':
                if path == '/api/state':
                    profile = {k: user[k] for k in ('name', 'email', 'level', 'goal', 'daily', 'diagnosed')}
                    attempts = [dict(r) for r in con.execute('SELECT * FROM attempts WHERE user_id=? ORDER BY id DESC', (uid,))]
                    reviews = [dict(r) for r in con.execute('SELECT * FROM reviews WHERE user_id=? AND due<=? ORDER BY due', (uid, now().isoformat()))]
                    return self.reply(200, {'profile': profile, 'lessons': [public_lesson(l) for l in LESSONS], 'diagnostic': [{k: v for k,v in q.items() if k != 'answer'} for q in DIAGNOSTIC], 'attempts': attempts, 'reviews': reviews, 'notes': {r['lesson']: r['text'] for r in con.execute('SELECT lesson,text FROM notes WHERE user_id=?', (uid,))}})
                return self.reply(404, {'error': 'Rota não encontrada.'})
            if path == '/api/logout':
                con.execute('DELETE FROM sessions WHERE token=?', (token,))
                return self.reply(200, {'ok': True}, 'session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
            if path == '/api/diagnostic':
                answers = data.get('answers')
                if not isinstance(answers, list) or len(answers) != len(DIAGNOSTIC) or any(type(a) is not int or a not in range(3) for a in answers):
                    raise ValueError()
                score = sum(a == q['answer'] for a, q in zip(answers, DIAGNOSTIC))
                level = 'A1' if score < 3 else 'A2' if score < 5 else 'B1'
                goal, daily = data.get('goal'), int(data.get('daily', 15))
                if goal not in ('Viagem', 'Trabalho', 'Cotidiano') or daily not in (10,15,30):
                    raise ValueError()
                con.execute('UPDATE users SET level=?,goal=?,daily=?,diagnosed=1 WHERE id=?', (level, goal, daily, uid))
                return self.reply(200, {'level': level, 'score': score, 'message': 'Estimativa inicial, não é certificação CEFR.'})
            if path == '/api/submit':
                lesson = next((l for l in LESSONS if l['id'] == data.get('lesson')), None)
                if lesson is None:
                    raise ValueError()
                answers = data.get('answers')
                if not isinstance(answers, list) or len(answers) != len(lesson['questions']) or any(type(a) is not int or a not in range(3) for a in answers):
                    raise ValueError()
                results = [{'correct': a == q['answer'], 'answer': q['answer'], 'explanation': q['explanation']} for a,q in zip(answers,lesson['questions'])]
                score = sum(r['correct'] for r in results)
                con.execute('INSERT INTO attempts(user_id,lesson,score,total,created) VALUES(?,?,?,?,?)', (uid,lesson['id'],score,len(results),now().isoformat()))
                for front,back in lesson['vocabulary']:
                    con.execute('INSERT OR IGNORE INTO reviews(user_id,front,back,due) VALUES(?,?,?,?)', (uid,front,back,now().isoformat()))
                con.execute('INSERT INTO events(user_id,kind,payload,created) VALUES(?,?,?,?)', (uid,'answer_submitted',json.dumps({'lesson':lesson['id'],'score':score}),now().isoformat()))
                return self.reply(200, {'score': score, 'total': len(results), 'results': results})
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
            if path == '/api/conversation':
                message = str(data.get('message','')).strip()
                scenario = data.get('scenario','cafe')
                if not message or len(message)>2000 or scenario not in ('cafe','viaje','trabajo'):
                    raise ValueError()
                # Respostas editoriais locais, nunca apresentadas como avaliação por IA.
                replies = {'cafe': '¡Muy bien! ¿Prefieres café con leche o café solo? También tenemos tostadas. ¿Qué te gustaría pedir?', 'viaje': '¡Claro! El museo está cerca de la plaza. ¿Prefieres ir a pie o en autobús?', 'trabajo': 'Gracias por compartir tu idea. ¿Qué objetivo te gustaría alcanzar y cuándo podemos reunirnos?'}
                corrections = []
                if 'yo gusto' in message.lower():
                    corrections.append('Para dizer que você gosta de algo, use «me gusta», por exemplo: Me gusta el café.')
                if 'soy de brasil' in message.lower():
                    corrections.append('Boa apresentação: «Soy de Brasil» usa ser corretamente para origem.')
                return self.reply(200, {'reply': replies[scenario], 'feedback': corrections or ['Tente incluir uma saudação, uma frase completa e uma pergunta. A análise local não avalia gramática livre nem pronúncia.'], 'mode': 'roteiro local'})
            return self.reply(404, {'error': 'Rota não encontrada.'})

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    init_db()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Rumbo al espanõl: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
