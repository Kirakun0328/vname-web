const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const c={window:{},URL,AbortSignal,document:{getElementById:()=>null}};vm.createContext(c);
for(const file of ['platforms.js','community.js'])vm.runInContext(fs.readFileSync(file,'utf8'),c);
const api=c.window.VNameCommunity;
const row={source_id:'community:'+'a'.repeat(64),display_name:'星空テスト',category:'VTuber',source_url:'https://www.youtube.com/@test',activity_source:'https://www.youtube.com/watch?v=abcdefghijk',registration_status:'ai_screened',review_model:'gemma-4-E2B-it'};
test('only screened additions pass through the public data adapter',()=>{
 assert.equal(api.clean({...row,registration_status:'pending'}),null);
 assert.equal(api.clean({...row,source_id:'youtube:anything'}),null);
 assert.equal(api.clean({...row,display_name:'<script>'}),null);
 assert.equal(api.clean({...row,source_url:'https://evil.example/creator'}),null);
 assert.equal(api.clean({...row,activity_source:'javascript:alert(1)'}),null);
 const cleaned=api.clean({...row,reading:'推測',aliases:['不正な別名'],audience_metrics:[{count:999999999}]});
 assert.equal(cleaned.reading,'');assert.equal(cleaned.aliases.length,0);assert.equal(cleaned.audience_metrics,undefined);
});
test('pagination loads all approved records and rejects failed or looping pages',async()=>{
 let calls=0;const fetcher=async()=>({ok:true,json:async()=>++calls===1?{records:[row],next:1000}:{records:[{...row,source_id:'community:'+'b'.repeat(64)}],next:null}});
 assert.equal((await api.loadAll('https://example.test',fetcher)).length,2);
 await assert.rejects(api.loadAll('https://example.test',async()=>({ok:false})));
 await assert.rejects(api.loadAll('https://example.test',async()=>({ok:true,json:async()=>({records:[],next:0})})));
});
