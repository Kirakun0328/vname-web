const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const context={window:{},URL};vm.createContext(context);vm.runInContext(fs.readFileSync('platforms.js','utf8'),context);
const p=context.window.VNamePlatforms;
const detail=r=>JSON.parse(JSON.stringify(p.details({source_id:'example',...r})));
test('YouTube account alone does not imply main platform',()=>{
 const d=detail({source_id:'youtube:UC'+'a'.repeat(22)});
 assert.deepEqual(d.primary,[]);assert.deepEqual(d.known,['YouTube']);
});
test('multiple explicit main platforms retain source and safe links',()=>{
 const d=detail({primary_platforms:['iriam','reality'],primary_platform_source:'https://agency.example/profile',primary_platform_evidence:'official_broadcast_destinations',platform_accounts:[{url:'https://web.iriam.app/s/user/ABC?uuid=123'}]});
 assert.deepEqual(d.primary,['IRIAM','REALITY']);assert.equal(d.accounts[0].url,'https://web.iriam.app/s/user/ABC');
});
test('reject untrusted source and account URLs',()=>{
 assert.deepEqual(detail({primary_platforms:['tiktok'],primary_platform_source:'javascript:alert(1)',primary_platform_evidence:'x'}).primary,[]);
 assert.equal(p.account('https://tiktok.com.evil.test/@example'),null);
 assert.equal(p.account('https://twitch.tv/directory'),null);
});
test('Avvy interview can establish platform without claiming it is primary',()=>{
 const d=detail({platforms:['avvy'],platform_sources:{avvy:'https://panora.tokyo/archives/137121'}});
 assert.deepEqual(d.known,['Avvy']);assert.deepEqual(d.primary,[]);
});
test('existing Twitch metadata remains visible',()=>{
 assert.deepEqual(detail({twitch_login:'example'}).known,['Twitch']);
});
test('scripts exist and load before app',()=>{
 const html=fs.readFileSync('index.html','utf8');
 const scripts=[...html.matchAll(/<script src="([^"?]+)(?:\?[^\"]*)?"/g)].map(m=>m[1]);
 for(const file of scripts){assert.ok(fs.existsSync(file),file);new vm.Script(fs.readFileSync(file,'utf8'),{filename:file});}
 for(const file of ['platforms.js','platform-data.js'])assert.ok(scripts.indexOf(file)>=0&&scripts.indexOf(file)<scripts.indexOf('app.js'));
});
test('published data searches and renders a TikTok V-liver without requiring YouTube',()=>{
 class El {
  constructor(tag='div'){this.tagName=tag;this.children=[];this.dataset={};this.value='';this._text='';}
  set textContent(value){this._text=String(value);this.children=[];}
  get textContent(){return this._text+this.children.map(c=>c.textContent).join(' ');}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(...nodes){this._text='';this.children=nodes;}
  addEventListener(){}
  setAttribute(name,value){this[name]=value;}
 }
 const els=new Map();const get=id=>{if(!els.has(id))els.set(id,new El());return els.get(id);};
 const doc={getElementById:get,createElement:tag=>new El(tag),createTextNode:value=>{const e=new El('#text');e.textContent=value;return e;},querySelectorAll:()=>[]};
 const c={window:{},document:doc,URL,translateUI:()=>{},setLanguage:()=>{}};vm.createContext(c);
 for(const file of ['data.js','extra-data.js','readings.js','platform-data.js','platforms.js','app.js'])vm.runInContext(fs.readFileSync(file,'utf8'),c);
 get('query').value='ルーカ・アレイス';vm.runInContext('search()',c);
 assert.match(get('results').textContent,/ルーカ・アレイス/);assert.match(get('results').textContent,/主な活動媒体 TikTok LIVE/);
 get('query').value='マほ姉';vm.runInContext('search()',c);assert.match(get('results').textContent,/IRIAM \/ REALITY/);
 get('query').value='あいうえ おばけ';vm.runInContext('search()',c);assert.match(get('results').textContent,/確認できた媒体 Avvy/);
 get('query').value='兎田ぺこら';vm.runInContext('search()',c);assert.match(get('results').textContent,/うさだぺこら/);
 get('query').value='枯葉 楓';vm.runInContext('search()',c);assert.match(get('results').textContent,/こば かえで/);assert.match(get('results').textContent,/主な活動媒体 IRIAM/);assert.match(get('results').textContent,/Vライバー/);
 get('query').value='日暮園';vm.runInContext('search()',c);assert.match(get('results').textContent,/主な活動媒体 REALITY/);
});
