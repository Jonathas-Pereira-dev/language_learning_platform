from urllib.parse import urlparse
from progression import allowed,LEVELS
from podcasts import COUNTRIES
from urllib.request import Request,HTTPRedirectHandler,build_opener
from urllib.parse import urlencode
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor

CHECK_HOSTS={'youtube.com','www.youtube.com','youtu.be','colombia.co','www.colombia.co','www.rtve.es','rtve.es','www.educ.ar','educ.ar','cervantes.org','www.cervantes.org','www.profedeele.es','www.pocoyo.com'}
class SourceRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        parsed=urlparse(newurl)
        if parsed.scheme!='https' or parsed.hostname not in CHECK_HOSTS:raise ValueError('Redirección no permitida')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

TOPICS={'cultura':'Cultura','educacion':'Educación','turismo':'Lugares turísticos','acentos':'Acentos','expresiones':'Expresiones y lenguaje informal','historia':'Historia','gastronomia':'Gastronomía'}
SEEDS=[
('Sonidos de Colombia','CO','cultura','A1','https://colombia.co/videos/sonidos-de-colombia','Identifica tres sonidos y nombra un lugar que te gustaría conocer.'),
('Colombia: un viaje visual','CO','turismo','A1','https://colombia.co/videos-turismo-la-respuesta-es-colombia','Describe un paisaje con tres palabras sencillas.'),
('Cultura colombiana','CO','cultura','A2','https://colombia.co/videos/en-cultura-la-respuesta-es-colombia','Describe una expresión cultural y compárala con una de tu comunidad.'),
('Lenguas y costumbres del Mercosur','AR','educacion','B1','https://www.educ.ar/recursos/132314/dia-del-mercosur-lenguas-y-costumbre','Reconoce una relación entre lengua, identidad y costumbres. Consulta los audiovisuales enlazados.'),
('Archivo audiovisual del Instituto Cervantes','ES','cultura','B2','https://cervantes.org/es/cultura/digital/contenidos','Selecciona una conversación cultural y resume la posición de sus participantes.'),
('Acentos y diversidad en España','ES','acentos','B2','https://www.rtve.es/play/videos/gen-playz/acentos/6466085/','Reconoce variedades de pronunciación y comenta el respeto a la diversidad lingüística.'),
('Expresiones coloquiales del español','ES','expresiones','B2','https://www.profedeele.es/actividad/expresiones-coloquiales/','Mira el vídeo explicativo y diferencia el registro informal del formal.')]

def migrate(con):
    con.execute('''CREATE TABLE IF NOT EXISTS video_resources(id INTEGER PRIMARY KEY,teacher_id INTEGER REFERENCES users(id),title TEXT,country TEXT,topic TEXT,level TEXT,url TEXT,instructions TEXT,UNIQUE(teacher_id,url))''')
    cols={r['name'] for r in con.execute('PRAGMA table_info(video_resources)')}
    for name in ('availability','checked_at'):
        if name not in cols:con.execute(f'ALTER TABLE video_resources ADD COLUMN {name} TEXT')
    for seed in SEEDS:
        if not con.execute('SELECT id FROM video_resources WHERE teacher_id IS NULL AND url=?',(seed[4],)).fetchone():
            con.execute('INSERT INTO video_resources(title,country,topic,level,url,instructions) VALUES(?,?,?,?,?,?)',seed)

def state(con,user):
    videos=[dict(v) for v in con.execute('SELECT * FROM video_resources WHERE teacher_id IS NULL OR teacher_id=? ORDER BY id DESC',(user['id'] if user['role']=='teacher' else user['teacher_id'],))]
    return dict(video_topics=TOPICS,videos=[v for v in videos if allowed(user,v['level']) and (user['role']=='teacher' or v['availability']=='available')])

def create(con,user,data):
    if user['role']!='teacher':return False
    fields={k:str(data.get(k,'')).strip() for k in ('title','country','topic','level','url','instructions')}
    parsed=urlparse(fields['url'])
    if not fields['title'] or len(fields['title'])>150 or fields['country'] not in COUNTRIES or fields['topic'] not in TOPICS or fields['level'] not in LEVELS or parsed.scheme!='https' or not parsed.hostname or len(fields['url'])>2000 or len(fields['instructions'])>3000:raise ValueError()
    con.execute('INSERT INTO video_resources(teacher_id,title,country,topic,level,url,instructions) VALUES(?,?,?,?,?,?,?) ON CONFLICT(teacher_id,url) DO UPDATE SET title=excluded.title,country=excluded.country,topic=excluded.topic,level=excluded.level,instructions=excluded.instructions',(user['id'],*[fields[k] for k in ('title','country','topic','level','url','instructions')]))
    return True

def check_url(url):
    parsed=urlparse(url)
    if parsed.scheme!='https':return False
    host=(parsed.hostname or '').lower()
    if host in ('youtube.com','www.youtube.com','youtu.be'):
        target='https://www.youtube.com/oembed?'+urlencode(dict(url=url,format='json'))
    elif host in ('colombia.co','www.colombia.co','www.rtve.es','rtve.es','www.educ.ar','educ.ar','cervantes.org','www.cervantes.org','www.profedeele.es','www.pocoyo.com'):
        target=url
    else:return False
    try:
        with build_opener(SourceRedirect()).open(Request(target,headers={'User-Agent':'Mozilla/5.0 (Rumbo educational link checker)'}),timeout=7) as response:
            body=response.read(500000).decode('utf-8','ignore').lower()
            final_host=urlparse(response.geturl()).hostname or ''
        return not any(word in body for word in ('video unavailable','vídeo no disponible','video no disponible','contenido no disponible','realizando tareas de mantenimiento')) and final_host not in ('comunes.cervantes.es',)
    except Exception:return False

def verify(connect,now):
    with connect() as con:rows=[dict(r) for r in con.execute('SELECT id,url FROM video_resources WHERE checked_at IS NULL OR checked_at<?',((now-timedelta(hours=24)).isoformat(),))]
    def inspect(row):return row['id'],check_url(row['url'])
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(inspect,rows))
    with connect() as con:
        for video_id,ok in results:con.execute('UPDATE video_resources SET availability=?,checked_at=? WHERE id=?',('available' if ok else 'unavailable',now.isoformat(),video_id))
    return len(results)
