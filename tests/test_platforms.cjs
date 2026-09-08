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
test('equivalent channel URLs and a known handle do not repeat a platform link',()=>{
 const cid='UC'+'a'.repeat(22);
 const d=detail({source_id:'youtube:'+cid,youtube_channel_id:cid,youtube_handle:'@Example',platform_accounts:[
  {url:'https://youtube.com/channel/'+cid+'?feature=share'},
  {url:'https://m.youtube.com/channel/'+cid+'/'},
  {url:'https://www.youtube.com/@EXAMPLE'}]});
 assert.equal(d.accounts.length,1);assert.equal(d.accounts[0].url,'https://www.youtube.com/channel/'+cid);
 assert.equal(d.groups.length,1);
});
test('different accounts on one platform remain available in one group',()=>{
 const d=detail({platform_accounts:[{url:'https://youtube.com/channel/UC'+'a'.repeat(22)},{url:'https://youtube.com/channel/UC'+'b'.repeat(22)}]});
 assert.equal(d.accounts.length,2);assert.equal(d.groups.length,1);assert.equal(d.groups[0].accounts.length,2);
});
test('Unicode handles and IRIAM query identities remain usable',()=>{
 assert.equal(p.account('https://www.youtube.com/@しずく').url,p.account('https://youtube.com/%40%E3%81%97%E3%81%9A%E3%81%8F').url);
 assert.equal(p.account('https://web.iriam.app/s/user?id=ABC&tracking=1').url,'https://web.iriam.app/s/user?id=ABC');
 assert.equal(p.account('https://www.youtube.com/channel/UC'+'a'.repeat(22)).url,'https://www.youtube.com/channel/UC'+'a'.repeat(22));
 assert.equal(p.account('https://www.youtube.com/@bad%2Fhandle'),null);
});
test('scripts exist and load before app',()=>{
 const html=fs.readFileSync('index.html','utf8');
 const scripts=[...html.matchAll(/<script src="([^"?]+)(?:\?[^\"]*)?"/g)].map(m=>m[1]);
 for(const file of scripts){assert.ok(fs.existsSync(file),file);new vm.Script(fs.readFileSync(file,'utf8'),{filename:file});}
 for(const file of ['platforms.js','platform-data.js'])assert.ok(scripts.indexOf(file)>=0&&scripts.indexOf(file)<scripts.indexOf('app.js'));
});
test('published data searches and renders reviewed and licensed-source records',()=>{
 class El {
  constructor(tag='div'){this.tagName=tag;this.children=[];this.dataset={};this.value='';this._text='';}
  set textContent(value){this._text=String(value);this.children=[];}
  get textContent(){return this._text+this.children.map(c=>c.textContent).join(' ');}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(...nodes){this._text='';this.children=nodes;}
  addEventListener(event,handler){(this.events||={})[event]=handler;}
  setAttribute(name,value){this[name]=value;}
 }
 const els=new Map();const get=id=>{if(!els.has(id))els.set(id,new El());return els.get(id);};
 const doc={getElementById:get,createElement:tag=>new El(tag),createTextNode:value=>{const e=new El('#text');e.textContent=value;return e;},querySelectorAll:()=>[]};
 const c={window:{},document:doc,URL,translateUI:()=>{},setLanguage:()=>{}};vm.createContext(c);
 for(const file of ['data.js','extra-data.js','readings.js','platform-data.js','platforms.js','primary-data.js','app.js'])vm.runInContext(fs.readFileSync(file,'utf8'),c);
 get('query').value='Luca黒蜜糖';vm.runInContext('search()',c);
 assert.match(get('results').textContent,/Luca黒蜜糖/);assert.match(get('results').textContent,/YouTube \/ Twitch/);
 get('query').value='マほ姉';vm.runInContext('search()',c);assert.match(get('results').textContent,/IRIAM \/ REALITY/);
 get('query').value='あいうえ おばけ';vm.runInContext('search()',c);assert.match(get('results').textContent,/確認できた媒体 Avvy/);
 get('query').value='兎田ぺこら';vm.runInContext('search()',c);assert.match(get('results').textContent,/うさだぺこら/);
 get('query').value='枯葉 楓';vm.runInContext('search()',c);assert.match(get('results').textContent,/こば かえで/);assert.match(get('results').textContent,/主な活動媒体 IRIAM/);assert.match(get('results').textContent,/Vライバー/);
 get('query').value='日暮園';vm.runInContext('search()',c);assert.match(get('results').textContent,/主な活動媒体 REALITY/);
 get('query').value='しずく';vm.runInContext('search()',c);
 const matches=vm.runInContext('find("しずく")',c);
 const ai=matches.filter(x=>x.r.source_id==='youtube:UCE2SWbhR2WRHPBi-bflr0-g');
 assert.equal(ai.length,1);assert.equal(ai[0].r.category,'AIVTuber');
 assert.ok(!matches.some(x=>x.r.source_id==='aivnav:char-Ta5Ze-v2qnru'));
 const aiLinks=c.window.VNamePlatforms.details(ai[0].r).accounts;
 assert.equal(aiLinks.length,1);assert.match(aiLinks[0].url,/UCE2SWbhR2WRHPBi-bflr0-g$/);
 // Legacy-directory cleanup may legitimately remove unrelated same-name rows.
 // What must never happen is leaking this AIV identity's account onto another identity.
 for(const match of matches.filter(x=>x.r.source_id!==ai[0].r.source_id)){
  assert.ok(!c.window.VNamePlatforms.details(match.r).accounts.some(a=>a.url===aiLinks[0].url));
 }
 get('query').value='キズナアイ';vm.runInContext('search()',c);
 const kizuna=get('results').children[0];const links=kizuna.children.find(e=>e.className==='platform-links');
 const kizunaLabels=links.children.map(e=>e.textContent);assert.ok(kizunaLabels.includes('YouTube'));
 for(const q of ['キズナアイ','兎田ぺこら','星街すいせい','宝鐘マリン','葛葉','戌神ころね'])assert.ok(vm.runInContext('find('+JSON.stringify(q)+').some(x=>x.type===0)',c),q);
 get('query').value='';get('search-tag').value='AIVTuber';get('search-tag').onchange();
 assert.ok(vm.runInContext('hits.length>100 && hits.every(x=>categoryOf(x.r)==="AIVTuber")',c));assert.equal(get('results').children.length,30);assert.equal(get('pages').hidden,false);
 get('query').value='しずく';vm.runInContext('search()',c);assert.ok(vm.runInContext('hits.some(x=>x.r.source_id==="youtube:UCE2SWbhR2WRHPBi-bflr0-g") && hits.every(x=>x.r.category==="AIVTuber")',c));
 get('search-tag').value='VTuber';get('search-tag').onchange();assert.ok(vm.runInContext('!hits.some(x=>x.r.source_id==="youtube:UCE2SWbhR2WRHPBi-bflr0-g")',c));
 // Global collision searches must not inherit a UI tag filter.
 assert.ok(vm.runInContext('find("しずく").some(x=>x.r.source_id==="youtube:UCE2SWbhR2WRHPBi-bflr0-g")',c));
 get('query').value='';get('search-tag').value='Vライバー';get('search-tag').onchange();assert.ok(vm.runInContext('hits.length>100 && hits.every(x=>categoryOf(x.r)==="Vライバー")',c));
 const walk=e=>[e,...e.children.flatMap(walk)];
 get('query').value='';get('search-tag').value='all';get('search-platform').value='all';vm.runInContext('search()',c);
 assert.ok(vm.runInContext('hits.length>10000',c));assert.equal(get('results').children.length,30);
 assert.ok(vm.runInContext('sortOrder==="random" && hits.every(x=>randomOrder.has(x.r.source_id))',c));
 assert.ok(!walk(get('results')).some(e=>e.className==='audience'));
 assert.doesNotMatch(get('results').textContent,/YouTube登録者|Twitchフォロワー|登録者・フォロワー数の出典/);
 assert.ok(!walk(get('results')).some(e=>e.tagName==='img'));
 get('search-tag').value='AIVTuber';get('search-platform').value='youtube';vm.runInContext('search()',c);
 assert.ok(vm.runInContext('hits.length>100 && hits.every(x=>x.r.category==="AIVTuber" && x.r.media.known.includes("YouTube"))',c));
 vm.runInContext('sortOrder="name";search()',c);assert.ok(vm.runInContext('hits.every((x,i)=>i===0||compareNames(hits[i-1],x)<=0)',c));
 vm.runInContext('sortOrder="random";shuffle();search()',c);
 const order=vm.runInContext('hits.map(x=>x.r.source_id).join(",")',c);get('next').onclick();get('prev').onclick();assert.equal(vm.runInContext('hits.map(x=>x.r.source_id).join(",")',c),order);
 get('reshuffle').onclick();assert.notEqual(vm.runInContext('hits.map(x=>x.r.source_id).join(",")',c),order);
 get('search-tag').value='all';get('search-platform').value='all';get('query').value='宙依ラビ';vm.runInContext('search()',c);
 assert.ok(walk(get('results')).some(e=>e.href==='https://ravi96.com/'));
 assert.ok(!walk(get('results')).some(e=>/kedamasuzume\/status/.test(e.href||'')));
 get('query').value='存在しない名前XYZ123';vm.runInContext('search()',c);assert.match(get('results').textContent,/見つかりません/);

 for(const name of ['九重いのり','羽姫しおり','桃栗にに','コグレアキ','ふつうのアサリガール','もちりにゃんこ','木乃伊めんま','くれないべあ','椿季ゆず']){
  assert.ok(vm.runInContext('find('+JSON.stringify(name)+').some(x=>x.r.display_name==='+JSON.stringify(name)+')',c),name);
 }
 for(const [oldName,currentName] of [['木乃伊綿巻','木乃伊めんま'],['昏內べあ','くれないべあ'],['椿ユズ','椿季ゆず']])assert.ok(vm.runInContext('find('+JSON.stringify(oldName)+').some(x=>x.r.display_name==='+JSON.stringify(currentName)+')',c),oldName);
 assert.equal(p.account('https://s.avvy.live/u/01jqw901crpbxrmmapm20a84qa?lang=ja').platform,'avvy');

});
test('major-service profile links survive rendering with identity query parameters',()=>{
 for(const [platform,url] of [
  ['mirrativ','https://mirrativ.page.link/?link=https%3A%2F%2Fwww.mirrativ.com%2Fuser%2F151711048'],
  ['topia','https://topia.tv/p/uM7HG'],['palmu','https://app.palmu.jp/users/a7413a8b12624c308fa8'],
  ['whowatch','https://whowatch.tv/profile/w%3Abokukun2323'],
  ['colorsing','https://web.colorsing.com/share/user?user_id=729e55d8-4775-4560-b549-ffa3d9dbd881&utm_source=test'],
  ['pikapika','https://pikapika.live/index/roomuser/uid/4101478625323'],
  ['pococha','https://www.pococha.com/app/users/1e273cf1-4810-4f8d-afe8-7154d4e5d3be'],
  ['standfm','https://stand.fm/channels/61225fd77de6f0a0e0827095'],
  ['radiotalk','https://radiotalk.jp/program/65414'],['openrec','https://www.openrec.tv/m/user/raiju68'],
  ['chzzk','https://chzzk.naver.com/'+'a'.repeat(32)],['rplay','https://rplay.live/c/mahina']
 ]) {
  const d=detail({platform_accounts:[{url}]});assert.equal(d.accounts[0]?.platform,platform,url);
  assert.deepEqual(d.primary,[]);assert.equal(p.account(d.accounts[0].url)?.platform,platform);
  if(platform==='colorsing')assert.match(d.accounts[0].url,/user_id=729e55d8/);
 }
 assert.equal(p.account('https://mirrativ.page.link/?link=https://evil.example/user/151711048'),null);
 assert.equal(p.account('https://web.colorsing.com/share/user?user_id=bad'),null);
});
