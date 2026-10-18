'use strict';

// Cada faixa contém apenas expressões do tema indicado, sem misturar assuntos.
window.AudioPractice = (() => {
  const tracks = [
    {id:'saludos', title:'Saudações · Saludos', description:'Para cumprimentar em diferentes momentos do dia.', phrases:[
      ['¡Hola!', 'Olá!'], ['Buenos días.', 'Bom dia.'],
      ['Buenas tardes.', 'Boa tarde.'], ['Buenas noches.', 'Boa noite, ao chegar.']
    ]},
    {id:'despedidas', title:'Despedidas · Despedidas', description:'Para encerrar uma conversa e se despedir.', phrases:[
      ['¡Adiós!', 'Adeus!'], ['Hasta luego.', 'Até logo.'],
      ['Hasta mañana.', 'Até amanhã.'], ['Nos vemos pronto.', 'Nos vemos em breve.'],
      ['Que tengas un buen día.', 'Tenha um bom dia.'], ['Que descanses.', 'Descanse bem.']
    ]},
    {id:'sentimientos', title:'Como você está? · ¿Cómo estás?', description:'Pergunte e responda sobre bem-estar e sentimentos.', phrases:[
      ['¿Cómo estás?', 'Como você está?'], ['Estoy bien, gracias. ¿Y tú?', 'Estou bem, obrigado(a). E você?'],
      ['¿Cómo te sientes hoy?', 'Como você se sente hoje?'], ['Me siento feliz.', 'Eu me sinto feliz.'],
      ['Estoy un poco triste.', 'Estou um pouco triste.'], ['Estoy cansada.', 'Estou cansada.'],
      ['Estoy cansado.', 'Estou cansado.'], ['¿Te sientes mejor?', 'Você se sente melhor?'],
      ['Sí, me siento mejor. Gracias por preguntar.', 'Sim, eu me sinto melhor. Obrigado(a) por perguntar.']
    ]}
  ];
  const escape = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const profiles = {female:'Voz feminina', male:'Voz masculina'};
  const chosen = {female:null, male:null};
  let playing = null, generation = 0;
  function voices() {
    return window.speechSynthesis ? window.speechSynthesis.getVoices().filter(v=>/^es(?:-|_|$)/i.test(v.lang)) : [];
  }
  function suggested(list, profile) {
    // Web Speech não informa gênero. Só sugerimos nomes de vozes conhecidas;
    // o aluno pode ouvir e ajustar a associação em qualquer dispositivo.
    const pattern = profile==='female'
      ? /\b(helena|sabina|laura|elvira|dalia|paulina|monica|mónica|lucia|lucía|paloma|conchita|maria|maría|catalina|isabela|female)\b/i
      : /\b(pablo|raul|raúl|diego|alvaro|álvaro|jorge|juan|carlos|enrique|andres|andrés|rodrigo|male)\b/i;
    return list.find(v=>pattern.test(v.name));
  }
  function render() {
    return `<section class="panel audio-practice" aria-labelledby="audio-title"><span class="eyebrow">ESCUCHA Y REPITE · OUÇA E REPITA</span><h2 id="audio-title">Uma situação, um áudio.</h2><p>Ouça cada tema separadamente. Compare a mesma frase nas duas vozes para reconhecer diferentes maneiras de falar.</p><div class="audio-settings"><label>Voz feminina<select id="audio-female" data-audio-profile="female" aria-describedby="audio-help"></select></label><label>Voz masculina<select id="audio-male" data-audio-profile="male" aria-describedby="audio-help"></select></label><label>Velocidade<select id="audio-rate"><option value="0.75">Devagar · 0,75×</option><option value="1" selected>Normal · 1×</option><option value="1.2">Mais rápido · 1,2×</option></select></label></div><small id="audio-help">As vozes vêm do navegador. Nomes conhecidos são sugeridos; você pode ajustar cada seleção após ouvir. Se uma voz não estiver disponível, instale outra voz de espanhol no sistema ou use outro navegador. Alterar a velocidade não muda o gênero da voz.</small><div class="audio-tracks">${tracks.map((t,i)=>`<article class="audio-track"><span class="eyebrow">ÁUDIO 0${i+1}</span><h3>${t.title}</h3><p>${t.description}</p><div class="controls"><button type="button" class="primary" data-audio-track="${t.id}" data-audio-voice="female">▶ Voz feminina</button><button type="button" class="secondary" data-audio-track="${t.id}" data-audio-voice="male">▶ Voz masculina</button></div><details><summary>Ver frases e ouvir uma por vez</summary><ul class="audio-phrases">${t.phrases.map(([es,pt],n)=>`<li><div><strong lang="es">${es}</strong><small>${pt}</small></div><div class="controls"><button type="button" class="text-button" data-audio-track="${t.id}" data-audio-voice="female" data-audio-phrase="${n}" aria-label="Ouvir ${escape(es)} na voz feminina">♀ Ouvir</button><button type="button" class="text-button" data-audio-track="${t.id}" data-audio-voice="male" data-audio-phrase="${n}" aria-label="Ouvir ${escape(es)} na voz masculina">♂ Ouvir</button></div></li>`).join('')}</ul></details></article>`).join('')}</div><div class="audio-status-bar"><span id="audio-status" role="status" aria-live="polite">Escolha um tema e uma voz para começar.</span><button type="button" class="secondary" id="audio-stop">■ Parar áudio</button></div></section>`;
  }
  function status(text) { const el=document.querySelector('#audio-status');if(el)el.textContent=text; }
  function sync() {
    const list=voices();
    for(const profile of Object.keys(profiles)) {
      const select=document.querySelector('#audio-'+profile);if(!select)continue;
      if(!list.some(v=>v.voiceURI===chosen[profile]))chosen[profile]=suggested(list,profile)?.voiceURI||null;
      select.innerHTML='<option value="">Selecione uma voz de espanhol</option>'+list.map(v=>`<option value="${escape(v.voiceURI)}">${escape(v.name)} · ${escape(v.lang)}</option>`).join('');
      select.value=chosen[profile]||'';
    }
    document.querySelectorAll('[data-audio-voice]').forEach(b=>{b.disabled=!chosen[b.dataset.audioVoice];});
    if(!window.speechSynthesis)status('Este navegador não oferece leitura por voz. As frases estão disponíveis abaixo.');
    else if(!list.length)status('Nenhuma voz de espanhol disponível no momento. A lista será atualizada quando as vozes carregarem.');
    else if(!chosen.female||!chosen.male)status('Selecione as vozes disponíveis acima. Se faltar uma delas, será necessário instalar outra voz de espanhol.');
    else if(chosen.female===chosen.male)status('As duas seleções usam a mesma voz. Escolha vozes diferentes para comparar.');
  }
  function stop() { generation++;playing=null;window.speechSynthesis?.cancel(); }
  function play(trackId,profile,phrase) {
    stop();const track=tracks.find(t=>t.id===trackId),voice=voices().find(v=>v.voiceURI===chosen[profile]);
    if(!track||!voice)return status('Selecione uma voz de espanhol disponível.');
    const items=phrase===undefined?track.phrases:[track.phrases[Number(phrase)]];
    if(items.some(p=>!p))return;
    const current= generation,rate=Number(document.querySelector('#audio-rate').value);
    playing=profile;
    function say(i) {
      if(current!==generation)return;
      if(i>=items.length){playing=null;status('Áudio concluído. Repita em voz alta ou compare com a outra voz.');return;}
      status(`${track.title} · ${profiles[profile]} (${voice.name}) · ${i+1}/${items.length}: ${items[i][0]}`);
      const utterance=new SpeechSynthesisUtterance(items[i][0]);utterance.voice=voice;utterance.lang=voice.lang;utterance.rate=rate;
      utterance.onend=()=>{if(current===generation)setTimeout(()=>say(i+1),450);};
      utterance.onerror=event=>{if(current===generation&&event.error!=='canceled'&&event.error!=='interrupted'){playing=null;status('Não foi possível reproduzir. Tente outra voz ou confira a saída de som.');}};
      window.speechSynthesis.speak(utterance);
    }
    say(0);
  }
  document.addEventListener('click',event=>{
    const button=event.target.closest('button');if(!button)return;
    if(button.dataset.audioTrack)play(button.dataset.audioTrack,button.dataset.audioVoice,button.dataset.audioPhrase);
    if(button.id==='audio-stop'||button.id==='stop-audio'){stop();status('Áudio parado.');}
    if(button.id==='listen'){stop();status('Reproduzindo o diálogo da lição.');}
    if(button.id==='logout')stop();
  });
  document.addEventListener('change',event=>{
    if(event.target.dataset.audioProfile){stop();chosen[event.target.dataset.audioProfile]=event.target.value||null;sync();}
    if(event.target.id==='audio-rate'&&playing){stop();status('Velocidade alterada. Clique em ouvir para recomeçar.');}
  });
  window.speechSynthesis?.addEventListener('voiceschanged',sync);
  return {render,sync,stop};
})();
