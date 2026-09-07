const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const pure={window:{}};vm.createContext(pure);vm.runInContext(fs.readFileSync('name-insights.js','utf8'),pure);
const insight=pure.window.VNameInsights;
const plain=value=>JSON.parse(JSON.stringify(value));
test('statistics normalize width and whitespace and count Unicode code points and record presence',()=>{
 const stats=plain(insight.analyze(['星星星','星月','Ａ Ｂ','𠮷野','ねこカフェ','123'].map(display_name=>({display_name}))));
 assert.equal(stats.total,6);assert.equal(stats.averageLength,2.8);
 assert.equal(stats.characters.find(r=>r.label==='星').count,2);
 assert.equal(stats.pairs.find(r=>r.label==='星星').count,1);
 assert.equal(stats.characters.find(r=>r.label==='𠮷').count,1);
 assert.equal(stats.lengths.reduce((n,r)=>n+r.count,0),6);
 assert.equal(stats.scripts.reduce((n,r)=>n+r.count,0),6);
 assert.equal(stats.scripts.find(r=>r.label==='複数の文字種').count,1);
 assert.equal(insight.analyze([]).averageLength,0);
});
test('malformed AI output is contained and valid suggestions are bounded and deduplicated',()=>{
 assert.equal(insight.parseReply('not JSON').valid,false);
 assert.equal(insight.parseReply('null').valid,false);
 const parsed=plain(insight.parseReply('```json\n'+JSON.stringify({reply:'提案',suggestions:[null,{name:'星ねこ',reading:'ほしねこ'},{name:'星ねこ'},{name:'a'.repeat(41)},{name:'<img src=x>',reason:'<script>alert(1)</script>'}]})+'\n```'));
 assert.equal(parsed.valid,true);assert.equal(parsed.suggestions.length,2);
 assert.equal(parsed.suggestions[1].name,'<img src=x>'); // Rendering must use textContent, not HTML.
 assert.match(insight.prompt(insight.analyze([]),'en'),/English/);
 assert.match(insight.prompt(insight.analyze([])),/時系列・人気/);
});

