# Rumbo al espanõl · Tu español empieza aquí

MVP local baseado em `sie flunty.pptx`: diagnóstico, trilha, conteúdo contextual, prática, feedback e revisão espaçada.

## Executar no Git Bash

Requisito: Python 3.12 ou superior disponível como `python`.

```bash
cd /c/Fluentia
bash start.sh
```

Abra **http://127.0.0.1:8000** e crie sua conta. Encerre com `Ctrl+C`. Se a porta estiver ocupada, use `bash start.sh --port 8001`.

Para ativar o ambiente manualmente no Git Bash:

```bash
cd /c/Fluentia
source .venv/Scripts/activate
python app.py
# Ao terminar:
deactivate
```

O script cria a `.venv` caso necessário. Não exige instalação de pacotes: HTTP, SQLite e autenticação utilizam a biblioteca padrão do Python. HTML, CSS e JavaScript não exigem build ou CDN.

## Recursos implementados

- Biblioteca **Áudios por tema** com faixas independentes de saudações, despedidas e perguntas/respostas sobre bem-estar e sentimentos. Cada faixa e cada frase podem ser ouvidas em duas vozes selecionáveis. Sugestões de voz feminina/masculina usam nomes conhecidos; o navegador não fornece gênero, então a associação pode ser ajustada manualmente. Se não houver uma segunda voz espanhola instalada, a interface informa a limitação sem simular uma voz com mudança de tom.

- Contas, login, logout e sessões de sete dias; senha protegida por PBKDF2 com salt individual.
- Diagnóstico de cinco perguntas, objetivo e meta diária; estimativa inicial A1/A2/B1, sem certificação CEFR.
- Quatro lições piloto com diálogos, leitura em espanhol pelo navegador, velocidade, texto ocultável e vocabulário.
- Quizzes corrigidos no servidor, explicações e histórico. Acerto de pelo menos 60% conclui a lição.
- Anotações privadas e progresso persistidos no SQLite, isolados por conta.
- Sugestão de lições por nível, objetivo e conclusão.
- Revisão espaçada: acerto agenda em 1, 2, 4 dias e até 60 dias; erro agenda em dez minutos.
- Conversação demonstrativa com três roteiros e ditado opcional pelo navegador.
- Layout responsivo em português com conteúdo de espanhol.

## Limites e próximos módulos

Esta entrega é um MVP local funcional, não toda a plataforma de produção do roadmap de 16 semanas. O slide não fornece vídeos de aula: o piloto usa texto e leitura por voz. Conversação usa respostas fixas identificadas como demonstração, sem IA conectada nem avaliação de pronúncia. O ditado pode processar áudio no serviço do navegador e só começa ao clicar.

Ainda precisam ser integrados: CMS e publicação editorial, mídia própria/licenciada, IA generativa, pagamentos, notificações, analytics operacional e aplicativo mobile. A evolução sugerida é migrar a camada HTTP para FastAPI, dados para PostgreSQL, mídia para Mux/Cloudflare Stream e adicionar serviços de IA e cobrança com credenciais no servidor.

O servidor é destinado ao endereço local `127.0.0.1`. Antes de publicar, usar servidor de produção e HTTPS, proteção contra tentativas de login, recuperação de conta, verificação de e-mail, backups e políticas de dados. O cookie local usa HttpOnly e SameSite; Secure depende de HTTPS.

## Arquivos

- `app.py`: servidor, contas, banco e APIs de aprendizagem.
- `content.py`: conteúdo editorial e diagnóstico.
- `static/`: interface, estilos e integração com APIs.
- `tests/test_app.py`: testes HTTP com banco temporário.
- `start.sh`: inicialização no Git Bash.
- `data/fluentia.sqlite3`: banco gerado automaticamente e ignorado pelo Git.
- `.venv/`: ambiente Python local, ignorado pelo Git.

Para backup, encerre o servidor e copie o banco para um local seguro. Datas do progresso usam o fuso do navegador.

## Verificação

```bash
source .venv/Scripts/activate
python -m unittest discover -s tests -v
node --check static/app.js # opcional: Node não é necessário para executar a plataforma
```
