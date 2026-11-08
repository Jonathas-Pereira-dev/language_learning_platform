from progression import allowed

GENRES=['animación','comedia','aventuras','drama','historia','documental','cultura','naturaleza','educativo']
ITEMS=[
dict(title='Pocoyó: episodios breves',kind='serie',genre='animación',level='A1',country='ES',url='https://www.pocoyo.com/es/episodios',task='Mira un fragmento corto. Nombra tres objetos y describe una acción con una frase sencilla.'),
dict(title='Pocoyó: una escena para contar',kind='corto',genre='educativo',level='A1',country='ES',url='https://www.pocoyo.com/es/episodios',task='Elige una escena de un episodio. Cuenta qué ves usando hay, es y está. No es necesario comprender todo.'),
dict(title='Sonidos de Colombia',kind='corto',genre='cultura',level='A1',country='CO',url='https://colombia.co/videos/sonidos-de-colombia',task='Identifica sonidos y describe el lugar que más te llama la atención.'),
dict(title='Una visita visual a Colombia',kind='corto',genre='aventuras',level='A2',country='CO',url='https://colombia.co/videos-turismo-la-respuesta-es-colombia',task='Describe dos lugares y explica cuál te gustaría visitar.'),
dict(title='Cultura colombiana',kind='corto',genre='documental',level='A2',country='CO',url='https://colombia.co/videos/en-cultura-la-respuesta-es-colombia',task='Anota cinco palabras culturales y prepara una presentación breve.'),
dict(title='Nuestros árboles: El olivo',kind='documental',genre='naturaleza',level='B1',country='ES',url='https://www.rtve.es/play/videos/nuestros-arboles/olivo-10-11-1986/7027485/',task='Trabaja un fragmento con subtítulos. Resume el proceso que se describe y ordena tres pasos.'),
dict(title='Campeones',kind='película',genre='comedia',level='B2',country='ES',url='https://www.rtve.es/play/videos/somos-cine/campeones/5751723/',task='Selecciona una escena y analiza cómo cambia la relación entre los personajes.'),
dict(title='El olivo',kind='película',genre='drama',level='B2',country='ES',url='https://www.rtve.es/play/videos/somos-cine/olivo/5649687/',task='Explica las motivaciones de un personaje y argumenta una decisión alternativa.'),
dict(title='El Ministerio del Tiempo',kind='serie',genre='historia',level='B2',country='ES',url='https://www.rtve.es/play/videos/el-ministerio-del-tiempo/',task='Describe un conflicto y diferencia el contexto histórico de los elementos ficticios.'),
dict(title='El olivo: coloquio con sus creadoras',kind='documental',genre='cultura',level='C1',country='ES',url='https://www.rtve.es/play/videos/version-espanola/version-espanola-olivo-coloquio/4815238/',task='Contrasta las interpretaciones de las participantes y reconstruye sus argumentos.'),
dict(title='El Ministerio del Tiempo: matices y registros',kind='serie',genre='aventuras',level='C1',country='ES',url='https://www.rtve.es/play/videos/el-ministerio-del-tiempo/',task='Compara registros de dos personajes y reformula un diálogo sin perder su intención.'),
dict(title='Cine y discurso: análisis de El olivo',kind='película',genre='drama',level='C2',country='ES',url='https://www.rtve.es/play/videos/somos-cine/olivo/5649687/',task='Analiza silencios, implicaciones y puntos de vista. Defiende dos lecturas de una escena con evidencia del filme.')]

DETAILS={
'https://www.pocoyo.com/es/episodios':('Pocoyó y sus amigos descubren objetos, juegos y situaciones cotidianas. Los episodios breves permiten seguir acciones sencillas con apoyo visual.','Pocoyó · episodios oficiales'),
'https://colombia.co/videos/sonidos-de-colombia':('Un recorrido audiovisual por sonidos y paisajes colombianos para acercarse al país mediante imágenes y experiencias sensoriales.','Marca País Colombia'),
'https://colombia.co/videos-turismo-la-respuesta-es-colombia':('Presentación turística de Colombia que invita a conocer paisajes y experiencias del país. Es un material breve para describir lugares y expresar preferencias.','Marca País Colombia'),
'https://colombia.co/videos/en-cultura-la-respuesta-es-colombia':('Una presentación audiovisual sobre expresiones culturales colombianas. Sirve para observar tradiciones y hablar de diversidad cultural.','Marca País Colombia'),
'https://www.rtve.es/play/videos/nuestros-arboles/olivo-10-11-1986/7027485/':('Documental dedicado al olivo, sus características y su relación con el paisaje mediterráneo y la producción de aceite.','RTVE Play'),
'https://www.rtve.es/play/videos/somos-cine/campeones/5751723/':('Un entrenador de baloncesto se hace cargo de un equipo de personas con discapacidad intelectual. La convivencia con el grupo transforma su forma de relacionarse y entender el deporte.','RTVE Play'),
'https://www.rtve.es/play/videos/somos-cine/olivo/5649687/':('Alma quiere recuperar el olivo que su familia vendió y que tiene un significado especial para su abuelo. Su búsqueda conecta vínculos familiares, memoria y decisiones personales.','RTVE Play'),
'https://www.rtve.es/play/videos/el-ministerio-del-tiempo/':('Una patrulla de una institución secreta viaja por distintas épocas para impedir que cambie la historia. La serie combina aventuras, conflictos personales y referencias históricas españolas.','RTVE Play'),
'https://www.rtve.es/play/videos/version-espanola/version-espanola-olivo-coloquio/4815238/':('Conversación con la directora Icíar Bollaín y la actriz Anna Castillo sobre El olivo. El coloquio permite escuchar cómo explican e interpretan la película.','RTVE Play')}
for item in ITEMS:
    item['synopsis'],item['where']=DETAILS[item['url']]
    item['availability_note']='Consulta la disponibilidad y los subtítulos en el sitio oficial; el acceso puede variar por país o requerir registro.'

def state(user):return dict(screen_genres=GENRES,screen_catalog=[i for i in ITEMS if allowed(user,i['level'])])
