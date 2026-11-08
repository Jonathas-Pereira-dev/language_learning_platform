import json
import re
import unicodedata
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlencode,quote
from urllib.request import Request,urlopen
from urllib.error import URLError

WORDS='''abecedario|sustantivo|Conjunto ordenado de las letras de una lengua.|Aprendo el abecedario español.
abrazo|sustantivo|Gesto de rodear a una persona con los brazos.|Te mando un abrazo.
acento|sustantivo|Manera de pronunciar o mayor intensidad de una sílaba.|Reconozco su acento argentino.
adiós|interjección|Expresión usada para despedirse.|Adiós, hasta mañana.
agua|sustantivo femenino|Líquido necesario para la vida.|Un vaso de agua, por favor.
ahora|adverbio|En este momento.|Ahora estoy en clase.
alfabeto|sustantivo|Conjunto ordenado de letras de una lengua.|Deletrea tu nombre con el alfabeto.
alumno|sustantivo|Persona que aprende con orientación de un docente.|El alumno envía su actividad.
amable|adjetivo|Que trata a los demás con atención y cortesía.|La recepcionista es muy amable.
amigo|sustantivo|Persona con quien se mantiene una relación de afecto y confianza.|Voy al cine con un amigo.
apellido|sustantivo|Nombre familiar que acompaña al nombre propio.|Mi apellido es García.
aprender|verbo|Adquirir conocimientos o habilidades mediante la práctica.|Quiero aprender español.
apodo|sustantivo|Nombre informal que se usa para llamar a una persona.|Su apodo es Dani.
apoyo|sustantivo|Ayuda que permite afrontar una tarea o dificultad.|Necesito apoyo con este ejercicio.
ayer|adverbio|El día anterior al actual.|Ayer estudié veinte minutos.
ayuda|sustantivo|Acción de colaborar con alguien para resolver una necesidad.|¿Puedes darme ayuda?
banco|sustantivo|Entidad que presta servicios financieros; también asiento para varias personas.|Voy al banco a abrir una cuenta.
barrio|sustantivo|Zona de una localidad con identidad propia.|Mi barrio tiene una biblioteca.
bien|adverbio|De manera adecuada o en un estado favorable.|Estoy bien, gracias.
billete|sustantivo|Documento que permite viajar; también papel moneda.|Quiero un billete de tren.
bolígrafo|sustantivo|Instrumento para escribir con tinta.|¿Me prestas un bolígrafo?
bonito|adjetivo|Que resulta agradable por su aspecto.|Es un pueblo muy bonito.
buscar|verbo|Intentar encontrar algo o a alguien.|Busco una farmacia.
café|sustantivo|Bebida preparada con semillas tostadas del cafeto.|Quisiera un café con leche.
calle|sustantivo|Vía pública situada entre edificios.|La farmacia está en esta calle.
cambiar|verbo|Sustituir una cosa por otra o modificarla.|Necesito cambiar la fecha.
cansado|adjetivo|Que siente necesidad de descansar.|Hoy estoy cansado.
casa|sustantivo|Edificio o vivienda donde viven personas.|Mi casa está cerca del parque.
cena|sustantivo|Comida que suele tomarse al final del día.|La cena empieza a las ocho.
cerca|adverbio|A poca distancia.|El museo está cerca.
charlar|verbo|Conversar de manera distendida.|Vamos a charlar un rato.
che|interjección|Llamada informal de atención frecuente en el español rioplatense.|Che, ¿cómo estás?
ciudad|sustantivo|Localidad con una población importante y diversos servicios.|Vivo en una ciudad pequeña.
clase|sustantivo|Sesión dedicada a enseñar y aprender.|La clase empieza a las nueve.
colectivo|sustantivo|Autobús, en el uso habitual de Argentina y otras regiones.|Tomo el colectivo para ir a clase.
comer|verbo|Ingerir alimentos.|Vamos a comer juntos.
compañero|sustantivo|Persona con quien se comparte una actividad.|Te presento a mi compañero.
comprar|verbo|Obtener algo a cambio de dinero.|Quiero comprar una entrada.
comprender|verbo|Entender el significado de algo.|Necesito comprender esta frase.
conocer|verbo|Tener información o experiencia sobre alguien o algo.|Quiero conocer tu país.
contestar|verbo|Dar respuesta a una pregunta o mensaje.|Voy a contestar al docente.
correo|sustantivo|Sistema para enviar mensajes; también mensaje enviado por ese sistema.|Mi correo electrónico está actualizado.
cultura|sustantivo|Conocimientos, prácticas y expresiones compartidos por una comunidad.|La música forma parte de la cultura.
deber|verbo|Tener una obligación o algo pendiente de devolver.|Debo entregar la actividad.
decir|verbo|Expresar algo mediante palabras.|¿Puedes decirlo otra vez?
deletrear|verbo|Nombrar las letras de una palabra por separado.|Voy a deletrear mi apellido.
derecha|sustantivo|Dirección opuesta a la izquierda.|Gira a la derecha.
descansar|verbo|Interrumpir una actividad para recuperar fuerzas.|Necesito descansar un poco.
después|adverbio|En un momento posterior.|Hablamos después de clase.
diccionario|sustantivo|Obra que reúne palabras y explica sus significados.|Consulto el diccionario de la plataforma.
dinero|sustantivo|Medio de pago usado para intercambiar bienes y servicios.|¿Cuánto dinero necesito?
docente|sustantivo|Persona que enseña y orienta el aprendizaje.|Mi docente revisa mis respuestas.
duda|sustantivo|Incertidumbre o pregunta sobre algo.|Tengo una duda de gramática.
edad|sustantivo|Tiempo transcurrido desde el nacimiento.|¿Qué edad tienes?
educación|sustantivo|Proceso de formación y aprendizaje de una persona.|La educación abre oportunidades.
ejemplo|sustantivo|Caso que ayuda a entender una explicación.|¿Puedes darme un ejemplo?
empleo|sustantivo|Trabajo que se realiza a cambio de una remuneración.|Busco un empleo.
entender|verbo|Captar el significado de algo.|No entiendo esta palabra.
entrega|sustantivo|Acción de poner algo a disposición de su destinatario.|La entrega de la actividad es mañana.
entrada|sustantivo|Acceso a un lugar o documento que permite acceder a él.|Tengo una entrada para el cine.
escuchar|verbo|Prestar atención a lo que se oye.|Voy a escuchar el diálogo.
escuela|sustantivo|Institución dedicada a la enseñanza.|Mi escuela está en el centro.
escribir|verbo|Representar palabras mediante signos gráficos.|Me gusta escribir en español.
español|sustantivo|Lengua compartida por numerosas comunidades y países.|Estudio español todos los días.
estudiar|verbo|Dedicar atención a aprender o comprender una materia.|Voy a estudiar por la tarde.
excelente|adjetivo|De muy buena calidad.|Me siento excelente hoy.
explicar|verbo|Hacer que una idea resulte más comprensible.|¿Puedes explicar la actividad?
familia|sustantivo|Conjunto de personas vinculadas por parentesco o convivencia.|Voy a viajar con mi familia.
fatal|adjetivo o adverbio|En el habla cotidiana, muy mal.|Hoy me encuentro fatal.
fecha|sustantivo|Indicación del día, mes y año de un hecho.|Confirma la fecha de entrega.
feliz|adjetivo|Que siente alegría o satisfacción.|Estoy feliz por mi progreso.
fiesta|sustantivo|Reunión o celebración para compartir un momento especial.|Tenemos una fiesta el sábado.
frase|sustantivo|Conjunto de palabras que expresa un sentido.|Escribe una frase con esta palabra.
gracias|interjección|Expresión de agradecimiento.|Gracias por ayudarme.
gramática|sustantivo|Estudio de las formas y combinaciones de una lengua.|Practicamos gramática con ejemplos.
gusto|sustantivo|Preferencia o sensación agradable.|Mucho gusto en conocerte.
hablar|verbo|Comunicarse mediante palabras.|Quiero hablar con más confianza.
hermano|sustantivo|Persona que comparte uno o ambos progenitores con otra.|Te presento a mi hermano.
hola|interjección|Expresión habitual para saludar.|Hola, ¿cómo estás?
hora|sustantivo|Unidad de tiempo de sesenta minutos.|¿A qué hora empieza la clase?
hotel|sustantivo|Establecimiento que ofrece alojamiento temporal.|Tengo una reserva en este hotel.
idioma|sustantivo|Lengua usada por una comunidad.|¿Qué idiomas hablas?
izquierda|sustantivo|Dirección opuesta a la derecha.|La biblioteca está a la izquierda.
jefe|sustantivo|Persona que dirige un equipo o una actividad.|Necesito hablar con mi jefe.
juntos|adverbio|En compañía o realizando una acción en común.|Vamos a practicar juntos.
kilómetro|sustantivo|Unidad de longitud equivalente a mil metros.|El museo está a un kilómetro.
lección|sustantivo|Unidad de contenido dedicada a un aprendizaje.|Completé la primera lección.
leer|verbo|Interpretar el significado de un texto escrito.|Voy a leer un cuento corto.
lejos|adverbio|A gran distancia.|La estación está lejos.
libro|sustantivo|Obra escrita organizada en páginas o en formato digital.|Leo un libro en español.
llamar|verbo|Nombrar a alguien o comunicarse a distancia.|Me llamo Lucía.
mal|adverbio|De manera inadecuada o en un estado desfavorable.|Hoy me siento mal.
mañana|sustantivo o adverbio|Primera parte del día; también el día siguiente.|Mañana tengo clase por la mañana.
mate|sustantivo|Infusión de yerba mate tradicional en varios países de Sudamérica.|Compartimos un mate.
mejor|adjetivo o adverbio|De mayor calidad o en un estado más favorable.|Hoy me encuentro mejor.
mensaje|sustantivo|Información que se transmite a una persona.|Envié un mensaje a mi docente.
mesa|sustantivo|Mueble con una superficie para apoyar objetos.|Quisiera una mesa para dos.
nombre|sustantivo|Palabra que identifica a una persona o cosa.|¿Cuál es tu nombre?
noticia|sustantivo|Información sobre un hecho de interés.|Escucho una noticia sobre educación.
número|sustantivo|Representación de una cantidad o de una posición.|¿Cuál es tu número de teléfono?
objetivo|sustantivo|Resultado que se desea alcanzar.|Mi objetivo es conversar con confianza.
oír|verbo|Percibir sonidos.|¿Puedes oír el audio?
país|sustantivo|Territorio organizado como comunidad política.|¿De qué país eres?
palabra|sustantivo|Unidad de una lengua que aporta significado.|Aprendo una palabra nueva.
pedir|verbo|Expresar a otra persona que se desea algo.|Quisiera pedir un café.
película|sustantivo|Obra audiovisual que cuenta una historia o presenta un tema.|Veo una película en español.
plazo|sustantivo|Tiempo fijado para realizar una acción.|El plazo termina el viernes.
pregunta|sustantivo|Expresión usada para solicitar información.|Tengo una pregunta.
profesor|sustantivo|Persona que enseña una materia.|Mi profesor prepara actividades.
pronunciación|sustantivo|Manera de producir los sonidos de una lengua.|Practico la pronunciación de la erre.
querer|verbo|Desear algo o sentir afecto por alguien.|Quiero aprender a conversar.
recordatorio|sustantivo|Aviso que ayuda a no olvidar una tarea o un hecho.|Recibí un recordatorio de entrega.
reserva|sustantivo|Solicitud anticipada para disponer de una plaza o servicio.|Quisiera confirmar mi reserva.
respuesta|sustantivo|Información que se da al contestar.|El docente revisa mi respuesta.
reunión|sustantivo|Encuentro de personas para tratar un asunto.|Tenemos una reunión mañana.
salud|sustantivo|Estado de bienestar físico y mental.|Hablamos de salud en la clase.
saludar|verbo|Dirigirse a alguien para mostrar reconocimiento o cortesía.|Aprendo nuevas formas de saludar.
sobrenombre|sustantivo|Nombre informal o añadido por el que se conoce a alguien.|Su sobrenombre es Lolo.
soletrar|verbo|Forma usada en portugués; en español se dice deletrear.|En español pedimos: ¿Puedes deletrearlo?
tarde|sustantivo o adverbio|Parte del día después del mediodía; también después del momento previsto.|Llegué tarde por la tarde.
teléfono|sustantivo|Dispositivo para comunicarse a distancia.|¿Cuál es tu teléfono de contacto?
tiempo|sustantivo|Duración de los hechos; también estado de la atmósfera.|Tengo tiempo para estudiar.
trabajo|sustantivo|Actividad realizada para conseguir un resultado.|Busco trabajo en turismo.
triste|adjetivo|Que siente pena o desánimo.|Hoy estoy un poco triste.
turismo|sustantivo|Actividad de viajar y conocer lugares fuera del entorno habitual.|Estudio vocabulario de turismo.
universidad|sustantivo|Institución de educación superior.|Quiero estudiar en una universidad.
usted|pronombre|Forma de tratamiento que suele expresar respeto o distancia.|¿Cómo está usted?
viaje|sustantivo|Desplazamiento de un lugar a otro.|Preparo mi próximo viaje.
vos|pronombre|Forma de tratamiento informal usada en Argentina y otras regiones.|¿Cómo estás vos?
ya|adverbio|Indica que algo sucede o se ha realizado en relación con un momento esperado.|Ya envié mi actividad.
zapato|sustantivo|Prenda que protege el pie.|Estos zapatos son cómodos.'''
LOCAL={w:dict(word=w,category=c,definitions=[d],example=e,source='Glosario didáctico de Rumbo',url='',license='Contenido editorial propio') for w,c,d,e in (line.split('|') for line in WORDS.splitlines())}
LOCAL.pop('soletrar',None)
for entry in LOCAL.values():entry['language']='es'

