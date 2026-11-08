"""Recordatorios con consentimiento, SMTP y plantillas de WhatsApp (Twilio)."""
import base64
import json
import os
import re
import smtplib
import threading
from datetime import datetime,timedelta,timezone
from email.message import EmailMessage
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from progression import allowed

def migrate(con):
    if 'due_at' not in {r['name'] for r in con.execute('PRAGMA table_info(activities)')}:con.execute('ALTER TABLE activities ADD COLUMN due_at TEXT')
    con.executescript('''
    CREATE TABLE IF NOT EXISTS reminder_preferences(user_id INTEGER PRIMARY KEY REFERENCES users(id),channel TEXT NOT NULL DEFAULT 'none',email TEXT,phone TEXT,updated TEXT);
    CREATE TABLE IF NOT EXISTS reminder_deliveries(id INTEGER PRIMARY KEY,activity_id INTEGER REFERENCES activities(id),student_id INTEGER REFERENCES users(id),channel TEXT,stage INTEGER,status TEXT,attempts INTEGER DEFAULT 0,next_try TEXT,created TEXT,accepted TEXT,UNIQUE(activity_id,student_id,channel,stage));
    ''')

def channels():
    return dict(email=bool(os.getenv('SMTP_HOST') and os.getenv('SMTP_FROM')),whatsapp=all(os.getenv(k) for k in ('TWILIO_ACCOUNT_SID','TWILIO_AUTH_TOKEN','TWILIO_WHATSAPP_FROM','TWILIO_CONTENT_SID')))

def state(con,user):
    row=con.execute('SELECT * FROM reminder_preferences WHERE user_id=?',(user['id'],)).fetchone()
    return dict(reminder_channels=channels(),reminder_preferences=dict(row) if row else dict(channel='none',email=user['email'],phone=''),reminder_deliveries=[dict(r) for r in con.execute('SELECT activity_id,channel,stage,status,created,accepted FROM reminder_deliveries WHERE student_id=? ORDER BY id DESC LIMIT 30',(user['id'],))])

def preferences(con,user,data,now):
    channel=data.get('channel','none');email=str(data.get('email','')).strip();phone=str(data.get('phone','')).strip()
    if channel!='none' and data.get('consent') is not True:raise ValueError()
    if channel not in ('none','email','whatsapp') or len(email)>254 or (channel=='email' and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email)) or (channel=='whatsapp' and not re.fullmatch(r'\+[1-9][0-9]{7,14}',phone)):raise ValueError()
    con.execute('INSERT INTO reminder_preferences VALUES(?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET channel=excluded.channel,email=excluded.email,phone=excluded.phone,updated=excluded.updated',(user['id'],channel,email,phone,now.isoformat()))

def parse_due(value):
    if not value:return None
    date=datetime.fromisoformat(str(value).replace('Z','+00:00'))
    if date.tzinfo is None:raise ValueError()
    return date.astimezone(timezone.utc).isoformat()

def send(channel,recipient,student,title,due):
    due_label=datetime.fromisoformat(due).strftime('%d/%m/%Y %H:%M UTC')
    if channel=='email':
        msg=EmailMessage();msg['Subject']='Rumbo · tu actividad está por vencer';msg['From']=os.environ['SMTP_FROM'];msg['To']=recipient
        msg.set_content(f'Hola, {student}.\nRecuerda entregar: {title}.\nFecha límite: {due_label}.\nEntra en Actividades para entregar para enviar tu respuesta.\nPuedes desactivar estos avisos desde la plataforma.')
        with smtplib.SMTP(os.environ['SMTP_HOST'],int(os.getenv('SMTP_PORT','587')),timeout=15) as server:
            server.starttls()
            if os.getenv('SMTP_USER'):server.login(os.environ['SMTP_USER'],os.environ['SMTP_PASSWORD'])
            server.send_message(msg)
    else:
        account=os.environ['TWILIO_ACCOUNT_SID']
        if not re.fullmatch(r'AC[a-zA-Z0-9]{32}',account):raise ValueError('Configuración no válida')
        data=urlencode(dict(To='whatsapp:'+recipient,From=os.environ['TWILIO_WHATSAPP_FROM'],ContentSid=os.environ['TWILIO_CONTENT_SID'],ContentVariables=json.dumps({'1':student[:80],'2':title[:150],'3':due_label}))).encode()
        auth=base64.b64encode((account+':'+os.environ['TWILIO_AUTH_TOKEN']).encode()).decode()
        request=Request(f'https://api.twilio.com/2010-04-01/Accounts/{account}/Messages.json',data=data,headers={'Authorization':'Basic '+auth,'Content-Type':'application/x-www-form-urlencoded'})
        with urlopen(request,timeout=15) as response:
            result=json.loads(response.read(100000))
        if not result.get('sid'):raise ValueError('El proveedor no aceptó la solicitud')

