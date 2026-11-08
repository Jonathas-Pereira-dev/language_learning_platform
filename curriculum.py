"""Banco editorial: requiere validación del docente, no certifica el MCER."""
LEVELS = ['A1','A2','B1','B2','C1','C2']
# Cada línea: enunciado | respuesta correcta | distractor | distractor.
BANK = {
'A1': '''Me ___ Ana.|llamo|llamas|llaman
Nosotros ___ estudiantes.|somos|son|eres
¿Cuántos años ___ tú?|tienes|eres|estás
Madrid está ___ España.|en|de|por
Quiero ___ agua, por favor.|un vaso de|una vaso de|un vaso en
La hermana de mi madre es mi ___.|tía|prima|abuela
Hoy es lunes. Mañana es ___.|martes|domingo|jueves
Son las ocho de la ___.|mañana|mañanas|mañano
Esta es ___ casa.|mi|yo|me
¿___ te llamas?|Cómo|Dónde|Cuánto
Un libro, dos ___.|libros|libres|libro
María ___ en Bogotá.|vive|viven|vivo
¿De dónde eres? — ___ Perú.|Soy de|Estoy de|Tengo de
El contrario de grande es ___.|pequeño|largo|alto
Gracias. — De ___.|nada|nadie|ningún
Para despedirte dices:|Hasta luego.|Mucho gusto.|¿Qué tal?
El número quince es ___.|15|50|5''',
'A2': '''Ayer ___ al mercado.|fui|voy|iré
Cuando era niño, ___ en Lima.|vivía|viviré|vivo
Este abrigo es más caro ___ aquel.|que|de|como
¿Has ___ alguna vez a Chile?|ido|ir|yendo
Mañana ___ a visitar el museo.|vamos|fuimos|íbamos
Me duelen ___ pies.|los|el|la
Necesito una habitación ___ dos noches.|para|hacia|desde
Hay ___ gente en la plaza.|mucha|mucho|muchos
El museo está ___ de la farmacia.|cerca|cercano|cerco
¿___ cuesta este billete?|Cuánto|Cuántos|Cómo
Antes desayunaba en casa, pero ayer ___ fuera.|desayuné|desayuno|desayunaré
Estoy ___ una carta.|escribiendo|escribir|escrito
A Pedro ___ gusta bailar.|le|lo|la
Es la película ___ divertida de la semana.|más|muy|mucho
No tengo ___ dinero.|nada de|ningún de|nadie
¿Puedes dar___ el menú a ellos?|les|los|las
Busco una camisa ___.|azul|azules|azula''',
'B1': '''Si tuviera tiempo, ___ más.|viajaría|viajé|viajo
Espero que ___ bien.|estés|estás|estar
Aunque llueve, saldré. Aunque expresa:|concesión|finalidad|consecuencia
Cuando ___ a casa, te llamaré.|llegue|llego|llegué
Llevo dos años ___ español.|estudiando|estudio|estudié
Te recomiendo que ___ más.|practiques|practicas|practicar
Ya había salido cuando me ___.|llamaste|llamas|llamarás
No conozco a ___ en esta ciudad.|nadie|nada|ninguno de
Trabajo aquí ___ hace tres años.|desde|durante|hasta
¿Puedes hablar más despacio ___ entenderte?|para|porque|aunque
Si mañana llueve, ___ en casa.|me quedaré|me quedaría|me quedara
La persona ___ te hablé es mi profesora.|de la que|la que|que de
Me gustaría ___ una mesa.|reservar|reservo|reservé
Es importante que todos ___ puntuales.|sean|son|ser
No fui a clase ___ estaba enfermo.|porque|para que|aunque no
Se me ___ las llaves ayer.|perdieron|perdí|perdido
Acabo ___ terminar el informe.|de|a|por''',
'B2': '''No creo que lo ___ ayer.|haya hecho|hizo|hará
De haberlo sabido, te ___.|habría avisado|aviso|avisaré
El informe es sólido; no obstante, faltan datos. Hay:|una reserva|un acuerdo total|una causa
Por mucho que ___, no lo convencerás.|insistas|insistes|insistirás
Ojalá ___ venido a la reunión.|hubieras|habrías|habías
No saldremos a menos que ___ de llover.|deje|deja|dejó
Me pidió que le ___ el documento.|enviara|envié|envío
La propuesta fue ___ por el comité.|aprobada|aprobar|aprobando
Si lo hubiera visto, se lo ___.|habría dicho|diré|digo
Hizo como si no me ___.|conociera|conoce|conocerá
No solo ahorra tiempo, ___ también dinero.|sino|pero|aunque
Busco a alguien que ___ alemán.|hable|habla|habló
Con tal de que ___, esperaremos.|vengas|vienes|vendrás
El proyecto salió adelante ___ las dificultades.|pese a|porque|gracias que
Me alegra que ___ el examen.|hayas aprobado|has aprobado|aprobarás
El autor sostiene que la medida es insuficiente. Sostiene significa:|afirma|prohíbe|desconoce
Cuanto más practiques, ___ te resultará.|más fácil|muy fácil|el fácil''',
'C1': '''Por muy difícil que ___, lo intentaré.|sea|es|será
La propuesta adolece de falta de rigor. Esto indica:|una carencia|una virtud|una certeza
Vino a decir que no habría cambios. La expresión:|resume aproximadamente|cita literalmente|ordena cambiar
De ahí que ___ necesario revisar el plan.|sea|es|será
No es que ___ tarde, sino que cambiaron el horario.|llegara|llegué|llegaré
Se negó a firmar, ___ sus reservas.|aduciendo|aludiendo de|eludiendo de
El acuerdo queda supeditado a la aprobación. Está:|condicionado|garantizado|cancelado
Por más objeciones que ___, continuaremos.|planteen|plantean|plantearán
El informe no hace sino confirmar la hipótesis. El informe:|solo la confirma|la rechaza|no la menciona
Huelga decir que la puntualidad es esencial. Huelga decir significa:|resulta innecesario decir|está prohibido decir|es imposible decir
Siempre y cuando ___ garantías, aceptaremos.|haya|hay|habrá
Con ser importante, no es lo único. Se expresa:|concesión|obligación|finalidad
Lejos de resolverlo, lo agravó. El resultado fue:|contrario al esperado|idéntico al previsto|irrelevante
No cabe duda de que ___ una oportunidad.|es|sea|fuera
La medida dista de ser suficiente. La medida es:|insuficiente|excesiva|definitiva
El argumento resulta endeble. Es un argumento:|poco sólido|irrefutable|neutral''',
'C2': '''No es que no ___, es que no me convence.|pueda|puedo|podré
A buenas horas, mangas verdes se dice cuando:|la ayuda llega tarde|alguien madruga|se compra ropa
Cuestiona la pretendida neutralidad del informe. Pretendida expresa:|distancia crítica|aceptación plena|indiferencia
Dar por zanjada una cuestión significa:|considerarla resuelta|plantearla de nuevo|ignorarla siempre
No por mucho madrugar amanece más temprano aconseja:|no forzar los tiempos|levantarse tarde siempre|evitar todo esfuerzo
La réplica fue tan sutil como demoledora. Fue:|discreta y contundente|confusa y débil|literal y neutra
El autor deja entrever su desacuerdo. Lo expresa:|de manera implícita|con una orden|sin ningún matiz
No deja títere con cabeza significa que:|critica a todos|elogia a todos|se guarda silencio
Una victoria pírrica es una victoria:|con un coste excesivo|fácil y sin coste|sin rival
Soslayar una dificultad significa:|evitar afrontarla|resolverla por completo|provocarla a propósito
El texto está salpicado de ironía. La ironía aparece:|en diversos pasajes|solo en el título|en ninguna parte
El elogio tenía un deje de reproche. Había:|un matiz de crítica|una alabanza sin reservas|una prohibición
La decisión se tomó a espaldas del equipo. Se tomó:|sin informarlo|con su aprobación|delante de todos
No hay mal que por bien no venga sugiere:|una consecuencia favorable de una dificultad|que todo daño es deseable|que nada puede mejorar
La aparente modestia del narrador encubre su vanidad. Hay:|contraste entre apariencia e intención|coincidencia plena|ausencia de intención
El desenlace rehúye toda complacencia. El desenlace:|evita satisfacer fácilmente al lector|busca halagarlo siempre|carece de propósito'''
}
QUESTIONS=[]
for index,level in enumerate(LEVELS):
    for line in BANK[level].splitlines():
        prompt,right,wrong1,wrong2=line.split('|')
        options=[right,wrong1,wrong2]
        rotation=len(QUESTIONS)%3
        options=options[rotation:]+options[:rotation]
        QUESTIONS.append(dict(id=len(QUESTIONS)+1,level=level,weight=index+1,prompt=prompt,options=options,answer=options.index(right),explanation=f'La opción adecuada es «{right}». Revisa su uso en este contexto con tu docente.'))
assert len(QUESTIONS)==100

def assess_items(items,answers):
    details=[dict(id=q['id'],level=q['level'],prompt=q['prompt'],selected=q['options'][a] if a>=0 else 'Todavía no lo sé',expected=q['options'][q['answer']],correct=a==q['answer'],explanation=q['explanation']) for q,a in zip(items,answers)]
    bands={l:sum(d['correct'] for d in details if d['level']==l) for l in LEVELS}
    level='Pre-A1'
    for l in LEVELS:
        if bands[l]<2:break
        level=l
    return dict(level=level,bands=bands,weighted=sum(q['weight'] for q,d in zip(items,details) if d['correct']),maximum=sum(q['weight'] for q in items),details=details,message='Estimación editorial de lectura y uso de la lengua. El docente debe confirmar expresión oral, comprensión auditiva y escritura. No certifica el MCER.')
