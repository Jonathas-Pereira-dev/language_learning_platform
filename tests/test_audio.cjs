const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('static/audio.js', 'utf8');
const storage = new Map();
const voices = [
  {voiceURI:'female-es',name:'Elvira',lang:'es-ES'},
  {voiceURI:'male-mx',name:'Jorge',lang:'es-MX'},
  {voiceURI:'custom-mx',name:'Custom voice',lang:'es-MX'}
  ,{voiceURI:'us-es',name:'US voice',lang:'es-US'}
];
function load(notices=[]) {
  const events={}, spoken=[], elements={}, timers=new Map();let timerId=0;
  for(const id of ['audio-country','audio-rate','audio-voice','audio-status'])
    elements['#'+id]={value:'',textContent:'',insertAdjacentHTML(){}};
  const synthesis={getVoices:()=>voices,cancel(){},speak:u=>spoken.push(u),addEventListener(){}};
  const context={window:{speechSynthesis:synthesis},
    localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},
    document:{querySelector:s=>elements[s],querySelectorAll:s=>s==='[data-audio-notice]'?notices:[],addEventListener:(n,f)=>events[n]=f},
    Intl,SpeechSynthesisUtterance:function(text){this.text=text;},
    setTimeout:(fn,delay)=>{timers.set(++timerId,{fn,delay});return timerId;},clearTimeout:id=>timers.delete(id)};
  vm.runInNewContext(source,context);
  context.window.AudioPractice.configure([{id:'saludos',title:'Saludos',level:'A1',phrases:[['Hola','Hola']]}],'A1');
  context.window.AudioPractice.sync();
  return {audio:context.window.AudioPractice,events,spoken,elements,timers};
}
let app=load();
app.audio.configure([{id:'saludos',title:'Saludos',level:'A1',phrases:[['Hola','Hola']]},{id:'advanced',title:'Tema avanzado',level:'A2',phrases:[['Buenas tardes','Buenas tardes']]}],'A1');
assert.match(app.audio.render(),/Nivel A1/);
assert.ok(!app.audio.render().includes('Tema avanzado'));
assert.ok(!app.audio.renderControls().includes('audio-level-group'));
app.audio.configure([{id:'saludos',title:'Saludos',level:'A1',phrases:[['Hola','Hola']]},{id:'advanced',title:'Tema avanzado',level:'A2',phrases:[['Buenas tardes','Buenas tardes']]}],'A2');
assert.match(app.audio.render(),/Nivel A2/);
assert.match(app.audio.render(),/Nivel A1/);
assert.ok(app.audio.render().includes('id="audio-voice"'));
assert.ok(!app.audio.render().includes('id="audio-gender"'));
assert.ok(!app.elements['#audio-country'].innerHTML.includes('es-AR'),'only available regions listed');
assert.ok(app.elements['#audio-country'].innerHTML.includes('es-mx'));
assert.ok(!app.elements['#audio-country'].innerHTML.includes('es-us'),'US voices excluded');
app.events.change({target:{id:'audio-voice',value:'custom-mx'}});
app.audio.speak('Hola',0.75);
assert.equal(app.spoken[0].voice,voices[2]);
assert.equal(app.spoken[0].rate,0.75);
app=load();
app.audio.speak('Otra vez');
assert.equal(app.spoken[0].voice,voices[2],'selection persists');
app.events.change({target:{id:'audio-country',value:'es-es'}});
assert.ok(!app.elements['#audio-voice'].innerHTML.includes('custom-mx'));
app.events.click({target:{closest:()=>({dataset:{audioTrack:'saludos',audioVoice:'selected',audioPhrase:'0'}})}});
assert.equal(app.spoken.at(-1).voice,voices[0]);
app.events.change({target:{id:'audio-country',value:'es-mx'}});
app.events.change({target:{id:'audio-voice',value:'custom-mx'}});
voices.splice(2,1);
assert.throws(()=>app.audio.speak('No silent replacement'),/voz/);
app.audio.sync();
assert.match(app.elements['#audio-status'].textContent,/anterior/);
storage.clear();
const available=voices.splice(0);
app=load();
assert.match(app.elements['#audio-status'].textContent,/Buscando/);
for(let i=0;i<8;i++){
  const [id,timer]=[...app.timers.entries()].find(([,t])=>t.delay===500);
  app.timers.delete(id);timer.fn();
}
assert.equal(app.timers.size,0);
assert.match(app.elements['#audio-status'].textContent,/no ofrece/);
voices.push(...available);
app.audio.sync();
app.events.click({target:{closest:()=>({dataset:{audioTrack:'saludos',audioVoice:'selected',audioPhrase:'0'}})}});
assert.equal(app.spoken.at(-1).voice,voices[0]);
const watchdog=[...app.timers.values()].find(t=>t.delay===8000);
watchdog.fn();
assert.match(app.elements['#audio-status'].textContent,/no se inició/);
app=load();
app.audio.speakDialogue([['Cliente','Hola'],['Recepcionista','Buenos días'],['Cliente','Gracias']]);
const first=app.spoken.at(-1);
function nextLine() {
  app.spoken.at(-1).onstart();
  app.spoken.at(-1).onend();
  const [id,timer]=[...app.timers.entries()].find(([,t])=>t.delay===350);
  app.timers.delete(id);timer.fn();
}
nextLine();
assert.notEqual(app.spoken.at(-1).voice.voiceURI,first.voice.voiceURI);
nextLine();
assert.equal(app.spoken.at(-1).voice.voiceURI,first.voice.voiceURI);
app.audio.speakDialogue([['A','Hola'],['B','Hola']]);
app.audio.stop();
const count=app.spoken.length;
for(const [id,timer] of [...app.timers])if(timer.delay===350){app.timers.delete(id);timer.fn();}
assert.equal(app.spoken.length,count);
const otherVoices=voices.splice(1);
app=load();
app.audio.speakDialogue([['A','Hola'],['B','Buenas'],['A','Gracias']]);
const singleVoiceFirst=app.spoken.at(-1);
nextLine();
assert.equal(app.spoken.at(-1).voice,singleVoiceFirst.voice);
assert.notEqual(app.spoken.at(-1).pitch,singleVoiceFirst.pitch);
nextLine();
assert.equal(app.spoken.at(-1).pitch,singleVoiceFirst.pitch);
voices.push(...otherVoices);
console.log('Audio voice selection and dialogue tests passed.');

const notices=['saludos','despedidas'].map(id=>({textContent:'',closest:()=>({querySelector:()=>({dataset:{audioTrack:id}})})}));
app=load(notices);
app.audio.configure([{id:'saludos',title:'Saludos',level:'A1',phrases:[['Hola','Hola']]},{id:'despedidas',title:'Despedidas',level:'A1',phrases:[['Adiós','Adiós']]}],'A1');
function clickTrack(id){app.events.click({target:{closest:()=>({dataset:{audioTrack:id,audioVoice:'selected'}})}});}
clickTrack('saludos');
assert.match(notices[0].textContent,/Saludos/);
assert.equal(notices[1].textContent,'');
clickTrack('despedidas');
assert.equal(notices[0].textContent,'');
assert.match(notices[1].textContent,/Despedidas/);
app.audio.stop();
assert.ok(notices.every(n=>n.textContent===''));
