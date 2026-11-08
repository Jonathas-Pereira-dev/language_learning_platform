'use strict';

// Cada faixa contém apenas expressões do tema indicado, sem misturar assuntos.
window.AudioPractice = (() => {
  let tracks=[], learnerLevel='A1';
  const ranks=['Pre-A1','A1','A2','B1','B2','C1','C2'];
  function configure(items,level){tracks=items;learnerLevel=level;}
  const escape = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem('rumbo.audio') || '{}') || {}; } catch {}
  let selectedVoice = saved.voice || '', country = saved.country || '';
  let rate = [0.75,1,1.5].includes(saved.rate) ? saved.rate : 1;
  function persist() { try { localStorage.setItem('rumbo.audio',JSON.stringify({voice:selectedVoice,country,rate})); } catch {} }
  let activeTrackId = null;
  let playing = null, generation = 0, loadTimer = null, loadAttempts = 0, startTimer = null, activeUtterance = null;
  function retryVoices() {
    if(loadTimer!==null||loadAttempts>=8||!window.speechSynthesis)return;
    loadTimer=setTimeout(()=>{loadTimer=null;loadAttempts++;sync();},500);
  }
  function voices() {
    return window.speechSynthesis ? window.speechSynthesis.getVoices().filter(v=>/^es(?:-|_|$)/i.test(v.lang)&&v.lang.toLowerCase().replace('_','-')!=='es-us').sort((a,b)=>{const priority=v=>({'es-es':0,'es-ar':1}[v.lang.toLowerCase().replace('_','-')]??2);return priority(a)-priority(b);}) : [];
  }
  const language = v => v.lang.toLowerCase().replace(/_/g,'-');
  function resolveVoice() {
    return {voice:voices().find(v=>v.voiceURI===selectedVoice&&(!country||language(v)===country)),notice:''};
  }
  function render() {
    const visible=tracks.filter(t=>learnerLevel==='teacher'||ranks.indexOf(t.level)<=Math.max(1,ranks.indexOf(learnerLevel)));
    return `<section class="panel audio-practice" aria-labelledby="audio-title"><span class="eyebrow">ESCUCHA Y REPITE</span><h2 id="audio-title">Una situación, un audio.</h2><p>Elige una voz de español disponible y escucha los diálogos de tu nivel y de niveles anteriores.</p><div class="audio-settings"><label>País / región disponible<select id="audio-country"><option value="">Todas las regiones disponibles</option></select></label><label>Voz para escuchar<select id="audio-voice" aria-describedby="audio-help"></select></label><label>Velocidad<select id="audio-rate"><option value="0.75">Lento · 0,75×</option><option value="1" selected>Normal · 1×</option><option value="1.5">Rápido · 1,5×</option></select></label></div><small id="audio-help">La lista muestra las voces de español del navegador. Todos los audios usan la voz seleccionada. No se garantiza la identificación de género.</small><div class="audio-levels">${ranks.slice(1).filter(level=>visible.some(t=>t.level===level)).map(level=>`<details class="audio-level-group" ${level===(learnerLevel==='teacher'?'A1':learnerLevel)||learnerLevel==='Pre-A1'?'open':''}><summary>Nivel ${level} · ${visible.filter(t=>t.level===level).length} temas disponibles</summary><div class="audio-tracks">${visible.filter(t=>t.level===level).map((t,i)=>`<article class="audio-track"><span class="eyebrow">AUDIO 0${i+1}</span><h3>${t.title} · ${t.level}</h3><p>${t.description}</p><div class="controls"><button type="button" class="primary" data-audio-track="${t.id}" data-audio-voice="selected">▶ Escuchar</button></div><details><summary>Ver frases y escucharlas individualmente</summary><ul class="audio-phrases">${t.phrases.map(([es,pt],n)=>`<li><div><strong lang="es">${es}</strong>${pt!==es?`<small>${pt}</small>`:''}</div><div class="controls"><button type="button" class="text-button" data-audio-track="${t.id}" data-audio-voice="selected" data-audio-phrase="${n}" aria-label="Escuchar ${escape(es)}">▶ Escuchar</button></div></li>`).join('')}</ul></details><form data-audio-exercises="${t.id}"><h4>Tres prácticas para asimilar</h4>${(t.questions||["Escribe una expresión que escuchaste y explica su significado.","Crea una respuesta usando una de las expresiones.","Imagina otra situación y escribe un diálogo breve."]).map((q,i)=>`<label>${i+1}. ${q}<textarea name="a${i}" required maxlength="3000"></textarea></label>`).join('')}<button class="secondary">Guardar mis tres prácticas</button><p role="status"></p></form></article>`).join('')}</div></details>`).join('')}</div><div class="audio-status-bar"><span id="audio-status" role="status" aria-live="polite">Elige un tema y una voz para empezar.</span><button type="button" class="secondary" id="audio-stop">■ Detener audio</button></div></section>`;
  }
  function status(text) {
    const el=document.querySelector('#audio-status');if(el)el.textContent=text;
    document.querySelectorAll('[data-audio-notice]').forEach(el=>{el.textContent=activeTrackId!==null&&el.closest('.audio-track')?.querySelector('[data-audio-track]')?.dataset.audioTrack===activeTrackId?text:'';});
  }
  function sync() {
    const all=voices();
    const regions=[...new Set(all.map(language))].sort();
    if(all.length&&country&&!regions.includes(country))country='';
    const regionSelect=document.querySelector('#audio-country');
    if(regionSelect){
      const names=new Intl.DisplayNames(['es'],{type:'region'});
      regionSelect.innerHTML='<option value="">Todas las regiones disponibles</option>'+regions.map(code=>{
        const region=code.split('-')[1];
        let name=code;
        try { if(region)name=names.of(region.toUpperCase())||code; } catch {}
        return `<option value="${escape(code)}">${escape(name)} · ${escape(code)}</option>`;
      }).join('');
      regionSelect.value=country;
    }
    const rateSelect=document.querySelector('#audio-rate');if(rateSelect)rateSelect.value=String(rate);
    const list=all.filter(v=>!country||language(v)===country);
    if(!selectedVoice&&list.length)selectedVoice=list[0].voiceURI;
    const select=document.querySelector('#audio-voice');
    if(select){
      select.innerHTML='<option value="">Selecciona una voz</option>'+list.map(v=>`<option value="${escape(v.voiceURI)}">${escape(v.name)} · ${escape(v.lang)}</option>`).join('');
      select.value=list.some(v=>v.voiceURI===selectedVoice)?selectedVoice:'';
      select.disabled=!list.length;
    }
    // Keep unavailable selections actionable: clicking explains what is missing.
    document.querySelectorAll('[data-audio-voice]').forEach(b=>{b.disabled=!window.speechSynthesis;});
    document.querySelectorAll('.audio-track').forEach(track=>{
      if(!track.querySelector('[data-audio-notice]'))track.querySelector('.controls').insertAdjacentHTML('afterend','<small data-audio-notice role="status"></small>');
    });
    persist();
    if(!window.speechSynthesis)status('Este navegador no ofrece lectura por voz. Puedes consultar las frases.');
    else if(!voices().length){
      retryVoices();
      status(loadAttempts<8?'Buscando voces de español…':'El navegador no ofrece voces de español. Instala una voz de español o prueba otro navegador.');
    }
    else {
      const {voice,notice}=resolveVoice();
      status(voice?`Listo para escuchar: ${voice.name} (${voice.lang}). Pulsa Escuchar.`:'A voz anterior não está mais disponível. Escolha uma voz na lista Voz para escuchar.');
    }
  }
  function stop() { activeTrackId=null;document.querySelectorAll('[data-audio-notice]').forEach(el=>{el.textContent='';});generation++;playing=null;activeUtterance=null;clearTimeout(startTimer);window.speechSynthesis?.cancel(); }
  function queue(utterance) {
    activeUtterance=utterance;
    const current=generation;
    startTimer=setTimeout(()=>{
      if(current!==generation)return;
      stop();status('La voz no se inició. Elige otra voz y vuelve a intentarlo.');
    },8000);
    utterance.onstart=()=>{if(current===generation)clearTimeout(startTimer);};
    const end=utterance.onend,error=utterance.onerror;
    utterance.onend=e=>{if(current===generation){clearTimeout(startTimer);activeUtterance=null;}end?.(e);};
    utterance.onerror=e=>{if(current===generation){clearTimeout(startTimer);activeUtterance=null;if(!error)status('No se pudo reproducir. Elige otra voz disponible.');}error?.(e);};
    window.speechSynthesis.resume?.();
    window.speechSynthesis.speak(utterance);
  }
  function speak(text, speed=rate) {
    stop();
    const {voice,notice}=resolveVoice();
    if(!voice)throw Error('No hay una voz seleccionada disponible. Elige una en Audios por tema o instala una voz de español.');
    status(`${notice||'Reproduciendo con: '}${voice.name} (${voice.lang}).`);
    const utterance=new SpeechSynthesisUtterance(text);
    utterance.voice=voice;utterance.lang=voice.lang;utterance.rate=Number(speed);
    queue(utterance);
  }
  function speakDialogue(dialogue) {
    stop();
    const speakers=[...new Set(dialogue.map(([who])=>who))];
    const preferred=resolveVoice().voice;
    const available=voices();
    const candidates=[preferred,...available.filter(v=>country&&language(v)===country),...available]
      .filter(Boolean).filter((v,i,list)=>list.findIndex(x=>x.voiceURI===v.voiceURI)===i);
    if(!candidates.length)throw Error('No hay voces de español disponibles. Comprueba las voces del navegador e inténtalo de nuevo.');
    const cast=new Map(speakers.map((who,i)=>[who,{
      voice:candidates[i%candidates.length],
      pitch:i<candidates.length?1:Math.max(0.6,Math.min(1.5,1+(i%2?-.3:.3)*Math.ceil(i/candidates.length)))
    }]));
    const current=generation;
    playing=true;
    function say(i) {
      if(current!==generation)return;
      if(i>=dialogue.length){playing=null;status('Diálogo terminado.');return;}
      const [who,text]=dialogue[i],{voice,pitch}=cast.get(who);
      status(`${who}: ${voice.name} (${voice.lang})${speakers.length>candidates.length?' · Personajes diferenciados por el tono de la misma voz.':''}`);
      const utterance=new SpeechSynthesisUtterance(text);
      utterance.voice=voice;utterance.lang=voice.lang;utterance.rate=rate;utterance.pitch=pitch;
      utterance.onend=()=>{if(current===generation)setTimeout(()=>say(i+1),350);};
      utterance.onerror=()=>{if(current===generation){stop();status('No se pudo reproducir el diálogo. Comprueba las voces y vuelve a intentarlo.');}};
      queue(utterance);
    }
    say(0);
  }
  function play(trackId,profile,phrase) {
    stop();sync();const track=tracks.find(t=>t.id===trackId),{voice,notice}=resolveVoice();
    if(!track)return;
    activeTrackId=track.id;
    if(!voice){
      if(!voices().length){loadAttempts=0;retryVoices();return status('No hay voces de español cargadas. Comprueba las voces del sistema o prueba otro navegador.');}
      return status('Elige una voz de la lista, encima de los audios.');
    }
    persist();
    const items=phrase===undefined?track.phrases:[track.phrases[Number(phrase)]];
    if(items.some(p=>!p))return;
    const current= generation;
    playing=true;
    function say(i) {
      if(current!==generation)return;
      if(i>=items.length){playing=null;status('Audio terminado. Repite en voz alta.');return;}
      status(`${notice}${voice.name} (${voice.lang}) · ${track.title} · ${i+1}/${items.length}: ${items[i][0]}`);
      const utterance=new SpeechSynthesisUtterance(items[i][0]);utterance.voice=voice;utterance.lang=voice.lang;utterance.rate=rate;
      utterance.onend=()=>{if(current===generation)setTimeout(()=>say(i+1),450);};
      utterance.onerror=event=>{if(current===generation&&event.error!=='canceled'&&event.error!=='interrupted'){playing=null;status('No se pudo reproducir. Prueba otra voz o comprueba la salida de sonido.');}};
      queue(utterance);
    }
    say(0);
  }
  document.addEventListener('click',event=>{
    const button=event.target.closest('button');if(!button)return;
    if(button.dataset.audioTrack)play(button.dataset.audioTrack,button.dataset.audioVoice,button.dataset.audioPhrase);
    if(button.id==='audio-stop'||button.id==='stop-audio'){stop();status('Audio detenido.');}
    if(button.id==='listen'){stop();status('Reproduciendo el diálogo de la lección.');}
    if(button.id==='logout')stop();
  });
  document.addEventListener('change',event=>{
    if(event.target.id==='audio-country'){stop();country=event.target.value;selectedVoice='';sync();}
    if(event.target.id==='audio-voice'){stop();selectedVoice=event.target.value;sync();}
    if(event.target.id==='audio-rate'){rate=Number(event.target.value);persist();if(playing){stop();status('Velocidad alterada. Clique em ouvir para recomeçar.');}}
  });
  window.speechSynthesis?.addEventListener('voiceschanged',sync);
  function renderControls(){const markup=render();return markup.slice(markup.indexOf('<div class="audio-settings">'),markup.indexOf('<div class="audio-levels">'));}
  return {render,sync,stop,speak,speakDialogue,configure,renderControls};
})();
