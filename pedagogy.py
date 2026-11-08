import base64
import json
import secrets
import unicodedata
from curriculum import QUESTIONS, LEVELS, assess_items
from audio_content import AUDIO_TRACKS, GRAMMAR
import automatic_cards
from practice_catalog import CATALOG, CATALOG_BY_ID
import podcasts
import video_library
import deadlines
import dictionary_es
import screen_catalog
import video_discovery
from progression import allowed,available_levels

def migrate(con):
    podcasts.migrate(con)
    video_library.migrate(con)
    dictionary_es.migrate(con)
    con.executescript('''
    CREATE TABLE IF NOT EXISTS diagnostic_rounds(id INTEGER PRIMARY KEY,student_id INTEGER REFERENCES users(id),teacher_id INTEGER REFERENCES users(id),status TEXT NOT NULL DEFAULT 'authorized',items TEXT,created TEXT,completed TEXT);
    CREATE TABLE IF NOT EXISTS oral_practices(id INTEGER PRIMARY KEY,student_id INTEGER REFERENCES users(id),scenario TEXT,text TEXT,audio TEXT,mime TEXT,feedback TEXT DEFAULT '',created TEXT);
    CREATE TABLE IF NOT EXISTS review_submissions(id INTEGER PRIMARY KEY,student_id INTEGER REFERENCES users(id),teacher_id INTEGER REFERENCES users(id),kind TEXT,prompt TEXT,answer TEXT,expected TEXT,correct INTEGER,created TEXT);
    CREATE TABLE IF NOT EXISTS lesson_writings(id INTEGER PRIMARY KEY,attempt_id INTEGER REFERENCES attempts(id),student_id INTEGER REFERENCES users(id),lesson TEXT,prompts TEXT,answers TEXT,feedback TEXT DEFAULT '',created TEXT);
    ''')
    if 'event_id' not in {r['name'] for r in con.execute('PRAGMA table_info(review_submissions)')}:
        con.execute('ALTER TABLE review_submissions ADD COLUMN event_id INTEGER')
    con.execute('CREATE UNIQUE INDEX IF NOT EXISTS review_submission_event ON review_submissions(event_id)')
    previous=con.execute("SELECT e.*,u.teacher_id FROM events e JOIN users u ON u.id=e.user_id LEFT JOIN review_submissions r ON r.event_id=e.id WHERE e.kind='review_practice' AND u.teacher_id IS NOT NULL AND r.id IS NULL").fetchall()
    for row in previous:
        try:p=json.loads(row['payload'])
        except (ValueError,TypeError):continue
        existing=con.execute('SELECT id FROM review_submissions WHERE student_id=? AND teacher_id=? AND kind=? AND answer=? AND expected=? AND event_id IS NULL ORDER BY id LIMIT 1',(row['user_id'],row['teacher_id'],p.get('kind','phrase'),p.get('answer',''),p.get('expected',''))).fetchone()
        if existing:
            con.execute('UPDATE review_submissions SET event_id=? WHERE id=?',(row['id'],existing['id']))
            continue
        con.execute('INSERT OR IGNORE INTO review_submissions(student_id,teacher_id,kind,prompt,answer,expected,correct,created,event_id) VALUES(?,?,?,?,?,?,?,?,?)',(row['user_id'],row['teacher_id'],p.get('kind','phrase'),p.get('prompt','Repaso registrado anteriormente'),p.get('answer',''),p.get('expected',''),int(bool(p.get('correct'))),row['created'],row['id']))

def rounds(con,student):
    return [dict(r) for r in con.execute('SELECT id,status,created,completed FROM diagnostic_rounds WHERE student_id=? ORDER BY id DESC',(student,))]

