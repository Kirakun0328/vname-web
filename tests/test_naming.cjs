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
 assert.equal(insight.parseReply('普通の文章で候補を提案します。').valid,true);
 assert.equal(insight.parseReply('{"reply":"提案があります","suggestions":[').reply,'提案があります');
 assert.equal(insight.parseReply('').valid,false);
 assert.equal(insight.parseReply('null').valid,false);
 const parsed=plain(insight.parseReply('```json\n'+JSON.stringify({reply:'提案',suggestions:[null,{name:'星ねこ',reading:'ほしねこ'},{name:'星ねこ'},{name:'a'.repeat(41)},{name:'<img src=x>',reason:'<script>alert(1)</script>'}]})+'\n```'));
 assert.equal(parsed.valid,true);assert.equal(parsed.suggestions.length,2);
 assert.equal(parsed.suggestions[1].name,'<img src=x>'); // Rendering must use textContent, not HTML.
 assert.match(insight.prompt(insight.analyze([]),'en'),/English/);
 assert.match(insight.prompt(insight.analyze([])),/時系列・人気/);
});
test('truncated responses retain complete candidates without inventing unfinished names',()=>{
 const result=plain(insight.parseReply('{"suggestions":[{"name":"月乃しずく","reading":"つきのしずく","reason":"優しい響き"},{"name":"未完成'));
 assert.equal(result.incomplete,true);assert.equal(result.suggestions.length,1);assert.equal(result.suggestions[0].name,'月乃しずく');
 const nested=plain(insight.parseReply('{"suggestions":[{"name":"星ねこ","reason":"引用: \\"ねこ\\" と {星}"}],"reply":"途中'));
 assert.equal(nested.suggestions.length,1);
 assert.equal(insight.parseReply('{}').valid,false);
 const lines=insight.parseRepair('名前 | 読み | 理由\n--- | --- | ---\n1. 月乃しずく | つきのしずく | 優しい響き\n2. 陽だまりこはる | ひだまりこはる | 暖かな印象');
 assert.equal(lines.suggestions.length,2);assert.equal(lines.suggestions[0].name,'月乃しずく');
 assert.equal(insight.parseRepair('39くん | みくくん | 数字を使った響き').suggestions[0].name,'39くん');
 assert.equal(insight.parseRepair('優しい名前を提案します。').suggestions.length,0);
 assert.equal(insight.wantsNames('癒やし系、優しい響きの名前が欲しい。'),true);
 assert.equal(insight.wantsNames('名前の傾向の分析だけお願いします。'),false);
});
test('name pattern statistics use code points and per-record frequencies',()=>{
 const stats=plain(insight.analyze(['月乃しずく','月乃こはる','星乃しずく','ＡＢ','𠮷野'].map(display_name=>({display_name}))));
 assert.equal(stats.medianLength,5);assert.equal(stats.exactLengths[2],2);
 assert.deepEqual(stats.prefixes.find(x=>x.label==='月乃'),{label:'月乃',count:2});
 assert.deepEqual(stats.suffixes.find(x=>x.label==='ずく'),{label:'ずく',count:2});
 assert.equal(stats.commonLengths[0].length,5);assert.equal(insight.analyze([]).medianLength,0);
});