def tick(connect,now):
    now=now.astimezone(timezone.utc)
    with connect() as con:
        rows=con.execute('''SELECT a.*,u.id AS pupil,u.name,u.level AS pupil_level,u.role,p.channel,p.email AS target_email,p.phone
        FROM activities a JOIN users u ON u.teacher_id=a.teacher_id AND u.role='student'
        JOIN reminder_preferences p ON p.user_id=u.id AND p.channel!='none'
        WHERE a.due_at>? AND a.due_at<=? AND (a.student_id IS NULL OR a.student_id=u.id)
        AND NOT EXISTS(SELECT 1 FROM submissions s WHERE s.activity_id=a.id AND s.user_id=u.id)''',(now.isoformat(),(now+timedelta(hours=24)).isoformat())).fetchall()
        for r in rows:
            if not allowed({'role':'student','level':r['pupil_level']},r['level']):continue
            stage=2 if datetime.fromisoformat(r['due_at'])<=now+timedelta(hours=2) else 24
            con.execute('INSERT OR IGNORE INTO reminder_deliveries(activity_id,student_id,channel,stage,status,next_try,created) VALUES(?,?,?,?,?,?,?)',(r['id'],r['pupil'],r['channel'],stage,'pending',now.isoformat(),now.isoformat()))
        pending=[dict(r) for r in con.execute('''SELECT d.*,a.title,a.due_at,a.teacher_id,a.level,u.name,u.teacher_id AS current_teacher,u.level AS pupil_level,p.channel AS preference,p.email,p.phone
        FROM reminder_deliveries d JOIN activities a ON a.id=d.activity_id JOIN users u ON u.id=d.student_id JOIN reminder_preferences p ON p.user_id=u.id
        WHERE d.status IN ('pending','retry','blocked') AND d.attempts<4 AND d.next_try<=?''',(now.isoformat(),))]
    for row in pending:
        with connect() as con:
            submitted=con.execute('SELECT id FROM submissions WHERE activity_id=? AND user_id=?',(row['activity_id'],row['student_id'])).fetchone()
            if submitted or row['due_at']<=now.isoformat() or (row['stage']==24 and datetime.fromisoformat(row['due_at'])<=now+timedelta(hours=2)) or row['current_teacher']!=row['teacher_id'] or row['preference']!=row['channel'] or not allowed({'role':'student','level':row['pupil_level']},row['level']):
                con.execute("UPDATE reminder_deliveries SET status='cancelled' WHERE id=?",(row['id'],));continue
            if not channels()[row['channel']]:
                con.execute("UPDATE reminder_deliveries SET status='blocked',next_try=? WHERE id=?",((now+timedelta(minutes=5)).isoformat(),row['id']));continue
            claimed=con.execute("UPDATE reminder_deliveries SET status='sending',attempts=attempts+1 WHERE id=? AND status IN ('pending','retry','blocked')",(row['id'],)).rowcount
        if not claimed:continue
        try:
            send(row['channel'],row['email'] if row['channel']=='email' else row['phone'],row['name'],row['title'],row['due_at'])
            with connect() as con:con.execute("UPDATE reminder_deliveries SET status='accepted',accepted=? WHERE id=?",(now.isoformat(),row['id']))
        except Exception:
            with connect() as con:con.execute("UPDATE reminder_deliveries SET status='retry',next_try=? WHERE id=?",((now+timedelta(minutes=15)).isoformat(),row['id']))

def start(connect):
    stop=threading.Event()
    def work():
        while not stop.is_set():
            try:tick(connect,datetime.now(timezone.utc))
            except Exception:pass
            try:
                import video_library
                video_library.verify(connect,datetime.now(timezone.utc))
            except Exception:pass
            stop.wait(60)
    worker=threading.Thread(target=work,daemon=True,name='deadline-reminders');worker.start()
    return stop
