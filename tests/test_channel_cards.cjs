const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const path=require('path');
const read=f=>fs.readFileSync(path.join(__dirname,'..',f),'utf8');
class Node{constructor(tag){this.tag=tag;this.children=[];this.textContent='';}append(...xs){this.children.push(...xs)}setAttribute(){} }
const c={URL,window:{VTUBER_DATA:[],VTUBER_EXTRA:[],VTUBER_PLATFORMS:[],VTUBER_PRIMARY:[]},document:{createElement:t=>new Node(t),getElementById:()=>new Node('div')}};vm.createContext(c);
vm.runInContext(read('platforms.js'),c);vm.runInContext(read('aiv-submissions-20260911.js'),c);
vm.runInContext(read('app.js').split('function render(){')[0]+';function buildPlatformFilters(){};load(window.VTUBER_EXTRA);window.rows=records;window.card=renderCard;window.key=key;',c);
const zs=JSON.parse(read('scripts/zundamon-channels-20260911.json')).entries;
const all=n=>[n,...n.children.flatMap(all)];
for(const z of zs){const r=c.window.rows.find(r=>r.youtube_channel_id===z.channel_id);assert(r);assert(r.keys.includes(c.window.key(z.channel_title)));if(z.handle)assert(r.keys.includes(c.window.key('@'+z.handle)));const card=c.window.card({r,type:0});const nodes=all(card);assert(nodes.some(n=>n.className==='card-channel-name'&&n.textContent===z.channel_title&&n.href==='https://www.youtube.com/channel/'+z.channel_id));assert(nodes.some(n=>n.className==='card-channel-handle'&&n.textContent===(z.handle?'@'+z.handle:z.channel_id)));}
console.log('PASS: 13 channel titles, identifiers, safe links and search keys');