def state(con,user):
    uid=user['id']; teacher=user['role']=='teacher'
    active=con.execute("SELECT id,items FROM diagnostic_rounds WHERE student_id=? AND status='started' ORDER BY id DESC LIMIT 1",(uid,)).fetchone()
    items=json.loads(active['items']) if active else []
    public=[{k:v for k,v in next(q for q in QUESTIONS if q['id']==i).items() if k in ('id','prompt','options')} for i in items]
    oral=[dict(r) for r in con.execute('SELECT p.* FROM oral_practices p JOIN users u ON u.id=p.student_id WHERE u.teacher_id=? ORDER BY p.id DESC' if teacher else 'SELECT * FROM oral_practices WHERE student_id=? ORDER BY id DESC',(uid,))]
    rank=LEVELS.index(user['level']) if user['level'] in LEVELS else 0
    writings=[] if teacher else [dict(r) for r in con.execute('SELECT * FROM lesson_writings WHERE student_id=? ORDER BY id DESC',(uid,))]
    for writing in writings:
        writing['answers']=json.loads(writing['answers']);writing['prompts']=json.loads(writing['prompts'])
    return dict(lesson_writings=writings,**screen_catalog.state(user),**deadlines.state(con,user),**video_library.state(con,user),available_levels=available_levels(user),podcast_countries=podcasts.COUNTRIES,podcast_topics=podcasts.TOPICS,podcast_sources=podcasts.SOURCES if teacher else [],activity_flashcards=automatic_cards.available(con,user) if not teacher else [],conversation_catalog=[s for s in CATALOG if allowed(user,s['level'])],diagnostic=public,diagnostic_round_id=active['id'] if active else None,diagnostic_rounds=rounds(con,uid),diagnostic_bank_size=len(QUESTIONS),audio_tracks=[t for t in AUDIO_TRACKS if allowed(user,t['level'])],grammar=[{k:v for k,v in g.items() if k not in ('answer','explanation')} for g in GRAMMAR if teacher or LEVELS.index(g['level'])<=rank],oral_practices=oral)

def normalize(text):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFC',text.lower()) if c.isalnum() or c.isspace()).split())

