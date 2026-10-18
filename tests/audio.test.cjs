// Execute: node --test tests/audio.test.cjs
const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');

test('temas independentes, vozes diferentes e cancelamento entre frases',()=>{
  const listeners={},timers=[],spoken=[],nodes={};
  for(const id of ['audio-female','audio-male','audio-status','audio-rate'])nodes['#'+id]={value:id==='audio-rate'?'0.75':'',textContent:'',innerHTML:''};
  const voices=[{name:'Microsoft Elvira',lang:'es-ES',voiceURI:'female-es'},{name:'Microsoft Alvaro',lang:'es-ES',voiceURI:'male-es'}];
  let changed;
  const document={addEventListener:(name,fn)=>listeners[name]=fn,querySelector:s=>nodes[s],querySelectorAll:()=>[]};
  const window={speechSynthesis:{getVoices:()=>voices,cancel:()=>{},speak:u=>spoken.push(u),addEventListener:(event,fn)=>changed=fn}};
  const context=vm.createContext({window,document,SpeechSynthesisUtterance:function(text){this.text=text;},setTimeout:fn=>timers.push(fn)});
  vm.runInContext(fs.readFileSync('static/audio.js','utf8'),context);
  const audio=window.AudioPractice;
  const html=audio.render();
  assert.match(html,/Saudações/);assert.match(html,/Despedidas/);assert.match(html,/Como você está/);
  changed();
  assert.equal(nodes['#audio-female'].value,'female-es');
  assert.equal(nodes['#audio-male'].value,'male-es');
  function click(dataset){listeners.click({target:{closest:()=>({dataset})}});}
  click({audioTrack:'saludos',audioVoice:'female'});
  assert.equal(spoken[0].voice.voiceURI,'female-es');
  assert.equal(spoken[0].text,'¡Hola!');
  assert.equal(spoken[0].rate,.75);
  spoken[0].onend();
  audio.stop();
  timers.shift()();
  assert.equal(spoken.length,1,'parar impede a próxima frase agendada');
  click({audioTrack:'despedidas',audioVoice:'male',audioPhrase:'1'});
  assert.equal(spoken[1].text,'Hasta luego.');
  assert.equal(spoken[1].voice.voiceURI,'male-es');
  click({audioTrack:'sentimientos',audioVoice:'female',audioPhrase:'2'});
  assert.equal(spoken[2].text,'¿Cómo te sientes hoy?');
  voices.length=0;changed();
  assert.match(nodes['#audio-status'].textContent,/Nenhuma voz/);
  assert.equal(nodes['#audio-female'].value,'');
});
