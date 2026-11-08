"""Tarjetas extraídas del contenido publicado; no inventa respuestas con IA."""
import re
from progression import allowed

def migrate(con):
    con.execute('''CREATE TABLE IF NOT EXISTS activity_cards(id INTEGER PRIMARY KEY,activity_id INTEGER REFERENCES activities(id),front TEXT NOT NULL,prompt TEXT NOT NULL,UNIQUE(activity_id,front))''')
    for activity in con.execute('SELECT * FROM activities WHERE id NOT IN (SELECT activity_id FROM activity_cards)').fetchall():generate(con,activity)

def generate(con,activity):
    text=activity['audio'].strip() or activity['instructions'].strip()
    sentences=re.split(r'(?<=[.!?])\s+|\n+',text)
    cards=[]
    for sentence in sentences:
        sentence=re.sub(r'^\s*[\w ÁÉÍÓÚÜÑáéíóúüñ-]{1,40}:\s*','',sentence).strip()
        if not 3<=len(sentence)<=500:continue
        words=list(re.finditer(r'\b[\wáéíóúüñÁÉÍÓÚÜÑ]{2,}\b',sentence))
        if not words:continue
        target=words[-1]
        prompt=sentence[:target.start()]+'____'+sentence[target.end():]
        if sentence not in [c[0] for c in cards]:cards.append((sentence,prompt))
        if len(cards)>=12:break
    for front,prompt in cards:con.execute('INSERT OR IGNORE INTO activity_cards(activity_id,front,prompt) VALUES(?,?,?)',(activity['id'],front,prompt))
    return len(cards)

def available(con,user):
    cards=[dict(r) for r in con.execute('''SELECT c.id,c.front,c.prompt,a.title AS source,a.id AS activity_id,a.level
    FROM activity_cards c JOIN activities a ON a.id=c.activity_id
    WHERE a.teacher_id=? AND (a.student_id IS NULL OR a.student_id=?) ORDER BY a.id DESC,c.id''',(user['teacher_id'],user['id']))]
    return [c for c in cards if allowed(user,c['level'])]

def owned(con,user,card_id):
    row=con.execute('''SELECT c.*,a.level,a.title AS source FROM activity_cards c JOIN activities a ON a.id=c.activity_id
    WHERE c.id=? AND a.teacher_id=? AND (a.student_id IS NULL OR a.student_id=?)''',(card_id,user['teacher_id'],user['id'])).fetchone()
    return row if row and allowed(user,row['level']) else None
