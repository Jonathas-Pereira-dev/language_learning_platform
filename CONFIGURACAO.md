# Plataforma local e acompanhamento

La interfaz actual está en español. Consulta [GUIA_DE_USO.md](GUIA_DE_USO.md) para el flujo actualizado: pruebas de 18 preguntas autorizadas por el docente desde un banco de 100, 20 temas de audio y evaluación docente de grabaciones. El frontend activo es `static/platform.js` y la reproducción usa `static/audio.js`; los scripts anteriores ya no se cargan en la página. Las secciones técnicas siguientes conservan las instrucciones de conexión de servicios.

No PowerShell, em `C:\Fluentia`:

```powershell
.\.venv\Scripts\python.exe app.py
```

Abra http://127.0.0.1:8000. Reinicie o servidor depois de alterar o código e atualize a página com Ctrl+F5.

## Aluno e professor

Crie uma conta escolhendo o perfil. Contas anteriores continuam como aluno. Para experimentar os dois acessos, use e-mails diferentes. O professor recebe um código de turma; o aluno informa esse código na tela inicial. A seleção no login deve corresponder ao perfil cadastrado e não promove contas existentes.

O professor pode criar atividades com diálogo para leitura em voz, três exercícios abertos e um link HTTPS para vídeo, material ou chamada externa. Os envios recebem devolutiva individual. Há mensagens entre professor e aluno. A plataforma não hospeda vídeos nem realiza videochamadas internamente.

O aluno vê práticas, orientações e desenvolvimento sem notas numéricas. O professor vê resultados dos quizzes, respostas, diagnósticos e conversas com IA dos alunos vinculados. Os registros são armazenados no SQLite local; faça backup de `data/fluentia.sqlite3` com o servidor encerrado.

## Diagnóstico

São 18 questões (três por faixa A1–C2), com opção “Não sei ainda”. Cada questão tem peso de 1 no A1 até 6 no C2; o relatório mostra pontuação ponderada e acertos por faixa. A estimativa exige ao menos duas respostas corretas em cada faixa, em sequência desde A1. Sem consolidação de A1, indica Pré-A1. Os pesos não permitem compensar lacunas básicas com acertos isolados avançados.

Esse banco é um ponto de partida editorial, não um instrumento validado ou certificação CEFR. Não cobre todas as competências ou todos os conteúdos de cada nível. O professor deve revisar as questões e confirmar o nível com escuta, fala e escrita. O aluno recebe nível estimado e orientações; o professor recebe respostas, erros e explicações completos.

## Conversação com IA

Configure no mesmo terminal antes de iniciar o servidor:

```powershell
$env:OPENAI_API_KEY = 'sua-chave'
$env:OPENAI_MODEL = 'modelo-da-sua-conta-compativel-com-chat-completions-e-json'
.\.venv\Scripts\python.exe app.py
```

Use um identificador real de modelo disponível na sua conta; o texto acima é um marcador. A chave permanece no servidor. A integração usa [Chat Completions e saída JSON](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create). A API pode gerar custos. Não há resposta simulada quando falta configuração: a interface informa a indisponibilidade.

O tutor recebe o cenário, nível estimado e até seis interações anteriores daquele cenário. Retorna uma resposta em espanhol e correções em português. Mensagens e correções são registradas para o professor; o conteúdo da conversa é enviado à OpenAI. O ditado usa reconhecimento do navegador e a análise da IA é textual, sem avaliação de pronúncia. A IA pode errar; o professor acompanha as orientações.

## Recuperação de senha

Configure um servidor SMTP com STARTTLS:

```powershell
$env:SMTP_HOST = 'smtp.seu-provedor.com'
$env:SMTP_PORT = '587'
$env:SMTP_FROM = 'contato@seu-dominio.com'
$env:SMTP_USER = 'usuario-smtp'
$env:SMTP_PASSWORD = 'senha-smtp'
$env:APP_URL = 'http://127.0.0.1:8000'
```

O link expira em 30 minutos, tem uso único e revoga as sessões anteriores após a redefinição. A resposta não revela se o endereço está cadastrado. Sem SMTP, a interface informa que a recuperação não está configurada. Não grave chaves ou senhas no repositório.

## Vozes e velocidades

O seletor inclui países hispanofalantes e Porto Rico e filtra as vozes efetivamente fornecidas pelo navegador. Permite associar vozes femininas e masculinas manualmente, pois o navegador não informa gênero com garantia. As velocidades são 0,75×, 1× e 1,5×.

A disponibilidade de duas vozes de cada país não é garantida. O sistema informa regiões sem voz e não simula sotaques. Garantir todas as regiões exige contratar e integrar um catálogo de síntese de voz que as cubra. Cada faixa da biblioteca tem três práticas abertas, salvas para o professor.

## Verificação

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --check static/app.js
node --check static/audio.js
node --check static/mentoring.js
```
