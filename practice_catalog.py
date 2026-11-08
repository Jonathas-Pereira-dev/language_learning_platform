"""Situaciones de conversación graduadas; catálogo ampliable por docentes."""
from curriculum import LEVELS
LEGACY_LEVELS={'cafe':'A1','viaje':'A2','trabajo':'B1','hotel':'A1','salud':'A2','compras':'A2','aeropuerto':'A2','vivienda':'B1','amistad':'A1'}

DOMAINS = {
'viajes': ('Viajes y transporte', [
('Comprar un billete','un viaje en tren','¿A qué hora sale el tren?'),
('En el aeropuerto','la facturación de un vuelo','Quisiera facturar una maleta.'),
('En el hotel','una reserva de alojamiento','Tengo una reserva a mi nombre.'),
('Pedir indicaciones','cómo llegar a un lugar','¿Dónde está la estación?'),
('Alquilar un coche','el alquiler de un vehículo','¿El seguro está incluido?'),
('Cambiar una reserva','un cambio de fecha','Necesito cambiar mi reserva.'),
('Equipaje perdido','una maleta que no ha llegado','Mi equipaje no aparece.'),
('En la frontera','los documentos de un viaje','Este es mi pasaporte.')]),
'trabajo': ('Trabajo y negocios', [
('Presentarse al equipo','tu primer día de trabajo','Soy parte del nuevo equipo.'),
('Entrevista de trabajo','una entrevista profesional','Me interesa este puesto.'),
('Participar en una reunión','una propuesta de trabajo','Quisiera aportar una idea.'),
('Negociar plazos','el plazo de un proyecto','¿Podemos revisar la fecha de entrega?'),
('Atender a un cliente','una consulta de un cliente','¿En qué puedo ayudarle?'),
('Dar y recibir orientación','comentarios sobre un trabajo','¿Qué podría mejorar?'),
('Resolver un conflicto','un desacuerdo profesional','Me gustaría aclarar lo ocurrido.'),
('Hablar de salario','las condiciones de un contrato','¿Podemos hablar de las condiciones?')]),
'educacion': ('Educación y aprendizaje', [
('Inscribirse en un curso','la matrícula de un curso','Quisiera inscribirme en este curso.'),
('Preguntar en clase','una duda durante una clase','¿Podría explicarlo de nuevo?'),
('Trabajar en grupo','un proyecto con compañeros','¿Cómo repartimos las tareas?'),
('Presentar un tema','una presentación oral','Hoy voy a hablar de este tema.'),
('Solicitar una beca','una solicitud de ayuda al estudio','¿Cuáles son los requisitos?'),
('Hablar con un tutor','tu plan de aprendizaje','Necesito orientación para estudiar.'),
('En la biblioteca','el préstamo de un libro','¿Puedo llevarme este libro?'),
('Defender una investigación','las conclusiones de un estudio','Los resultados sugieren esta interpretación.')]),
'cotidiano': ('Vida cotidiana y relaciones', [
('Conocer a alguien','una primera conversación','¿Cómo te llamas?'),
('Invitar a salir','una invitación a un encuentro','¿Te apetece tomar un café?'),
('Organizar una fiesta','una reunión con amigos','¿Qué podemos preparar?'),
('Hablar con vecinos','una cuestión de convivencia','Quería hablar del ruido.'),
('Repartir tareas en casa','la organización de un hogar','¿Quién se encarga de cocinar?'),
('Pedir ayuda','una dificultad cotidiana','¿Puedes ayudarme un momento?'),
('Expresar límites','una situación incómoda','Prefiero que lo hablemos con calma.'),
('Disculparse','un malentendido personal','Siento lo que pasó.')]),
'servicios': ('Compras, vivienda y servicios', [
('En el restaurante','un pedido de comida','¿Me trae la carta, por favor?'),
('En la cafetería','un pedido de una bebida','Un café con leche, por favor.'),
('Comprar y devolver un producto','una compra o devolución','Quisiera cambiar este producto.'),
('Alquilar una vivienda','una visita a un apartamento','¿Cuánto cuesta el alquiler?'),
('Abrir una cuenta','un trámite bancario','¿Qué documentos necesito?'),
('Solicitar una reparación','una avería en casa','La calefacción no funciona.'),
('Hacer un trámite','una gestión administrativa','Quisiera solicitar una cita.'),
('Reclamar un cobro','un cargo que no reconoces','No reconozco este importe.')]),
'salud': ('Salud, bienestar y emergencias', [
('En la farmacia','una consulta en la farmacia','Necesito hablar con el farmacéutico.'),
('En la consulta médica','una descripción de síntomas','Me duele la garganta.'),
('Pedir una cita médica','una cita con un profesional','¿Hay una cita disponible?'),
('Explicar una alergia','una necesidad de salud','Soy alérgico a este ingrediente.'),
('Solicitar ayuda urgente','una petición de ayuda','Necesitamos ayuda médica.'),
('Hablar de bienestar','tus emociones y necesidades','Últimamente me siento preocupado.'),
('Entender instrucciones','las indicaciones de un profesional','¿Puede escribir las instrucciones?'),
('Comunicar una necesidad de accesibilidad','una adaptación para participar','¿Hay un acceso sin escalones?')]),
'cultura': ('Cultura, ocio y ciudadanía', [
('En el museo','una visita cultural','¿Hay una visita guiada?'),
('Hablar de cine','una película que has visto','¿Qué te pareció la película?'),
('Compartir música','una recomendación musical','Te recomiendo esta canción.'),
('Practicar deporte','una actividad deportiva','¿Podemos entrenar juntos?'),
('Conocer tradiciones','una costumbre local','¿Cómo se celebra esta fiesta?'),
('Hacer voluntariado','una iniciativa de la comunidad','¿Cómo puedo participar?'),
('Debatir una noticia','una noticia de actualidad','¿Qué fuentes podemos consultar?'),
('Hablar del medioambiente','una propuesta ambiental','¿Qué podemos hacer en el barrio?')]),
'tecnologia': ('Tecnología y comunicación digital', [
('Pedir soporte técnico','un problema con una aplicación','No puedo acceder a mi cuenta.'),
('Comprar un dispositivo','la elección de un equipo','¿Qué características tiene?'),
('En una videollamada','una reunión a distancia','¿Se me oye bien?'),
('Hablar de privacidad','el uso de datos personales','¿Cómo se utilizan mis datos?'),
('Evaluar información digital','la fiabilidad de una publicación','¿Quién publicó esta información?'),
('Debatir inteligencia artificial','el uso responsable de IA','¿Qué ventajas y límites tiene?'),
('Crear un proyecto digital','una idea para una herramienta','Quisiera diseñar una solución.'),
('Resolver una compra en línea','un pedido por internet','Mi pedido no ha llegado.')])}