def key(text):return unicodedata.normalize('NFC',text.strip().lower())
def common_word(word):
    return isinstance(word,str) and word==word.lower() and bool(re.fullmatch(r'[a-záéíóúüñ]+(?:[ -][a-záéíóúüñ]+)*',word))
def proper_category(category):
    return any(w in category.lower() for w in ('propio','antropónimo','apellido','topónimo','onomástica','patronímico','nombre de persona'))
def cached_common_entry(item):
    return item.get('language')=='es' and item.get('entry_type')=='common_word' and common_word(item.get('word')) and not proper_category(item.get('category',''))
def alphabet(text):return ''.join(c for c in unicodedata.normalize('NFD',text) if not unicodedata.combining(c))
def migrate(con):
    con.execute('CREATE TABLE IF NOT EXISTS dictionary_cache(word TEXT PRIMARY KEY,payload TEXT NOT NULL,updated TEXT)')
    con.execute('CREATE TABLE IF NOT EXISTS dictionary_index_cache(cache_key TEXT PRIMARY KEY,payload TEXT NOT NULL)')

class Definitions(HTMLParser):
    def __init__(self):super().__init__();self.depth=0;self.parts=[];self.entries=[];self.heading=None;self.category='entrada';self.spanish=True;self.definitions=False;self.heading_tag=None
    def handle_starttag(self,tag,attrs):
        if tag in ('h2','h3','h4'):self.heading=[];self.heading_tag=tag
        if tag=='dd' and self.spanish and self.definitions:
            if not self.depth:self.parts=[]
            self.depth+=1
    def handle_data(self,data):
        if self.heading is not None:self.heading.append(data)
        if self.depth:self.parts.append(data)
    def handle_endtag(self,tag):
        if tag==self.heading_tag and self.heading is not None:
            title=re.sub(r'\[.*?\]','',' '.join(self.heading)).strip()
            if tag=='h2':self.spanish=title.lower().startswith('español');self.definitions=False
            else:
                proper=proper_category(title)
                self.definitions=not proper and any(w in title.lower() for w in ('sustantivo','verbo','adjetivo','adverbio','interjección','pronombre','locuci','preposición','conjunción','artículo','refrán'))
                if self.definitions:self.category=title[:100]
            self.heading=None
        if tag=='dd' and self.depth:
            self.depth-=1
            if not self.depth:
                text=re.sub(r'\s+',' ',''.join(self.parts)).strip()
                if len(text)>8 and not re.match(r'^(Ejemplo|Uso|Ámbito|Sinónimo|Antónimo|Relacionado|Hipónimo|Hiperónimo|Derivado|Referencia|Traducci)',text,re.I):self.entries.append((self.category,text[:350]))

