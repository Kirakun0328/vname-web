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
test('published data searches and renders a TikTok V-liver without requiring YouTube',()=>{
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
 for(const file of ['data.js','extra-data.js','readings.js','platform-data.js','platforms.js','app.js'])vm.runInContext(fs.readFileSync(file,'utf8'),c);
 get('query').value='ルーカ・アレイス';vm.runInContext('search()',c);
 assert.match(get('results').textContent,/ルーカ・アレイス/);assert.match(get('results').textContent,/主な活動媒体 TikTok LIVE/);
 get('query').value='マほ姉';vm.runInContext('search()',c);assert.match(get('results').textContent,/IRIAM \/ REALITY/);
 get('query').value='あいうえ おばけ';vm.runInContext('search()',c);assert.match(get('results').textContent,/確認できた媒体 Avvy/);
 get('query').value='兎田ぺこら';vm.runInContext('search()',c);assert.match(get('results').textContent,/うさだぺこら/);
 const avatar=get('results').children[0].children.find(e=>e.className==='result-heading').children[0];
 const profileImage=avatar.children.find(e=>e.tagName==='img');assert.ok(profileImage);assert.equal(profileImage.loading,'lazy');assert.equal(profileImage.referrerPolicy,'no-referrer');
 profileImage.events.load();assert.equal(avatar.children[0].hidden,true);profileImage.events.error();assert.equal(profileImage.hidden,true);assert.equal(avatar.children[0].hidden,false);
 get('query').value='枯葉 楓';vm.runInContext('search()',c);assert.match(get('results').textContent,/こば かえで/);assert.match(get('results').textContent,/主な活動媒体 IRIAM/);assert.match(get('results').textContent,/Vライバー/);
 get('query').value='日暮園';vm.runInContext('search()',c);assert.match(get('results').textContent,/主な活動媒体 REALITY/);
 get('query').value='しずく';vm.runInContext('search()',c);
 const matches=vm.runInContext('find("しずく")',c);
 const ai=matches.filter(x=>x.r.source_id==='youtube:UCE2SWbhR2WRHPBi-bflr0-g');
 assert.equal(ai.length,1);assert.equal(ai[0].r.category,'AIVTuber');
 assert.ok(!matches.some(x=>x.r.source_id==='aivnav:char-Ta5Ze-v2qnru'));
 const aiLinks=c.window.VNamePlatforms.details(ai[0].r).accounts;
 assert.equal(aiLinks.length,1);assert.match(aiLinks[0].url,/UCE2SWbhR2WRHPBi-bflr0-g$/);
 const other=matches.find(x=>x.r.source_id==='youtube:UCAHQGIKolfBfoeXXMY79SBA');
 assert.ok(other);assert.notEqual(other.r.category,'AIVTuber');
 assert.ok(!c.window.VNamePlatforms.details(other.r).accounts.some(a=>a.url===aiLinks[0].url));
 get('query').value='キズナアイ';vm.runInContext('search()',c);
 const kizuna=get('results').children[0];const links=kizuna.children.find(e=>e.className==='platform-links');
 assert.deepEqual(links.children.map(e=>e.textContent),['YouTube','bilibili']);
 for(const q of ['キズナアイ','兎田ぺこら','星街すいせい','宝鐘マリン','葛葉','戌神ころね'])assert.ok(vm.runInContext('find('+JSON.stringify(q)+').some(x=>x.type===0)',c),q);
 get('query').value='';get('search-tag').value='AIVTuber';get('search-tag').onchange();
 assert.ok(vm.runInContext('hits.length>100 && hits.every(x=>categoryOf(x.r)==="AIVTuber")',c));assert.equal(get('results').children.length,30);assert.equal(get('pages').hidden,false);
 get('query').value='しずく';vm.runInContext('search()',c);assert.ok(vm.runInContext('hits.some(x=>x.r.source_id==="youtube:UCE2SWbhR2WRHPBi-bflr0-g") && hits.every(x=>x.r.category==="AIVTuber")',c));
 get('search-tag').value='VTuber';get('search-tag').onchange();assert.ok(vm.runInContext('!hits.some(x=>x.r.source_id==="youtube:UCE2SWbhR2WRHPBi-bflr0-g")',c));
 // Global collision searches must not inherit a UI tag filter.
 assert.ok(vm.runInContext('find("しずく").some(x=>x.r.source_id==="youtube:UCE2SWbhR2WRHPBi-bflr0-g")',c));
 get('query').value='';get('search-tag').value='Vライバー';get('search-tag').onchange();assert.ok(vm.runInContext('hits.length>900 && hits.every(x=>categoryOf(x.r)==="Vライバー")',c));
});

test('profile icons require a credited HTTPS image on an explicit host',()=>{
 assert.equal(p.icon({icon_url:'https://yt3.ggpht.com/avatar'}),null);
 assert.equal(p.icon({icon_url:'https://yt3.ggpht.com.evil.test/avatar',icon_source:'https://youtube.com/@test'}),null);
 assert.equal(p.icon({icon_url:'data:image/png;base64,test',icon_source:'https://youtube.com/@test'}),null);
 assert.equal(p.icon({icon_url:'https://yt3.ggpht.com/avatar',icon_source:'https://youtube.com/@test'}).url,'https://yt3.ggpht.com/avatar');
});
