'use strict';
const key=s=>String(s||'').normalize('NFKC').toLowerCase().replace(/[ァ-ヶ]/g,c=>String.fromCharCode(c.charCodeAt(0)-96)).replace(/[^\p{L}\p{N}]/gu,'');
let records=[],hits=[],page=0,sortOrder='random',randomOrder=new Map();
const PAGE_SIZE=30;
const categoryOf=r=>r.category==='AIVTuber'?'AIVTuber':r.category==='Vライバー'||/^https:\/\//.test(r.vliver_source||'')?'Vライバー':'VTuber';
const $=id=>document.getElementById(id);
const sourceLink=url=>/^https:\/\//.test(url||'')&&!/^https:\/\/(?:x|twitter)\.com\/kedamasuzume\/status\//i.test(url);
const corrections=new Map(Object.entries(window.VTUBER_READINGS||{}).map(([name,value])=>[key(name),value]));
function mergeData(base,extra){const map=new Map(base.map(r=>[r.source_id,{...r}]));for(const r of extra||[]){const old=map.get(r.source_id);map.set(r.source_id,old?{...old,...r,aliases:[...new Set([...(old.aliases||[]),...(r.aliases||[])])],platform_accounts:[...(old.platform_accounts||[]),...(r.platform_accounts||[])],platform_sources:{...(old.platform_sources||{}),...(r.platform_sources||{})}}:r)}return [...map.values()]}
const preparingName=name=>/(?:[a-z]*v(?:irtual)?[\s-]*tuber\s*準備中|準備中\s*(?:個人勢)?\s*[a-z]*vtuber|(?<!再)デビュー準備中|(?<!再)デビュー前|(?:Vライバー|IRIAM|Avvy|REALITY)\s*準備中|準備中\s*Vライバー|未デビュー|\bpre[\s-]?debut\b)/i.test(name||'');
function resolveReading(r){
 const verified=r.reading_source&&['manual','official','profile_explicit','directory_explicit'].includes(r.reading_source_kind);
 if(verified&&r.reading)return {reading:r.reading,reading_inferred:false};
 const kana=value=>{const s=String(value||'').normalize('NFKC').replace(/[ァ-ヶ]/g,c=>String.fromCharCode(c.charCodeAt(0)-96)).replace(/[\s・･]/g,'');return /^[ぁ-ゖー]+$/.test(s)?s:'';};
 const estimate=(window.VTUBER_ESTIMATED_READINGS||{})[r.source_id];
 const spelled=String(r.display_name||'').normalize('NFKC').replace(/[ァ-ヶ]/g,c=>String.fromCharCode(c.charCodeAt(0)-96)),end=spelled.match(/[ぁ-ゖー]+$/)?.[0],start=spelled.match(/^[ぁ-ゖー]+/)?.[0],guess=kana(estimate?.reading);
 if(estimate?.display_name===r.display_name&&estimate.model==='gemma-4-E2B-it'&&estimate.kind==='inferred'&&guess&&(!end||guess.endsWith(end))&&(!start||guess.startsWith(start)))return {reading:guess,reading_inferred:true};
 const direct=kana(r.display_name);
 // Only use complete kana candidates for Japanese names, never partial transliterations.
 const japanese=/^[\p{Script=Han}ぁ-ゖァ-ヶー\s・･]+$/u.test(String(r.display_name||'').normalize('NFKC'));
 const candidate=direct||(japanese?kana(r.reading):'');
 return {reading:candidate,reading_inferred:!!candidate};
}
function load(data){
 const primary=new Map((window.VTUBER_PRIMARY||[]).map(r=>[r.source_id,r]));
 data=data.map(r=>primary.has(r.source_id)?{...r,...primary.get(r.source_id)}:r);
 // Platform-only/licensed metadata rows can exist without a display name. They
 // are useful as overlays but are not independently searchable identities.
 records=data.filter(r=>r.display_name&&r.listing_status!=='predebut'&&!preparingName(r.display_name)).map(original=>{
  const hasOwnReading=original.reading&&original.reading_source&&['manual','official','profile_explicit'].includes(original.reading_source_kind);
  const correction=hasOwnReading?undefined:corrections.get(key(original.display_name)),r={...original,...correction,corrected:!!correction};
  Object.assign(r,resolveReading(r));
  r.romanized_name=r.romanized_source?r.romanized_name:'';
  const media=window.VNamePlatforms.details(r);
  return {...r,media,keys:[r.display_name,r.reading,r.romanized_name,r.channel_title,r.youtube_handle,...(r.aliases||[])].map(key)};
 });
 $('count').textContent=`収録 ${records.length.toLocaleString()} 件`;
 buildPlatformFilters();
 if(sortOrder==='random')for(const r of records)if(!randomOrder.has(r.source_id))randomOrder.set(r.source_id,Math.random());
}
function find(q){const k=key(q);if(!k)return [];return records.map(r=>{const type=r.keys[0]===k?0:r.keys.slice(1).includes(k)?1:r.keys.some(v=>v&&v.includes(k))?2:9;return{r,type};}).filter(x=>x.type<9).sort((a,b)=>a.type-b.type||compareNames(a,b));}
function compareNames(a,b){return (a.r.reading||a.r.display_name).localeCompare(b.r.reading||b.r.display_name,'ja')||a.r.display_name.localeCompare(b.r.display_name,'ja')||a.r.source_id.localeCompare(b.r.source_id);}
function shuffle(){randomOrder=new Map(records.map(r=>[r.source_id,Math.random()]));}
function sortHits(){
 if(sortOrder==='random'&&!randomOrder.size)shuffle();
 hits.sort((a,b)=>{
  // An exact match stays first when checking a name; sorting applies within match groups.
  if(key($('query').value)&&a.type!==b.type)return a.type-b.type;
  if(sortOrder==='random')return randomOrder.get(a.r.source_id)-randomOrder.get(b.r.source_id);
  return compareNames(a,b);
 });
}
function element(tag,className,text){const e=document.createElement(tag);if(className)e.className=className;if(text!==undefined)e.textContent=text;return e;}
function link(label,url,className){const e=element('a',className,label);e.href=url;e.target='_blank';e.rel='noopener noreferrer';return e;}
function fieldsFor(r){
 const media=r.media,fields=element('dl','fields');
 const rows=[['主な活動媒体',media.primary.join(' / ')],...(!media.primary.length?[['確認できた媒体',media.known.join(' / ')]]:[]),[r.reading_inferred?'読み（推定）':'読み',r.reading],...(r.romanized_name?[['英字',r.romanized_name]]:[]),...(r.aliases?.length?[['別名',r.aliases.join(' / ')]]:[])];
 for(const [label,value] of rows){const dd=element('dd','',value||'不明');if(!value)dd.setAttribute('data-i18n','');fields.append(element('dt','',label),dd);}
 return fields;
}
function renderCard({r,type}){
 const article=element('article','result'),top=element('div','card-tags');
 top.append(element('span','category'+(r.category==='AIVTuber'?' ai':''),categoryOf(r)));
 if(r.registration_status==='ai_screened')top.append(element('span','badge','利用者登録・AI確認'));
 if(type<3)top.append(element('span','badge'+(type===0?' exact':''),['表示名が一致','読み・英字が一致','名前の一部が一致'][type]));
 const name=element('h3','name',r.display_name),reading=element('p','card-reading',r.reading||'読み未確認');
 if(r.reading_inferred)reading.append(element('span','reading-estimate',' （推定）'));
 const media=r.media,platformLinks=element('div','platform-links');
 for(const group of media.groups){
  platformLinks.append(link(group.label,group.accounts[0].url,'platform-link'));
  if(group.accounts.length>1){const more=element('details','platform-more');more.append(element('summary','','その他のアカウント'));for(const account of group.accounts.slice(1)){const a=link(decodeURIComponent(new URL(account.url).pathname).replace(/^\//,''),account.url);a.setAttribute('data-generated','');more.append(a);}platformLinks.append(more);}
 }
 try{const official=new URL(r.official_website);if(['https:','http:'].includes(official.protocol)&&!official.username&&!official.password)platformLinks.append(link('公式サイト',official.href,'platform-link'));}catch{}
 const details=element('details','record-details');details.append(element('summary','','詳細・出典'),fieldsFor(r));
 if(r.registration_status==='ai_screened')details.append(element('p','muted','Gemma 4 E2Bが登録内容を確認しました。本人確認や情報の正しさを保証するものではありません。'));
 const note=element('div','note');
 const sources=[...(r.platform_accounts||[]).filter(a=>a.platform==='x'&&/^https:\/\/(?:x|twitter)\.com\/[A-Za-z0-9_]{1,15}$/.test(a.url||'')).map(a=>['本人のX',a.url]),...(r.name_source?[['名前の確認元',r.name_source]]:[]),...(r.reading&&!r.reading_inferred?[['読みの出典',r.reading_source]]:[]),['掲載元',r.activity_source||r.source_url||(r.source_id.startsWith('youtube:')?'https://vtuber-post.com/database_detail.html?id='+r.source_id.slice(8):'https://vdb.vtbs.moe/')],['活動媒体の出典',media.primarySource]];
 for(const [label,url] of sources)if(sourceLink(url))note.append(link(label,url));
 details.append(note);article.append(top,name,reading);
 if(r.channel_title){
  const channel=element('div','card-channel');channel.append(element('span','card-channel-label','YouTubeチャンネル'));
  const account=window.VNamePlatforms?.account(r.youtube_url);
  channel.append(account?link(r.channel_title,account.url,'card-channel-name'):element('span','card-channel-name',r.channel_title));
  const identifier=r.youtube_handle||r.youtube_channel_id;
  if(identifier)channel.append(element('span','card-channel-handle',identifier));
  article.append(channel);
 }
 article.append(platformLinks,details);return article;
}
function render(){
 const box=$('results');box.replaceChildren();
 for(const hit of hits.slice(page*PAGE_SIZE,(page+1)*PAGE_SIZE))box.append(renderCard(hit));
 if(!hits.length){const empty=element('div','empty');empty.append(element('strong','','条件に一致する活動者が見つかりませんでした。'),element('p','','名前やタグ・配信媒体を変えてお試しください。'));box.append(empty);}
 $('pages').hidden=hits.length<=PAGE_SIZE;$('page').textContent=`${page+1} / ${Math.max(1,Math.ceil(hits.length/PAGE_SIZE))}`;
 $('prev').disabled=page===0;$('next').disabled=(page+1)*PAGE_SIZE>=hits.length;
 $('reshuffle').hidden=sortOrder!=='random';
 translateUI();
}
function syncFilters(){
 for(const [attr,id] of [['tag','search-tag'],['platform','search-platform']])document.querySelectorAll('[data-'+attr+']').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset[attr]===($(id).value||'all'))));
 document.querySelectorAll('[data-sort]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.sort===sortOrder)));
}
function search(){
 const q=$('query').value,tag=$('search-tag').value||'all',platform=$('search-platform').value||'all';
 const platformName=window.VNamePlatforms.labels[platform];
 hits=(key(q)?find(q):records.map(r=>({r,type:3}))).filter(x=>(tag==='all'||categoryOf(x.r)===tag)&&(platform==='all'||x.r.media.known.includes(platformName)));
 sortHits();page=0;const exact=hits.filter(x=>x.type===0).length;
 $('results-heading').textContent=key(q)?'検索結果':'活動者一覧';$('clear-search').hidden=!q;
 $('status').dataset.state=exact?'exact':hits.length?'candidates':'none';
 $('status').textContent=key(q)?(exact?`同じ表示名が ${exact} 件あります。下の結果を確認してください。`:hits.length?`読み・英字、または名前の一部が一致する候補が ${hits.length.toLocaleString()} 件あります。`:'この条件では一致する名前が見つかりませんでした。未使用を保証する結果ではありません。'):`${hits.length.toLocaleString()} 件の活動者を表示`;
 syncFilters();render();
}
function buildPlatformFilters(){
 const box=$('platform-filters');box.replaceChildren();const known=new Set(records.flatMap(r=>r.media.known));
 const labels=window.VNamePlatforms.labels,order=['youtube','twitch','tiktok','iriam','reality','avvy',...Object.keys(labels)];
 for(const id of ['all',...new Set(order.filter(id=>known.has(labels[id])))] ){
  const button=element('button','',id==='all'?'すべて':labels[id]);button.type='button';button.dataset.platform=id;button.setAttribute('aria-pressed',String(id==='all'));button.onclick=()=>{$('search-platform').value=id;search();};box.append(button);
 }
}
$('search-tag').onchange=search;$('search-platform').onchange=search;
document.querySelectorAll('[data-tag]').forEach(b=>b.onclick=()=>{$('search-tag').value=b.dataset.tag;search();});
document.querySelectorAll('[data-sort]').forEach(b=>b.onclick=()=>{sortOrder=b.dataset.sort;if(sortOrder==='random')shuffle();search();});
$('reshuffle').onclick=()=>{shuffle();search();};$('clear-search').onclick=()=>{$('query').value='';search();$('query').focus();};
$('form').addEventListener('submit',e=>{e.preventDefault();search();});
function turnPage(delta){page=Math.max(0,Math.min(Math.ceil(hits.length/PAGE_SIZE)-1,page+delta));render();$('results-heading').scrollIntoView?.({block:'start'});$('results-heading').focus?.({preventScroll:true});}
$('prev').onclick=()=>turnPage(-1);$('next').onclick=()=>turnPage(1);
try{load(mergeData(mergeData(window.VTUBER_DATA,window.VTUBER_EXTRA),window.VTUBER_PLATFORMS));search();}catch(e){$('status').textContent='辞書を読み込めませんでした。ページを再読み込みしてください。';}
window.VNameAddCommunity=incoming=>{
 const ids=new Set(records.map(r=>r.source_id)),accounts=new Set(records.flatMap(r=>r.media.accounts.map(a=>a.url)));
 const additions=incoming.filter(r=>!ids.has(r.source_id)&&!r.platform_accounts.some(a=>accounts.has(a.url)));
 if(!additions.length)return;
 const previousPage=page;
 for(const row of additions)if(!randomOrder.has(row.source_id))randomOrder.set(row.source_id,Math.random());
 load([...records,...additions]);search();page=Math.min(previousPage,Math.max(0,Math.ceil(hits.length/PAGE_SIZE)-1));render();
};
$('language').onchange=e=>setLanguage(e.target.value);translateUI();