def wiki_api(params):
    url='https://es.wiktionary.org/w/api.php?'+urlencode(dict(action='parse',format='json',formatversion=2,redirects=1,**params))
    with urlopen(Request(url,headers={'User-Agent':'RumboLocal/1.0 (educational dictionary reader)'}),timeout=10) as response:raw=response.read(2000001)
    if len(raw)>2000000:raise ValueError()
    return json.loads(raw)

def lookup(con,word,now):
    word=key(word)
    if not re.fullmatch(r'[a-záéíóúüñ -]{1,60}',word):raise ValueError()
    if word in LOCAL:return LOCAL[word]
    cached=con.execute('SELECT payload FROM dictionary_cache WHERE word=?',(word,)).fetchone()
    if cached:
        item=json.loads(cached['payload'])
        if cached_common_entry(item):return item
    try:
        meta=wiki_api(dict(page=word,prop='sections'))
        resolved=meta.get('parse',{}).get('title',word)
        if not common_word(resolved):return None
        sections=meta.get('parse',{}).get('sections',[])
        section=next((s['index'] for s in sections if unescape(re.sub('<[^>]*>','',s.get('line',''))).strip().lower()=='español'),None)
        if section is None:return None
        result=wiki_api(dict(page=word,prop='text',section=section))
        parser=Definitions();parser.feed(result.get('parse',{}).get('text',''))
        entries=parser.entries[:5]
        if not entries:return None
        item=dict(language='es',entry_type='common_word',word=word,category=entries[0][0],definitions=[d for _,d in entries],example='',source='Wikcionario · palabras comunes en español',url='https://es.wiktionary.org/wiki/'+quote(word),license='CC BY-SA · consulta la licencia y el historial en la fuente')
        con.execute('INSERT OR REPLACE INTO dictionary_cache VALUES(?,?,?)',(word,json.dumps(item,ensure_ascii=False),now.isoformat()))
        return item
    except (URLError,OSError,ValueError,KeyError):raise ConnectionError('No se pudo consultar Wikcionario. El glosario local sigue disponible.')