class El{
 constructor(tag='div'){this.tagName=tag;this.children=[];this.dataset={};this.style={};this.value='';this._text='';this.hidden=false;}
 set textContent(value){this._text=String(value);this.children=[];}
 get textContent(){return this._text+this.children.map(c=>c.textContent).join(' ');}
 append(...nodes){this.children.push(...nodes);}
 replaceChildren(...nodes){this._text='';this.children=nodes;}
 addEventListener(){}
 setAttribute(name,value){this[name]=value;}
 removeAttribute(name){delete this[name];}
 focus(){this.focused=true;}
}
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return{promise,resolve};};
async function harness(options={}){
 const elements=new Map(),get=id=>{if(!elements.has(id))elements.set(id,new El());return elements.get(id);};
 const tabs=['search','consult','trends'].map(name=>{const el=get('tab-'+name);el.dataset.tab=name;return el;});
 get('trend-platform').value='all';
 const document={getElementById:get,querySelectorAll:selector=>selector==='[data-tab]'?tabs:[],createElement:tag=>new El(tag),createTextNode:text=>{const el=new El('#text');el.textContent=text;return el;}};
 const state={fetches:[],imports:[],engineDeletes:0,conversationDeletes:0,cancels:0,requests:[],configs:[]};
 const conversation={
  async getTokenCount(){return options.tokenCount||1200;},
  async *sendMessageStreaming(input){
   state.requests.push(input);
   const raw=JSON.stringify({reply:'猫の案です。',suggestions:[{name:'星ねこ',reading:'ほしねこ',reason:'星と猫から'},{name:'<img src=x>',reason:'<script>alert(1)</script>'}]});
   yield{content:[{type:'text',text:raw.slice(0,30)}]};yield{content:[{type:'text',text:raw.slice(30)}]};
  },
  cancel(){state.cancels++;},
  async delete(){state.conversationDeletes++;}
 };
 const engine={
  async createConversation(config){state.configs.push(config);if(options.conversationGate)await options.conversationGate.promise;return conversation;},
  async delete(){state.engineDeletes++;}
 };
 const Engine={async create(config){state.engineConfig=config;if(options.engineGate)await options.engineGate.promise;return engine;}};
 const c={window:{addEventListener(){},VTUBER_DATA:[
  {source_id:'one',display_name:'星ねこ',reading:'ほしねこ',reading_source:'https://example.org',reading_source_kind:'official',platforms:['iriam'],platform_sources:{iriam:'https://example.org'}},
  {source_id:'two',display_name:'ほしねこ',platforms:['tiktok'],platform_sources:{tiktok:'https://example.org'}}
 ]},document,URL,AbortController,TransformStream,ReadableStream,TextEncoder,performance,
 navigator:options.noGPU?{}:{gpu:{requestAdapter:async()=>({})}},location:{hash:''},history:{replaceState(_s,_t,hash){c.location.hash=hash;}},
 translateUI(){},setLanguage(){},language:'ja',
 fetch:async(url,{signal})=>{state.fetches.push(url);if(options.failDownload)throw new Error('Network');return{ok:true,headers:{get:()=>String(4)},body:new ReadableStream({start(controller){controller.enqueue(new Uint8Array(4));controller.close();}})}}
 };
 vm.createContext(c);
 const module=new vm.SyntheticModule(['Engine'],function(){this.setExport('Engine',Engine);},{context:c});await module.link(()=>{});await module.evaluate();
 for(const file of ['platforms.js','app.js','name-insights.js','naming.js']){
  const script=new vm.Script(fs.readFileSync(file,'utf8'),{filename:file,importModuleDynamically:async url=>{state.imports.push(url);return module;}});script.runInContext(c);
 }
 return{get,state,c,tabs,submit:()=>get('ai-form').onsubmit({preventDefault(){}})};
}
test('search and platform-filtered analysis work without model or SDK downloads',async()=>{
 const h=await harness({noGPU:true});h.tabs[2].onclick();
 assert.match(h.get('trend-content').textContent,/集計対象 2/);
 h.get('trend-platform').value='iriam';h.get('trend-platform').onchange();assert.match(h.get('trend-content').textContent,/集計対象 1/);
 assert.equal(h.state.fetches.length,0);assert.equal(h.state.imports.length,0);
 await h.get('ai-start').onclick();assert.match(h.get('ai-status').textContent,/WebGPUを利用できません/);assert.equal(h.get('ai-send').disabled,true);
 h.tabs[0].onclick();assert.equal(h.get('panel-search').hidden,false);
});
test('opt-in model load, actual dictionary collision checks, and follow-up context',async()=>{
 const h=await harness();assert.equal(h.state.fetches.length,0);
 await h.get('ai-start').onclick();assert.equal(h.get('ai-send').disabled,false);
 assert.match(h.state.imports[0],/@litert-lm\/core@0\.17\.0/);assert.match(h.state.fetches[0],/gemma-4-E2B-it-web\.litertlm$/);
 h.get('ai-message').value='猫の名前';await h.submit();
 assert.equal(h.state.configs[0].prefillPrefaceOnInit,true);
 assert.match(h.state.configs[0].preface.messages[0].content,/"total":2/);
 assert.match(h.get('ai-log').textContent,/同名・同じ読みの候補: 2 件/);
 const answer=h.get('ai-log').children[1];const card=answer.children[2].children[1];assert.equal(card.children[0].textContent,'<img src=x>');assert.equal(card.children[0].children.length,0);
 answer.children[2].children[0].children.at(-1).onclick();assert.equal(h.get('query').value,'星ねこ');assert.match(h.get('results').textContent,/星ねこ/);
 h.get('ai-message').value='別の名前';await h.submit();assert.match(h.state.requests[1],/matching_records":2/);
 await h.get('ai-unload').onclick();assert.equal(h.state.engineDeletes,1);assert.equal(h.state.conversationDeletes,1);assert.equal(h.get('ai-send').disabled,true);
});
test('a failed download leaves the rest of the site and retry available',async()=>{
 const h=await harness({failDownload:true});await h.get('ai-start').onclick();assert.match(h.get('ai-status').textContent,/AIを起動できませんでした/);assert.equal(h.get('ai-start').disabled,false);h.tabs[2].onclick();assert.match(h.get('trend-content').textContent,/集計対象 2/);
});
test('unloading during engine initialization prevents a second model from loading and deletes the stale engine',async()=>{
 const gate=deferred(),h=await harness({engineGate:gate});const loading=h.get('ai-start').onclick();
 while(!h.state.engineConfig)await new Promise(setImmediate);
 const unloading=h.get('ai-unload').onclick();assert.equal(h.get('ai-start').disabled,true);
 await h.get('ai-start').onclick();assert.equal(h.state.fetches.length,1);
 gate.resolve();await loading;await unloading;assert.equal(h.state.engineDeletes,1);assert.equal(h.get('ai-send').disabled,true);assert.equal(h.get('ai-start').disabled,false);
});
test('unloading during conversation initialization cannot publish stale suggestions or leak a conversation',async()=>{
 const gate=deferred(),h=await harness({conversationGate:gate});await h.get('ai-start').onclick();h.get('ai-message').value='相談';const sending=h.submit();
 while(!h.state.configs.length)await new Promise(setImmediate);
 const unloading=h.get('ai-unload').onclick();gate.resolve();await sending;await unloading;
 assert.equal(h.state.conversationDeletes,1);assert.equal(h.state.engineDeletes,1);assert.equal(h.state.requests.length,0);assert.equal(h.get('ai-send').disabled,true);
});
test('context capacity is checked before inference and keeps the unsent input',async()=>{
 const h=await harness({tokenCount:7900});await h.get('ai-start').onclick();h.get('ai-message').value='長い相談の続き';await h.submit();assert.equal(h.state.requests.length,0);assert.equal(h.get('ai-message').value,'長い相談の続き');assert.match(h.get('ai-status').textContent,/会話が長く/);
});