OBJECTIVES={
'A1':('Usa frases breves: saluda, explica una necesidad y haz una pregunta sencilla.','Responde con dos o tres frases. Puedes pedir que repitan.'),
'A2':('Describe la situación, pide información y confirma que has entendido.','Mantén cuatro turnos y utiliza una expresión de cortesía.'),
'B1':('Cuenta lo ocurrido, explica tus motivos y propone una solución.','Compara dos opciones y responde a una pregunta imprevista.'),
'B2':('Defiende una propuesta, negocia condiciones y responde a una objeción.','Utiliza conectores, justifica tus decisiones y reformula una idea.'),
'C1':('Matiza tu postura, adapta el registro y concilia intereses contrapuestos.','Detecta una implicación y responde con precisión y cortesía.'),
'C2':('Gestiona ambigüedades, ironía o desacuerdos sutiles con flexibilidad.','Reformula con distintos registros y construye una conclusión matizada.')}
DOMAINS['presentaciones']=('Presentaciones y trato formal e informal',[
('Decir y deletrear tu nombre','cómo decir y deletrear tu nombre','Me llamo Ana. Se escribe a, ene, a.'),
('Deletrear tus apellidos','el registro de tus apellidos','Mi apellido es García. ¿Quiere que lo deletree?'),
('Explicar tu apodo','el nombre que usas entre amigos','Mis amigos me llaman Dani.'),
('Decir tu edad','tu edad y cumpleaños','Tengo veinticinco años. ¿Y tú?'),
('Presentar a otra persona','la presentación de un amigo','Te presento a mi amiga Laura.'),
('Presentar a un compañero formalmente','una presentación profesional','Le presento a nuestra nueva compañera.'),
('Hablar con tu jefe','una conversación con tu superior','¿Tendría un momento para hablar conmigo?'),
('Pedir algo formalmente','una petición con trato de usted','¿Podría ayudarme con esta solicitud?'),
('Pedir algo entre amigos','una petición informal','¿Me pasas eso, por favor?'),
('Saludar en una entrevista','el inicio de una entrevista','Buenos días. Es un placer conocerle.'),
('Romper el hielo con amigos','una conversación informal','¿Qué tal tu día?'),
('Elegir entre tú y usted','el tratamiento adecuado en una conversación','¿Puedo tutearle?')])
CATALOG=[]
for domain,(label,situations) in DOMAINS.items():
    for index,(title,context,opening) in enumerate(situations):
        for level in LEVELS:
            goal,challenge=OBJECTIVES[level]
            register='formal' if domain in ('trabajo','servicios','educacion','salud') or any(w in title.lower() for w in ('formalmente','formal','jefe','entrevista')) and 'informal' not in title.lower() else 'informal' if domain=='cotidiano' or any(w in title.lower() for w in ('amigos','apodo','informal')) else 'neutro'
            CATALOG.append(dict(id=f'{domain}-{index}-{level}',domain=domain,domain_title=label,level=level,title=title,register=register,context=f'Practica una conversación sobre {context}.',opening=opening,objective=goal,challenge=challenge))
CATALOG_BY_ID={s['id']:s for s in CATALOG}