def browse(con,letter='A'):
    if letter not in list('ABCDEFGHIJKLMNÑOPQRSTUVWXYZ'):raise ValueError()
    stored={r['word']:json.loads(r['payload']) for r in con.execute('SELECT * FROM dictionary_cache')}
    entries={**LOCAL,**{word:item for word,item in stored.items() if cached_common_entry(item)}}
    return [entries[w] for w in sorted(entries,key=alphabet) if (w.upper().startswith('Ñ') if letter=='Ñ' else alphabet(w).upper().startswith(letter) and not (letter=='N' and w.upper().startswith('Ñ')))]

def fetch_index(letter,cursor=''):
    letters=list('ABCDEFGHIJKLMNÑOPQRSTUVWXYZ')
    if letter=='Ñ':
        # The category collation groups Ñ with N; use page prefixes for this letter.
        params=dict(action='query',format='json',formatversion=2,generator='allpages',gapprefix='ñ',gaplimit=100,gapnamespace=0,prop='categories',clcategories='Categoría:ES:Lemas',cllimit=500)
        if cursor:params['gapcontinue']=cursor
    else:
        params=dict(action='query',format='json',formatversion=2,list='categorymembers',cmtitle='Categoría:ES:Lemas',cmnamespace=0,cmtype='page',cmsort='sortkey',cmlimit=100,cmprop='title')
        params['cmstartsortkeyprefix']=letter
        if letter!='Z':params['cmendsortkeyprefix']='O' if letter=='N' else letters[letters.index(letter)+1]
        if cursor:params['cmcontinue']=cursor
    with urlopen(Request('https://es.wiktionary.org/w/api.php?'+urlencode(params),headers={'User-Agent':'RumboLocal/1.0 (educational dictionary index)'}),timeout=10) as response:data=json.loads(response.read(1000000))
    if 'error' in data:raise ValueError()
    members=data.get('query',{}).get('pages',[]) if letter=='Ñ' else data.get('query',{}).get('categorymembers',[])
    words=[x['title'] for x in members if common_word(x.get('title')) and len(x['title'])<=60 and (x['title'].startswith('ñ') and x.get('categories') if letter=='Ñ' else alphabet(x['title']).upper().startswith(letter) and not (letter=='N' and x['title'].startswith('ñ')))]
    return dict(words=sorted(words,key=alphabet),next_cursor=data.get('continue',{}).get('gapcontinue' if letter=='Ñ' else 'cmcontinue',''))

def browse_catalog(con,letter,cursor=''):
    if letter not in list('ABCDEFGHIJKLMNÑOPQRSTUVWXYZ') or not isinstance(cursor,str) or len(cursor)>1500:raise ValueError()
    cache_key='es-common-v3:'+letter+':'+cursor
    cached=con.execute('SELECT payload FROM dictionary_index_cache WHERE cache_key=?',(cache_key,)).fetchone()
    try:
        result=json.loads(cached['payload']) if cached else fetch_index(letter,cursor)
        if not cached:con.execute('INSERT INTO dictionary_index_cache VALUES(?,?)',(cache_key,json.dumps(result,ensure_ascii=False)))
        return dict(letter=letter,entries=browse(con,letter) if not cursor else [],**result,offline=False,message='Índice de palabras comunes en español, sin nombres propios. Pulsa una palabra para consultar sus acepciones. Usa las páginas para recorrer toda la letra; este catálogo no equivale a una copia completa de todos los diccionarios.')
    except (URLError,OSError,ValueError,KeyError):
        return dict(letter=letter,entries=browse(con,letter),words=[],next_cursor='',offline=True,message='No se pudo cargar el índice general. Se muestran las entradas locales y guardadas; vuelve a intentarlo cuando haya conexión.')