class El{
 constructor(tag='div'){this.tagName=tag;this.children=[];this.dataset={};this.style={};this.value='';this._text='';this.hidden=false;}
 set textContent(value){this._text=String(value);this.children=[];}
 get textContent(){return this._text+this.children.map(c=>c.textContent).join(' ');}
 append(...nodes){this.children.push(...nodes);}
 replaceChildren(...nodes){this._text='';this.children=nodes;}
 addEventListener(name,callback){this['on'+name]=callback;}
 setAttribute(name,value){this[name]=value;}
 removeAttribute(name){delete this[name];}
 focus(){this.focused=true;}
}
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return{promise,resolve};};
async function harness(options={}){
 const elements=new Map(),get=id=>{if(!elements.has(id))elements.set(id,new El());return elements.get(id);};
 const tabs=['search','consult','trends'].map(name=>{const el=get('tab-'+name);el.dataset.tab=name;return el;});
 get('trend-platform').value='all';get('ai-save').checked=true;
 const document={getElementById:get,querySelectorAll:selector=>selector==='[data-tab]'?tabs:[],createElement:tag=>new El(tag),createTextNode:text=>{const el=new El('#text');el.textContent=text;return el;}};
 const state={fetches:[],imports:[],engineDeletes:0,conversationDeletes:0,starterDeletes:0,starterConfigs:[],cancels:0,requests:[],configs:[]};
 const conversation={
  async getTokenCount(){return options.tokenCount||1200;},
  async *sendMessageStreaming(input){
   const index=state.requests.length;
   state.requests.push(input);
   const raw=options.responses?.[index]??JSON.stringify({reply:'猫の案です。',suggestions:[{name:'星ねこ',reading:'ほしねこ',reason:'星と猫から'},{name:'<img src=x>',reason:'<script>alert(1)</script>'}],next_prompts:['もっと短い名前にしたい','英字での表記も考えて']});
   yield{content:[{type:'text',text:raw.slice(0,30)}]};if(options.replyGate)await options.replyGate.promise;if(index>0&&options.repairGate)await options.repairGate.promise;yield{content:[{type:'text',text:raw.slice(30)}]};
  },
  cancel(){state.cancels++;},
  async delete(){state.conversationDeletes++;}
 };
 const engine={
  async createConversation(config){
   if(config.sessionConfig.maxOutputTokens===256){
    state.starterConfigs.push(config);if(options.starterGate)await options.starterGate.promise;
    return {async *sendMessageStreaming(){yield options.badStarter?'null':JSON.stringify({next_prompts:['雨と鉱石の名前を考えたい','<img src=x>','雨と鉱石の名前を考えたい']});},async delete(){state.starterDeletes++;},cancel(){state.cancels++;}};
   }
   state.configs.push(config);if(options.conversationGate)await options.conversationGate.promise;return conversation;
  },
  async delete(){state.engineDeletes++;}
 };
 const Engine={async create(config){state.engineConfig=config;if(options.engineGate)await options.engineGate.promise;return engine;}};
 const c={window:{VNameModel:{status:async()=>({supported:true,saved:false}),remove:async()=>{},obtain:async()=>{state.fetches.push('gemma-4-E2B-it-web.litertlm');if(options.failDownload)throw new Error('MODEL_DOWNLOAD');return new ReadableStream({start(c){c.close();}});}},addEventListener(){},VTUBER_DATA:options.rows||[
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
 const answer=h.get('ai-log').children[1].children[1];const card=answer.children[2].children[1];assert.equal(card.children[0].textContent,'<img src=x>');assert.equal(card.children[0].children.length,0);
 answer.children[2].children[0].children.at(-1).onclick();assert.equal(h.get('query').value,'星ねこ');assert.match(h.get('results').textContent,/星ねこ/);
 h.get('ai-message').value='別の名前';await h.submit();assert.match(h.state.requests[1],/matching_records":2/);
 await h.get('ai-unload').onclick();assert.equal(h.state.engineDeletes,1);assert.equal(h.state.conversationDeletes,1);assert.equal(h.get('ai-send').disabled,true);
});
test('a failed download leaves the rest of the site and retry available',async()=>{
 const h=await harness({failDownload:true});await h.get('ai-start').onclick();assert.match(h.get('ai-status').textContent,/AIを起動できませんでした/);assert.equal(h.get('ai-start').disabled,false);h.tabs[2].onclick();assert.match(h.get('trend-content').textContent,/集計対象 2/);
});
test('conversation chips come from AI, populate the input without sending, and change with replies',async()=>{
 const h=await harness();assert.equal(h.get('ai-prompts').children.length,0);
 await h.get('ai-start').onclick();assert.equal(h.state.starterDeletes,1);
 const chips=h.get('ai-prompts').children;assert.equal(chips.length,2);assert.equal(chips[0].textContent,'雨と鉱石の名前を考えたい');assert.equal(chips[1].children.length,0);
 chips[0].onclick();assert.equal(h.get('ai-message').value,'雨と鉱石の名前を考えたい');assert.equal(h.state.requests.length,0);
 await h.submit();assert.equal(h.get('ai-prompts').children[0].textContent,'もっと短い名前にしたい');assert.equal(h.state.starterConfigs.length,1);
 await h.get('ai-reset').onclick();assert.equal(h.get('ai-prompts').children[0].textContent,'雨と鉱石の名前を考えたい');
});
test('invalid starter generation leaves manual input available without canned suggestions',async()=>{
 const h=await harness({badStarter:true});await h.get('ai-start').onclick();
 assert.equal(h.get('ai-prompts').children.length,0);assert.match(h.get('ai-prompts-status').textContent,/直接入力/);assert.equal(h.get('ai-send').disabled,false);
});
test('unloading during starter setup disposes the pending context without publishing late chips',async()=>{
 const gate=deferred(),h=await harness({starterGate:gate});const loading=h.get('ai-start').onclick();
 while(!h.state.starterConfigs.length)await new Promise(setImmediate);
 const unloading=h.get('ai-unload').onclick();gate.resolve();await loading;await unloading;
 assert.equal(h.state.starterDeletes,1);assert.equal(h.state.engineDeletes,1);assert.equal(h.get('ai-prompts').children.length,0);assert.equal(h.get('ai-send').disabled,true);
});
test('new replies respect readers scrolling through older messages',async()=>{
 const gate=deferred(),h=await harness({replyGate:gate});await h.get('ai-start').onclick();
 const history=h.get('ai-history');history.scrollHeight=1600;history.clientHeight=400;history.scrollTop=1200;
 h.get('ai-message').value='名前を相談';const sending=h.submit();
 while(!h.state.requests.length)await new Promise(setImmediate);
 history.scrollTop=200;history.onscroll();gate.resolve();await sending;
 assert.equal(history.scrollTop,200);
 history.scrollTop=1200;history.onscroll();history.scrollHeight=2200;
 h.get('ai-message').value='別の候補';await h.submit();assert.equal(history.scrollTop,2200);
 await h.get('ai-reset').onclick();assert.equal(history.scrollTop,0);
});
test('intro-only name replies get one bounded repair and actual checked candidate cards',async()=>{
 const h=await harness({responses:['{"reply":"癒やし系の名前を提案します。","suggestions":[','月乃しずく | つきのしずく | 優しい響き\n陽だまりこはる | ひだまりこはる | 暖かな印象']});
 await h.get('ai-start').onclick();h.get('ai-message').value='癒やし系、優しい響きの名前が欲しい。';await h.submit();
 assert.equal(h.state.requests.length,2);assert.equal(h.get('ai-log').children.length,2);assert.match(h.get('ai-log').textContent,/月乃しずく/);assert.match(h.get('ai-log').textContent,/傾向との比較/);assert.equal(h.get('ai-status').dataset.error,'false');
});
test('failed repair never reports success or loops; analysis-only requests do not force names',async()=>{
 const h=await harness({responses:['{"reply":"提案します"}','候補を作ります']});await h.get('ai-start').onclick();h.get('ai-message').value='名前を考えて';await h.submit();
 assert.equal(h.state.requests.length,2);assert.match(h.get('ai-log').textContent,/具体的な名前候補を生成できませんでした/);assert.equal(h.get('ai-status').dataset.error,'true');
 const analysis=await harness({responses:['{"reply":"収録は2件です","suggestions":[]}']});await analysis.get('ai-start').onclick();analysis.get('ai-message').value='名前の傾向の分析だけお願い';await analysis.submit();assert.equal(analysis.state.requests.length,1);
});
test('unloading during candidate repair prevents late candidates from appearing',async()=>{
 const gate=deferred(),h=await harness({responses:['{"reply":"提案します"}','遅い候補 | おそいこうほ | 遅延'],repairGate:gate});await h.get('ai-start').onclick();h.get('ai-message').value='名前を考えて';const sending=h.submit();
 while(h.state.requests.length<2)await new Promise(setImmediate);
 const unloading=h.get('ai-unload').onclick();gate.resolve();await sending;await unloading;
 assert.doesNotMatch(h.get('ai-log').textContent,/遅い候補/);assert.equal(h.state.engineDeletes,1);
});
test('platform, tag and script filters determine the next conversation statistics',async()=>{
 const h=await harness({rows:[
  {source_id:'ai',display_name:'月乃しずく',category:'AIVTuber',platforms:['youtube'],platform_sources:{youtube:'https://example.org'}},
  {source_id:'v',display_name:'月乃こはる',vliver_source:'https://example.org',platforms:['iriam'],platform_sources:{iriam:'https://example.org'}},
  {source_id:'en',display_name:'Luna',category:'AIVTuber',platforms:['youtube'],platform_sources:{youtube:'https://example.org'}}]});
 h.get('trend-tag').value='AIVTuber';h.get('trend-script').value='kana';h.get('trend-platform').value='youtube';h.tabs[2].onclick();assert.match(h.get('trend-content').textContent,/集計対象 1/);
 await h.get('ai-start').onclick();h.get('ai-message').value='名前を考えて';await h.submit();assert.match(h.state.configs[0].preface.messages[0].content,/"total":1/);assert.match(h.state.configs[0].preface.messages[0].content,/"tag":"AIVTuber"/);
 h.get('trend-tag').value='all';h.get('trend-script').value='all';h.get('trend-platform').value='all';h.get('trend-platform').onchange();h.get('ai-message').value='別の名前を考えて';await h.submit();assert.equal(h.state.configs.length,2);assert.match(h.state.configs[1].preface.messages[0].content,/"total":3/);
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

test('expanded statistics count unique record presence and distinguish reading provenance',()=>{
 const rows=[{display_name:'星ねこ',reading:'ほしねこ',reading_inferred:false},{display_name:'星ねこ',reading:'ほしねこ',reading_inferred:true},{display_name:'ねこねこ'},{display_name:'Ａlice'},{display_name:'alice'}];
 const s=plain(insight.analyze(rows));assert.equal(s.uniqueNames,3);assert.equal(s.duplicateGroups,2);assert.equal(s.duplicateRecords,4);
 assert.equal(s.ngrams2.find(r=>r.label==='ねこ').count,3);assert.equal(s.ngrams3.find(r=>r.label==='星ねこ').count,2);
 assert.equal(s.readingStatus.find(r=>r.label==='推定の読み').count,1);assert.equal(s.readable,2);
 const c=plain(insight.compare([{display_name:'ねこ',groups:['A','A','B']},{display_name:'星月空',groups:['A']}],r=>r.groups));
 assert.equal(c[0].count,2);assert.equal(c[0].averageLength,2.5);assert.equal(c[0].kanaPercent,50);assert.equal(c[1].count,1);
});