def routes(h,con,user,path,data,now):
    uid=user['id']; teacher=user['role']=='teacher'
    if path=='/api/lesson-writing-feedback':
        row=con.execute('SELECT w.id FROM lesson_writings w JOIN users u ON u.id=w.student_id WHERE w.id=? AND u.teacher_id=?',(data.get('id'),uid)).fetchone()
        text=str(data.get('feedback','')).strip()
        if not teacher or not row:h.reply(403,{'error':'Acceso denegado.'});return True
        if not text or len(text)>5000:raise ValueError()
        con.execute('UPDATE lesson_writings SET feedback=? WHERE id=?',(text,row['id']))
        h.reply(200,{'ok':True});return True
    if path=='/api/video-discovery':
        if not teacher:h.reply(403,{'error':'La búsqueda de materiales corresponde al docente.'});return True
        try:items=video_discovery.search(data.get('country'),data.get('topic'))
        except (ConnectionError,OSError) as error:h.reply(503,{'error':str(error) if isinstance(error,ConnectionError) else 'No se pudo consultar YouTube.'});return True
        h.reply(200,{'items':items});return True
    if path=='/api/dictionary':
        if data.get('word'):
            try:entry=dictionary_es.lookup(con,str(data['word']),now())
            except ConnectionError as error:h.reply(503,{'error':str(error)});return True
            h.reply(200,{'entry':entry});return True
        letter=data.get('letter','A')
        if data.get('catalog') is True:
            h.reply(200,dictionary_es.browse_catalog(con,letter,data.get('cursor','')));return True
        h.reply(200,{'letter':letter,'entries':dictionary_es.browse(con,letter)});return True
    if path=='/api/reminder-preferences':
        if teacher:h.reply(403,{'error':'Las preferencias corresponden al estudiante.'});return True
        deadlines.preferences(con,user,data,now());h.reply(200,{'ok':True});return True
    if path=='/api/videos':
        if not video_library.create(con,user,data):h.reply(403,{'error':'Solo el docente puede publicar vídeos.'});return True
        h.reply(200,{'ok':True});return True
    if path=='/api/student-level':
        sid=int(data['student_id']);level=data.get('level')
        if not teacher or not con.execute('SELECT id FROM users WHERE id=? AND teacher_id=?',(sid,uid)).fetchone():h.reply(403,{'error':'Acceso denegado.'});return True
        if level not in LEVELS:raise ValueError()
        con.execute('UPDATE users SET level=?,diagnosed=1 WHERE id=?',(level,sid))
        con.execute('INSERT INTO events(user_id,kind,payload,created) VALUES(?,?,?,?)',(sid,'teacher_level',json.dumps(dict(level=level,teacher_id=uid)),now().isoformat()))
        h.reply(200,{'ok':True});return True
    if path=='/api/podcasts':
        if data.get('level') not in LEVELS:raise ValueError()
        if not allowed(user,data['level']):h.reply(403,{'error':'Este nivel todavía no está disponible.'});return True
        try:result=podcasts.get(con,data.get('country'),data.get('topic'),data.get('level'),now())
        except ConnectionError as error:h.reply(503,{'error':str(error)});return True
        h.reply(200,result);return True
    if path=='/api/diagnostic-authorize':
        sid=int(data['student_id'])
        if not teacher or not con.execute("SELECT id FROM users WHERE id=? AND teacher_id=? AND role='student'",(sid,uid)).fetchone():h.reply(403,{'error':'Acceso denegado.'});return True
        if con.execute("SELECT id FROM diagnostic_rounds WHERE student_id=? AND status IN ('authorized','started')",(sid,)).fetchone():h.reply(409,{'error':'Ya hay una prueba pendiente para este estudiante.'});return True
        con.execute('INSERT INTO diagnostic_rounds(student_id,teacher_id,created) VALUES(?,?,?)',(sid,uid,now().isoformat()))
        h.reply(200,{'ok':True});return True
    if path=='/api/diagnostic-start':
        if teacher:h.reply(403,{'error':'Prueba exclusiva del estudiante.'});return True
        row=con.execute("SELECT * FROM diagnostic_rounds WHERE student_id=? AND status IN ('authorized','started') ORDER BY id DESC LIMIT 1",(uid,)).fetchone()
        if not row:h.reply(403,{'error':'Tu docente debe autorizar la prueba.'});return True
        if row['status']=='authorized':
            used=set()
            for r in con.execute("SELECT items FROM diagnostic_rounds WHERE student_id=? AND status='completed'",(uid,)):used.update(json.loads(r['items']))
            selected=[]
            rng=secrets.SystemRandom()
            for level in LEVELS:
                band=[q['id'] for q in QUESTIONS if q['level']==level]
                fresh=[i for i in band if i not in used];rng.shuffle(fresh)
                rest=[i for i in band if i in used];rng.shuffle(rest)
                selected.extend((fresh+rest)[:3])
            rng.shuffle(selected)
            con.execute("UPDATE diagnostic_rounds SET status='started',items=? WHERE id=? AND status='authorized'",(json.dumps(selected),row['id']))
        h.reply(200,{'ok':True});return True
    if path=='/api/diagnostic':
        row=con.execute("SELECT * FROM diagnostic_rounds WHERE id=? AND student_id=? AND status='started'",(data.get('round_id'),uid)).fetchone()
        if teacher or not row:h.reply(403,{'error':'No hay una prueba autorizada en curso.'});return True
        ids=json.loads(row['items']);answers=data.get('answers')
        if not isinstance(answers,list) or len(answers)!=18 or any(type(a) is not int or a not in (-1,0,1,2) for a in answers):raise ValueError()
        items=[next(q for q in QUESTIONS if q['id']==i) for i in ids]
        report=assess_items(items,answers);report['round_id']=row['id'];report['created']=now().isoformat()
        con.execute('INSERT INTO placements(user_id,report,created) VALUES(?,?,?)',(uid,json.dumps(report,ensure_ascii=False),now().isoformat()))
        con.execute('UPDATE users SET level=?,diagnosed=1 WHERE id=?',(report['level'],uid))
        con.execute("UPDATE diagnostic_rounds SET status='completed',completed=? WHERE id=?",(now().isoformat(),row['id']))
        h.reply(200,{'level':report['level'],'message':'Prueba enviada. Tu docente recibe el análisis; no se muestran notas.','guidance':[]});return True
    if path=='/api/review-practice':
        kind=data.get('kind');answer=str(data.get('answer','')).strip()
        if not answer or len(answer)>3000:raise ValueError()
        if kind=='grammar':
            q=next((q for q in GRAMMAR if q['id']==data.get('id')),None)
            rank=LEVELS.index(user['level']) if user['level'] in LEVELS else 0
            if not q or LEVELS.index(q['level'])>rank:raise ValueError()
            expected=q['answer'];explanation=q['explanation'];prompt=q['prompt']
        elif kind=='activity':
            q=automatic_cards.owned(con,user,data.get('id'))
            if not q:raise ValueError()
            expected=q['front'];explanation='Modelo extraído del contenido de tu docente. También puedes pedirle otras respuestas válidas.';prompt=q['prompt']
        elif kind=='phrase':
            q=con.execute('SELECT * FROM reviews WHERE id=? AND user_id=?',(data.get('id'),uid)).fetchone()
            if not q:raise ValueError()
            from content import LESSONS
            owner=next((l for l in LESSONS if any(q['front']==text for _,text in l['dialogue']) or any(q['front']==front for front,_ in l['vocabulary'])),None)
            if owner and not allowed(user,owner['level']):h.reply(403,{'error':'Este nivel todavía no está disponible.'});return True
            expected=q['front'];explanation='Compara tu frase con el modelo y vuelve a intentarlo.';prompt='Reconstruye la frase escuchada.'
        else:raise ValueError()
        correct=normalize(answer)==normalize(expected)
        if kind=='activity':
            before,_,after=q['prompt'].partition('____')
            missing=expected[len(before):len(expected)-len(after) if after else len(expected)]
            correct=correct or normalize(answer)==normalize(missing)
        event=con.execute('INSERT INTO events(user_id,kind,payload,created) VALUES(?,?,?,?)',(uid,'review_practice',json.dumps(dict(kind=kind,id=data.get('id'),prompt=prompt,answer=answer,expected=expected,correct=correct),ensure_ascii=False),now().isoformat()))
        if user['teacher_id']:
            con.execute('INSERT INTO review_submissions(student_id,teacher_id,kind,prompt,answer,expected,correct,created,event_id) VALUES(?,?,?,?,?,?,?,?,?)',(uid,user['teacher_id'],kind,prompt,answer,expected,int(correct),now().isoformat(),event.lastrowid))
        h.reply(200,dict(correct=correct,expected=expected,explanation=explanation,sent_to_teacher=bool(user['teacher_id'])));return True
    if path=='/api/oral-practice':
        if teacher:h.reply(403,{'error':'Solo el estudiante puede enviar esta práctica.'});return True
        if not user['teacher_id']:h.reply(409,{'error':'Vincula a tu docente antes de enviar la práctica.'});return True
        text=str(data.get('text','')).strip();audio=str(data.get('audio',''));mime=data.get('mime','')
        if len(text)>5000 or len(audio)>2800000 or not (text or audio) or (audio and mime not in ('audio/webm','audio/ogg','audio/mp4')):raise ValueError()
        if audio:base64.b64decode(audio,validate=True)
        scenario=str(data.get('scenario',''))
        if len(scenario)>100:raise ValueError()
        if scenario in CATALOG_BY_ID:
            item=CATALOG_BY_ID[scenario];scenario=f'{item["level"]} · {item["title"]}'
            if not allowed(user,item['level']):h.reply(403,{'error':'Este nivel todavía no está disponible.'});return True
        con.execute('INSERT INTO oral_practices(student_id,scenario,text,audio,mime,created) VALUES(?,?,?,?,?,?)',(uid,scenario,text,audio,mime,now().isoformat()))
        h.reply(200,{'ok':True});return True
    if path=='/api/oral-feedback':
        row=con.execute('SELECT p.id FROM oral_practices p JOIN users u ON u.id=p.student_id WHERE p.id=? AND u.teacher_id=?',(data.get('id'),uid)).fetchone()
        text=str(data.get('feedback','')).strip()
        if not teacher or not row:h.reply(403,{'error':'Acceso denegado.'});return True
        if not text or len(text)>5000:raise ValueError()
        con.execute('UPDATE oral_practices SET feedback=? WHERE id=?',(text,row['id']))
        h.reply(200,{'ok':True});return True
    return False
