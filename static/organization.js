'use strict';

// Professor connection belongs to the signed-in header.
$('#avatar').insertAdjacentHTML('beforebegin','<details id="teacher-connection" class="teacher-connection"><summary>Meu professor</summary><div id="teacher-connection-content" class="connection-popover"></div></details>');
const refreshWithConnection=refresh;
refresh=async function(){
  await refreshWithConnection();
  const connection=$('#teacher-connection');
  connection.hidden=isTeacher();
  if(isTeacher())return;
  $('#teacher-connection-content').innerHTML=state.teacher
    ? `<h3>Meu professor</h3><p>${esc(state.teacher.name)}</p><small>Seu acompanhamento está vinculado a este professor.</small>`
    : '<h3>Vincular professor</h3><p>Informe o código que seu professor compartilhou.</p><form id="join-form"><label>Código do professor<input name="code" required autocomplete="off"></label><button type="submit" class="primary">Vincular professor</button></form>';
  connection.open=false;
};

const previousHome=home;
function personalForm(){
  const p=state.personal_form||state.profile;
  return `<form id="personal-form" class="panel"><h3>Conhecendo seu perfil</h3><label>Nome<input name="name" required maxlength="80" value="${esc(p.name)}"></label><label>E-mail para contato<input name="email" type="email" required maxlength="254" value="${esc(p.email)}"></label><small>Este e-mail é para o acompanhamento do professor; não altera seu e-mail de login.</small><div class="form-row"><label>Objetivo principal<select name="goal">${['Viagem','Trabalho','Cotidiano'].map(g=>`<option ${p.goal===g?'selected':''}>${g}</option>`).join('')}</select></label><label>Meta diária<select name="daily">${[10,15,30].map(n=>`<option value="${n}" ${Number(p.daily)===n?'selected':''}>${n} minutos</option>`).join('')}</select></label></div><label>Você já estudou espanhol?<select name="studied" required><option value="">Selecione</option>${['Nunca estudei','Já estudei','Estudo atualmente'].map(v=>`<option ${p.studied===v?'selected':''}>${v}</option>`).join('')}</select></label><label>Como foi seu contato com o espanhol?<textarea name="experience" maxlength="2000" placeholder="Cursos, viagens, conversas, tempo de estudo…">${esc(p.experience||'')}</textarea></label><label>O que você deseja conseguir com o espanhol?<textarea name="motivation" required maxlength="2000" placeholder="Conte ao professor suas expectativas e necessidades.">${esc(p.motivation||'')}</textarea></label><label>Quais são suas maiores dificuldades?<textarea name="challenges" maxlength="2000" placeholder="Escuta, fala, escrita, confiança, tempo para estudar…">${esc(p.challenges||'')}</textarea></label><button type="submit" class="primary">${state.personal_form?'Atualizar formulário pessoal':'Concluir formulário pessoal'}</button></form>`;
}
function diagnosticFormOnly(){
  return `<form id="diagnostic-form" class="panel"><p>Questões de A1 a C2. Marque “Não sei ainda” quando precisar. Seu professor recebe a análise detalhada; você não recebe nota.</p>${state.diagnostic.map((q,i)=>`<fieldset class="question"><legend>${esc(q.level)} · ${i+1}. ${esc(q.prompt)}</legend>${[...q.options,'Não sei ainda'].map((o,j)=>`<label class="option"><input type="radio" name="q${i}" value="${j===3?-1:j}" required>${esc(o)}</label>`).join('')}</fieldset>`).join('')}<button type="submit" class="primary">Enviar prova ao professor</button></form>`;
}
function learnerForms(){
  return `<section id="student-diagnostic"><h2>Meus formulários</h2><p>Primeiro apresente seu perfil. Depois responda à prova para ajudar o professor a planejar seus estudos.</p><details class="panel learner-form-option"><summary><span><strong>1. Formulário pessoal</strong><small>Dados de contato, objetivos e experiência com espanhol</small></span><span class="completion ${state.personal_form?'complete':''}">${state.personal_form?'✓ Concluído':'A preencher'}</span></summary>${personalForm()}</details><details class="panel learner-form-option"><summary><span><strong>2. Prova diagnóstica</strong><small>Questões de todos os níveis · resultados para seu professor</small></span><span class="completion ${state.profile.diagnosed?'complete':''}">${state.profile.diagnosed?'✓ Enviada':'A responder'}</span></summary>${state.profile.diagnosed?'<div class="notice">✓ Prova enviada. Seu professor já pode consultar os resultados. Você pode responder novamente se necessário.</div>':''}${diagnosticFormOnly()}</details></section>`;
}
function teacherPersonalForm(student){
  const p=student.personal_form;
  return `<details class="student-section"><summary>Formulário pessoal · ${p?'✓ Concluído':'Pendente'}</summary>${p?`<p>Atualizado em ${esc(dateLabel(p.completed))}</p>${[['Nome',p.name],['E-mail de contato',p.email],['Objetivo',p.goal],['Meta diária',p.daily+' minutos'],['Estudo prévio',p.studied],['Experiência',p.experience||'Não informada'],['Expectativas',p.motivation],['Dificuldades',p.challenges||'Não informadas']].map(([label,value])=>`<div class="profile-answer"><strong>${label}</strong><p class="preserve">${esc(value)}</p></div>`).join('')}`:'<p>O aluno ainda não concluiu o formulário pessoal.</p>'}</details>`;
}
function studentArea(){
  const practiced=state.lessons.filter(l=>state.attempts.some(a=>a.lesson===l.id));
  const level=state.profile.diagnosed?esc(state.profile.level):'Ainda não avaliado';
  const resources=state.activities.filter(a=>a.resource);
  return title('SEU ESPAÇO DE APRENDIZAGEM','Área do aluno',`¡Hola, ${esc(state.profile.name.split(' ')[0])}! Seu perfil, desenvolvimento e acompanhamento em um só lugar.`)+`
  <div class="student-overview"><section class="panel"><span class="eyebrow">MEU NÍVEL ESTIMADO</span><h2 class="student-level">${level}</h2><p>${state.profile.diagnosed?'Estimativa do diagnóstico, acompanhada pelo seu professor.':'Preencha o diagnóstico abaixo para conhecer seu ponto de partida.'}</p></section>
  <section class="panel"><span class="eyebrow">MEUS DADOS E OBJETIVOS</span><h2>${esc(state.profile.name)}</h2><p>${esc(state.profile.email)}</p><p>Objetivo: ${esc(state.profile.goal)} · Meta: ${state.profile.daily} minutos por dia</p><small>${state.teacher?`Professor: ${esc(state.teacher.name)}`:'Vincule seu professor pelo botão Meu professor, no topo.'}</small></section></div>
  <section id="student-progress"><h2>Meu progresso</h2>${stats()}<section class="panel"><h3>O que já aprendi e pratiquei</h3>${practiced.map(l=>`<div class="learned-topic"><div><strong>${esc(l.title)}</strong><p>${esc(l.description)}</p><small>Expressões trabalhadas: ${l.vocabulary.map(([word])=>esc(word)).join(' · ')}</small></div></div>`).join('')||'<p>Seus conteúdos praticados aparecerão aqui depois do primeiro envio de uma lição.</p>'}<h3>Histórico de práticas</h3>${state.attempts.map(a=>`<p>${esc(state.lessons.find(l=>l.id===a.lesson)?.title||a.lesson)} · ${esc(dateLabel(a.created))}</p>`).join('')||'<p>Ainda não há práticas registradas.</p>'}</section></section>
  ${learnerForms()}
  <section><h2>Atividades do professor</h2>${state.activities.map(a=>activityCard(a)).join('')||'<div class="panel"><p>As atividades aparecerão aqui quando seu professor as disponibilizar.</p></div>'}</section>
  <section class="panel"><h2>Links e materiais do professor</h2>${resources.map(a=>`<div class="vocab"><strong>${esc(a.title)}</strong><a class="text-button" href="${esc(a.resource)}" target="_blank" rel="noopener noreferrer">Abrir material ou aula ↗</a></div>`).join('')||'<p>Este espaço receberá os links de vídeos, materiais e aulas que seu professor compartilhar nas atividades.</p>'}</section>
  ${contact()}`;
}
function dateLabel(date){return new Date(date).toLocaleString('pt-BR');}
function studentHistory(student){
  const rows=student.attempts.map(a=>({created:a.created,title:state.lessons.find(l=>l.id===a.lesson)?.title||a.lesson,detail:`Prática de lição · ${a.score}/${a.total}`}));
  for(const e of student.content_history||[]){const p=JSON.parse(e.payload);rows.push({created:e.created,title:`Áudio: ${p.track}`,detail:'Três exercícios práticos enviados'});}
  for(const created of student.placement_dates||[])rows.push({created,title:'Diagnóstico de espanhol',detail:'Respostas e análise disponíveis na avaliação'});
  for(const a of state.activities.filter(a=>a.student_id===null||a.student_id===student.id))rows.push({created:a.created,title:a.title,detail:'Atividade disponibilizada pelo professor'});
  for(const s of state.submissions.filter(s=>s.user_id===student.id))rows.push({created:s.created,title:state.activities.find(a=>a.id===s.activity_id)?.title||'Atividade',detail:s.feedback?'Respostas enviadas · com devolutiva':'Respostas enviadas · aguardando devolutiva'});
  for(const c of student.conversations)rows.push({created:c.created,title:state.scenarios[c.scenario]||c.scenario,detail:'Prática de conversação com IA'});
  rows.sort((a,b)=>b.created.localeCompare(a.created));
  if(!rows.length)return '<p>Ainda não há registros de conteúdos para este aluno.</p>';
  return `<ol class="content-timeline">${rows.map(r=>`<li><time>${esc(dateLabel(r.created))}</time><strong>${esc(r.title)}</strong><p>${esc(r.detail)}</p></li>`).join('')}</ol>`||'';
}
function studentPanel(s){
  const activities=state.activities.filter(a=>a.student_id===null||a.student_id===s.id);
  const submissions=state.submissions.filter(a=>a.user_id===s.id);
  return `<details class="panel student-panel"><summary><span class="student-initial">${esc(s.name.charAt(0))}</span><span><strong>${esc(s.name)}</strong><small>${esc(s.goal)} · ${s.daily} min por dia</small></span><span class="pill">${s.diagnosed?esc(s.level):'Diagnóstico pendente'}</span></summary><div class="student-profile"><div><small>E-mail</small><strong>${esc(s.email)}</strong></div><div><small>Objetivo</small><strong>${esc(s.goal)}</strong></div><div><small>Nível estimado</small><strong>${s.diagnosed?esc(s.level):'Ainda não avaliado'}</strong></div><div><small>Meta diária</small><strong>${s.daily} minutos</strong></div></div><div class="student-metrics"><span>${activities.length} atividades disponíveis</span><span>${submissions.length} envios</span><span>${submissions.filter(a=>!a.feedback).length} aguardando orientação</span></div>${teacherPersonalForm(s)}<div class="student-metrics"><span>Formulário pessoal: ${s.personal_form?"✓ Concluído":"Pendente"}</span><span>Prova diagnóstica: ${s.diagnosed?"✓ Enviada":"Pendente"}</span></div><details class="student-section"><summary>Histórico de conteúdos e práticas</summary><p>Registros de atividades disponibilizadas e práticas enviadas. Abertura de páginas não significa conteúdo concluído.</p>${studentHistory(s)}</details><details class="student-section"><summary>Atividades e orientações deste aluno</summary>${activities.map(a=>activityCard(a,s.id)).join('')||'<p>Nenhuma atividade disponível para este aluno.</p>'}</details><details class="student-section"><summary>Diagnósticos, resultados e conversas</summary>${report(s)}${s.audio_practices.map(p=>`<div class="notice"><h3>Áudio: ${esc(p.track)}</h3>${p.answers.map((a,i)=>`<p>${i+1}. ${esc(a)}</p>`).join('')}</div>`).join('')}</details><button type="button" class="secondary" data-plan-student="${s.id}">Propor atividade para ${esc(s.name.split(' ')[0])}</button></details>`;
}
home=function(){
  if(!isTeacher())return studentArea();
  const original=previousHome();
  const start=original.indexOf('<form id="activity-create"');
  const form=original.slice(start,original.indexOf('</form>',start)+7);
  const pending=state.submissions.filter(s=>!s.feedback).length;
  return title('ACOMPANHAMENTO DO PROFESSOR','Cada aluno, um caminho.','Conheça os objetivos, revise as práticas e planeje os próximos passos.')+`<div class="stats"><div class="stat"><strong>${state.students.length}</strong><span>alunos vinculados</span></div><div class="stat"><strong>${state.activities.length}</strong><span>atividades propostas</span></div><div class="stat"><strong>${pending}</strong><span>envios para orientar</span></div></div><section class="panel"><div class="section-title"><h2>Meus alunos</h2><span class="pill">Código da turma: ${esc(state.profile.invite)}</span></div><p>Compartilhe o código para vincular alunos. Abra o nome de cada pessoa para ver seu perfil e histórico.</p></section>${state.students.map(studentPanel).join('')||'<section class="panel"><p>Seus alunos aparecerão aqui quando informarem o código da turma.</p></section>'}<details class="panel" id="teacher-planning"><summary>Criar atividade e material de apoio</summary>${form}</details>`+contact();
};

