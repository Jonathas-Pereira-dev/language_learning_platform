"""Titulares recientes y guiones didácticos; no reproduce artículos completos."""
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError

COUNTRIES={'ES':'España','MX':'México','AR':'Argentina','BO':'Bolivia','CL':'Chile','CO':'Colombia','CR':'Costa Rica','CU':'Cuba','DO':'República Dominicana','EC':'Ecuador','SV':'El Salvador','GQ':'Guinea Ecuatorial','GT':'Guatemala','HN':'Honduras','NI':'Nicaragua','PA':'Panamá','PY':'Paraguay','PE':'Perú','PR':'Puerto Rico','UY':'Uruguay','VE':'Venezuela'}
TOPICS={'tecnologia':'tecnología','educacion':'educación','viajes':'viajes','turismo':'turismo','ciencia':'ciencia','cultura':'cultura','medioambiente':'medioambiente','economia':'economía','deportes':'deportes','sociedad':'sociedad','finanzas':'finanzas personales','empleo':'empleo','salud':'salud','innovacion':'innovación','gastronomia':'gastronomía'}
TASKS={
'A1':['Identifica el país y el tema.','Escoge tres palabras del titular y escribe una frase sencilla con cada una.','Di: Esta noticia habla de…'],
'A2':['Explica el titular con dos frases sencillas.','Formula una pregunta sobre la noticia.','Relaciona el tema con una experiencia cotidiana.'],
'B1':['Resume la idea del titular sin añadir hechos que no conoces.','Abre la fuente y distingue hechos de opiniones.','Explica por qué el tema puede interesar a la comunidad.'],
'B2':['Consulta la fuente y contrasta el titular con su contenido.','Explica una causa y una consecuencia respaldadas por la fuente.','Defiende tu opinión y responde a una objeción.'],
'C1':['Analiza el enfoque y las voces representadas en la fuente.','Compara la cobertura con otro medio.','Expón una conclusión matizada con atribución de fuentes.'],
'C2':['Examina presuposiciones, ambigüedades y posibles sesgos.','Reformula la noticia para dos públicos sin distorsionar sus hechos.','Construye un análisis crítico y señala los límites de la evidencia.']}
SOURCES=[dict(title='RNE Audio · Esto merece una explicación',url='https://www.rtve.es/play/audios/esto-merece-una-explicacion/',description='Pódcast original sobre actualidad y contexto. El audio original no está graduado por nivel.')]
FRAMES={
'A1':'Hola. Hoy escuchamos un título. El país es {country}. El tema es {topic}. Escucha despacio y reconoce palabras.',
'A2':'Hoy practicamos con una noticia sobre {topic}, relacionada con {country}. Escucha el titular e identifica su idea principal.',
'B1':'Este boletín de práctica parte de un titular sobre {topic} en {country}. Escucha, explica la idea con tus palabras y consulta la fuente antes de añadir detalles.',
'B2':'Analizaremos un titular sobre {topic} relacionado con {country}. Distingue lo que el titular afirma de lo que solo podrías inferir.',
'C1':'Tomamos como punto de partida un titular sobre {topic} vinculado con {country}. Atiende al enfoque, las atribuciones y los matices del lenguaje periodístico.',
'C2':'Este ejercicio propone una lectura crítica de un titular sobre {topic} relacionado con {country}. Examina sus presuposiciones y su encuadre sin atribuir a la fuente información que no hayas contrastado.'}

def migrate(con):con.execute('CREATE TABLE IF NOT EXISTS news_cache(cache_key TEXT PRIMARY KEY,payload TEXT NOT NULL,fetched TEXT NOT NULL)')

def fetch_news(country,topic,now):
    query=f'"{COUNTRIES[country]}" {TOPICS[topic]} when:7d'
    url='https://news.google.com/rss/search?'+urlencode(dict(q=query,hl='es',gl='ES',ceid='ES:es'))
    req=Request(url,headers={'User-Agent':'RumboLocal/1.0 (educational RSS reader)','Accept':'application/rss+xml, application/xml'})
    with urlopen(req,timeout=10) as response:
        raw=response.read(1000001)
    if len(raw)>1000000:raise ValueError('Feed demasiado grande')
    root=ET.fromstring(raw)
    items=[];seen=set()
    for entry in root.findall('./channel/item'):
        title=re.sub(r'<[^>]*>','',entry.findtext('title','')).strip()[:180]
        link=entry.findtext('link','').strip()
        try:published=parsedate_to_datetime(entry.findtext('pubDate','')).astimezone(timezone.utc)
        except (TypeError,ValueError,OverflowError):continue
        if not now-timedelta(days=7)<=published<=now+timedelta(hours=1):continue
        if not title or title in seen or urlparse(link).scheme!='https' or not urlparse(link).hostname:continue
        seen.add(title)
        source=entry.find('source')
        publisher=(source.text or 'Fuente periodística')[:100] if source is not None else 'Fuente periodística'
        items.append(dict(title=title,url=link,publisher=publisher,published=published.isoformat()))
        if len(items)==8:break
    return items

def get(con,country,topic,level,now):
    if country not in COUNTRIES or topic not in TOPICS or level not in TASKS:raise ValueError()
    key=country+':'+topic
    row=con.execute('SELECT * FROM news_cache WHERE cache_key=?',(key,)).fetchone()
    stale=False
    if row and row['fetched']>(now-timedelta(minutes=15)).isoformat():items=json.loads(row['payload']);fetched=row['fetched']
    else:
        try:
            items=fetch_news(country,topic,now);fetched=now.isoformat()
            con.execute('INSERT OR REPLACE INTO news_cache VALUES(?,?,?)',(key,json.dumps(items,ensure_ascii=False),fetched))
        except (URLError,OSError,TimeoutError,ValueError,ET.ParseError):
            if not row:raise ConnectionError('No se pudieron consultar las noticias. Comprueba la conexión y vuelve a intentarlo.')
            items=json.loads(row['payload']);fetched=row['fetched'];stale=True
    output=[]
    for i in items:
        intro=FRAMES[level].format(country=COUNTRIES[country],topic=TOPICS[topic])
        script=f'{intro} El titular publicado por {i["publisher"]} dice: {i["title"]}. '
        script+='Actividad de nivel '+level+'. '+ ' '.join(TASKS[level])
        output.append({**i,'script':script,'tasks':TASKS[level]})
    return dict(items=output,country=COUNTRIES[country],topic=TOPICS[topic],level=level,fetched=fetched,stale=stale,source='Google Noticias RSS · titulares de medios externos',message='Boletín didáctico leído por la voz del navegador; no es un pódcast original del medio. El nivel corresponde a las actividades, no garantiza la dificultad del titular. Abre la fuente para conocer la noticia completa.')
