'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const context={window:{},URL,document:{getElementById:()=>({})}};vm.createContext(context);
const read=f=>fs.readFileSync(path.join(root,f),'utf8');
for(const f of ['data.js','extra-data.js','readings.js','estimated-readings.js','platforms.js','platform-data.js','primary-data.js','creator-submissions-20260910.js'])vm.runInContext(read(f),context);
const layerNames=['VTUBER_DATA','VTUBER_EXTRA','VTUBER_PLATFORMS','VTUBER_PRIMARY'];
const report=JSON.parse(read('scripts/aiv-submissions-review-20260911.json'));
const touched=new Set([...report.records.map(r=>r.id),...report.superseded_ids]);
const unchanged=new Map(layerNames.map(n=>[n,JSON.stringify(context.window[n].filter(r=>!touched.has(r.source_id)))]));
vm.runInContext(read('aiv-submissions-20260911.js'),context);
for(const n of layerNames)assert.equal(JSON.stringify(context.window[n].filter(r=>!touched.has(r.source_id))),unchanged.get(n),n+' unrelated records preserved');
vm.runInContext(read('app.js').split('function find(q)')[0]+'\nfunction buildPlatformFilters(){};load(mergeData(mergeData(window.VTUBER_DATA,window.VTUBER_EXTRA),window.VTUBER_PLATFORMS));window.checked=records;window.key=key;',context);
const records=context.window.checked,byId=new Map(records.map(r=>[r.source_id,r]));
assert.equal(byId.size,records.length,'No duplicate source IDs');
for(const entry of report.records){
 const row=byId.get(entry.id);assert(row,entry.name+' is visible');assert.equal(row.category,'AIVTuber');assert.equal(row.reading_inferred,false,entry.name+' manual reading');assert(row.keys.includes(context.window.key(entry.name)),entry.name+' searchable');
 const expected=context.window.VTUBER_EXTRA.find(r=>r.source_id===entry.id)||context.window.VTUBER_DATA.find(r=>r.source_id===entry.id);assert.equal(row.reading,expected.reading,entry.name+' latest reading');
}
function rowsNamed(name){return records.filter(r=>r.display_name===name);}
assert.equal(rowsNamed('音成みらね')[0].reading,'ねなりみらね');assert.equal(rowsNamed('Stella Voyd')[0].reading,'すてらゔぉいど');
for(const group of [['夢飴めあ','夢影とあ'],['アイリス・ロゼッティ','フィオナ・ロゼッティ'],['リリカ','ルゼブル'],['スピカ','マキナ'],['アム','イム'],['真流賀レイテ','ハンナ・アクタヴィア'],['シロ','Lumi']]){
 const ids=group.map(n=>report.records.find(r=>r.name===n)?.id);assert(ids.every(Boolean));assert.equal(new Set(ids).size,ids.length,'Shared channel characters separated');
 for(const n of group){const row=byId.get(report.records.find(r=>r.name===n).id);for(const sibling of group.filter(x=>x!==n))assert(!row.aliases.includes(sibling),n+' does not alias '+sibling);}
}
for(const name of ['Yuna','Luna','カゲ','めぐ'])assert(new Set(report.records.filter(r=>r.name===name).map(r=>r.id)).size>1,name+' different accounts remain distinct');
assert.equal(records.find(r=>r.source_id==='youtube:UC6eWCld0KwmyHFbAqK3V-Rw').category,'VTuber','Human Koyori preserved');
const platforms=context.window.VNamePlatforms;
for(const u of ['https://www.youtube.com/@個人開発AIライちゃん','https://www.youtube.com/@GINGABANKOちゃんねる','https://www.youtube.com/@TAERUちゃん','https://www.youtube.com/@宙依ラビ','https://whowatch.tv/sp/profile/w:anicona'])assert(platforms.account(u),u+' valid');
for(const u of ['https://www.youtube.com/@name/extra','https://www.youtube.com/watch?v=123','https://whowatch.tv/sp/profile/w:anicona/extra','https://evil.example/@name','javascript:alert(1)'])assert.equal(platforms.account(u),null,u+' rejected as profile');
assert.equal(platforms.account('https://whowatch.tv/sp/profile/w:anicona').url,'https://whowatch.tv/profile/w:anicona');
assert.equal(report.input_rows,484);assert.equal(report.characters,490);assert.equal(context.window.VNameAIVSubmission.count,490);
const zundamon=JSON.parse(read('scripts/zundamon-channels-20260911.json')).entries;
const zids=[];
for(const channel of zundamon){
 const matches=records.filter(r=>r.display_name==='AIずんだもん'&&r.youtube_channel_id===channel.channel_id);
 assert.equal(matches.length,1,channel.channel_title+' has exactly one character');
 const row=matches[0];zids.push(row.source_id);
 assert(row.keys.includes(context.window.key('AIずんだもん')));
 for(const url of channel.urls)assert(row.source_profiles.includes(url),url+' retained');
}
assert.equal(new Set(zids).size,13,'Different Zundamon channels retain separate identities');
assert.equal(rowsNamed('すえ').length,0,'Channel label corrected to character name');
assert(rowsNamed('つむぎさん').some(r=>r.source_profiles.includes('https://www.youtube.com/channel/UCXMAPL3mzvSnUNOx7o2sEuw')),'Shared-channel Tsumugi retained');
const once=JSON.stringify(context.window.VTUBER_EXTRA);vm.runInContext(read('aiv-submissions-20260911.js'),context);assert.equal(JSON.stringify(context.window.VTUBER_EXTRA),once,'Overlay is idempotent');
console.log(JSON.stringify({characters:report.characters,added:report.added,updated:report.updated,listedAI:records.filter(r=>r.category==='AIVTuber').length,total:records.length,unrelatedPreserved:true}));
