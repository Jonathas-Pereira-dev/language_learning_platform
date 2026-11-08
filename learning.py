"""Placement content and formative assessment (not a CEFR certification)."""
LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
ITEMS = {
 'A1': [('Me ___ Ana.', ['llamo', 'llamas', 'llaman'], 0, 'Apresentação: me llamo.'), ('Tengo veinte ___.', ['años', 'año', 'añ os'], 0, 'Idade é expressa com tener e años.'), ('¿Dónde está la estación?', ['Pergunta o preço', 'Pergunta a localização', 'Despede-se'], 1, 'Dónde pergunta localização.')],
 'A2': [('Ayer ___ al mercado.', ['voy', 'fui', 'iré'], 1, 'Ayer indica passado concluído: fui.'), ('Cuando era niño, ___ en Lima.', ['vivía', 'viviré', 'vivo'], 0, 'O imperfeito descreve hábitos e situações passadas.'), ('Necesito una habitación para dos noches.', ['Reserva de hospedagem', 'Pedido de emprego', 'Consulta médica'], 0, 'Habitación e noches situam a reserva num hotel.')],
 'B1': [('Si tuviera tiempo, ___ más.', ['viajé', 'viajaría', 'viajo'], 1, 'Hipótese com imperfecto de subjuntivo e condicional.'), ('Espero que ___ bien.', ['estás', 'estar', 'estés'], 2, 'Desejo com espero que pede subjuntivo.'), ('Aunque llueve, saldré. ¿Qué expresa aunque?', ['Consequência', 'Concessão', 'Finalidade'], 1, 'Aunque introduz uma dificuldade que não impede a ação.')],
 'B2': [('No creo que lo ___ ayer.', ['hizo', 'haya hecho', 'hará'], 1, 'Opinião negativa sobre passado: haya hecho.'), ('De haberlo sabido, te ___.', ['habría avisado', 'aviso', 'avisaré'], 0, 'Hipótese passada não realizada: habría avisado.'), ('El informe es sólido; no obstante, faltan datos.', ['O relatório é rejeitado totalmente', 'Há uma ressalva apesar da qualidade', 'Não faltam dados'], 1, 'No obstante introduz uma ressalva.')],
 'C1': [('Por muy difícil que ___, lo intentaré.', ['es', 'sea', 'será'], 1, 'Concessiva com por muy e subjuntivo.'), ('La propuesta adolece de falta de rigor.', ['Tem falta de rigor', 'Tem rigor excessivo', 'Dispensa avaliação'], 0, 'Adolecer de indica um defeito ou carência.'), ('El director vino a decir que no habría cambios.', ['Citou literalmente uma ordem', 'Transmitiu aproximadamente essa ideia', 'Prometeu mudar tudo'], 1, 'Venir a decir pode resumir uma ideia de forma aproximada.')],
 'C2': [('No es que no ___, es que no me convence.', ['puedo', 'pueda', 'podré'], 1, 'No es que rejeita uma explicação com subjuntivo.'), ('A buenas horas, mangas verdes, se dice cuando…', ['A ajuda chega tarde', 'Alguém chega cedo', 'Uma roupa é bonita'], 0, 'A expressão critica ajuda ou solução tardia.'), ('El articulista cuestiona la pretendida neutralidad del informe.', ['Aceita a neutralidade', 'Sugere distanciamento crítico da alegação', 'Não expressa posição'], 1, 'Pretendida marca distância crítica em relação à neutralidade alegada.')]
}
DIAGNOSTIC = [dict(level=level, weight=idx+1, prompt=p, options=o, answer=a, explanation=e) for idx,level in enumerate(LEVELS) for p,o,a,e in ITEMS[level]]

def assess(answers):
    details = [dict(level=q['level'], prompt=q['prompt'], selected=q['options'][a] if a in range(3) else 'Não sei ainda', expected=q['options'][q['answer']], correct=a==q['answer'], explanation=q['explanation']) for a,q in zip(answers, DIAGNOSTIC)]
    bands = {level: sum(x['correct'] for x in details if x['level']==level) for level in LEVELS}
    level = 'Pré-A1'
    for band in LEVELS:
        if bands[band] < 2: break
        level = band
    weighted = sum(q['weight'] for q,d in zip(DIAGNOSTIC,details) if d['correct'])
    return dict(level=level, bands=bands, weighted=weighted, maximum=sum(q['weight'] for q in DIAGNOSTIC), details=details, message='Estimativa de leitura, uso da língua e pragmática. Professor deve confirmar fala, escuta e escrita; não certifica CEFR.')

SCENARIOS = {'cafe':'Pedir en una cafetería', 'viaje':'Pedir indicaciones en la ciudad', 'trabajo':'Participar en una reunión', 'hotel':'Resolver una reserva de hotel', 'salud':'Explicar síntomas en una consulta', 'compras':'Cambiar un producto', 'aeropuerto':'Resolver un problema con el equipaje', 'vivienda':'Alquilar un apartamento', 'amistad':'Quedar con amigos'}