conversation=()=>title('CONVERSAÇÃO','Sua voz encontra uma conversa.','Pratique situações reais com espaço para falar, ouvir e escrever.')+`<div class="conversation-layout"><section class="panel voice-studio"><span class="eyebrow">PRÁTICA ORAL</span><label>Situação<select id="scenario">${Object.entries(state.scenarios).map(([id,t])=>`<option value="${id}">${esc(t)}</option>`).join('')}</select></label><div class="voice-orb" aria-hidden="true">♫</div><h2>Vamos conversar?</h2><p>Fale no seu ritmo e acompanhe o diálogo pelo chat.</p><div class="voice-wave" aria-hidden="true">▂ ▄ ▆ ▃ █ ▅ ▂ ▆ ▄</div><div class="notice">Áudio da conversa em preparação</div><button type="button" class="secondary" disabled>▶ Ouvir resposta · em breve</button><p><small>O visual da conversa por áudio está preparado. Gravação, envio de áudio e resposta falada ainda precisam de integração.</small></p></section><section class="panel conversation-chat"><div class="section-title"><h2>Chat da prática</h2><span class="pill">${state.ai_ready?'Texto com IA':'Integração pendente'}</span></div><div id="chat" class="chat" role="log" aria-label="Histórico da conversa"><div class="bubble">¡Hola! Escolha uma situação e comece a conversa.</div></div><form id="chat-form"><label>Sua mensagem em espanhol<input name="message" maxlength="2000" required placeholder="Escreva sua mensagem…"></label><div class="controls"><button type="button" class="secondary" id="microphone">◉ Ditar mensagem</button><button type="submit" class="primary" ${state.ai_ready?'':'disabled'}>Enviar ↗</button></div><small>O ditado preenche o texto pelo navegador. ${state.ai_ready?'As conversas enviadas à IA ficam registradas para acompanhamento do professor.':'O envio de mensagens à IA depende da configuração do responsável.'}</small></form></section></div>`;
document.addEventListener('click',event=>{
  const button=event.target.closest('button');
  if(button?.dataset.planStudent){
    $('#teacher-planning').open=true;
    $('#activity-create [name=student_id]').value=button.dataset.planStudent;
    $('#activity-create [name=title]').focus();
  }
});
document.addEventListener('submit',async event=>{
  if(event.target.id!=='personal-form')return;
  event.preventDefault();
  const button=event.target.querySelector('[type=submit]');button.disabled=true;
  try{
    const values=Object.fromEntries(new FormData(event.target));
    await api('personal-form',{...values,daily:Number(values.daily)});
    await refresh();render('home');
    toast('✓ Formulário pessoal concluído. Seu professor pode consultar seu perfil.');
    document.getElementById('student-diagnostic').scrollIntoView({block:'start'});
  }catch(err){toast(err.message);}finally{button.disabled=false;}
});
(async()=>{try{await refresh();render();}catch(err){showAuth();if(!err.message.includes('Entre para'))toast(err.message);}})();
