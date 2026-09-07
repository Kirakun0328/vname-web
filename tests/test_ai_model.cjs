const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function setup(options={}){
 const stores=new Map([['another-app',new Map()],['vname-ai-model-old',new Map()]]);let downloads=0,writes=0;
 const storage={
  async keys(){return [...stores.keys()];},async delete(key){return stores.delete(key);},
  async open(key){
   if(options.unavailable)throw new Error('Not supported');
   if(!stores.has(key))stores.set(key,new Map());const entries=stores.get(key);
   return{
    async match(url){const headers=entries.get(url);return headers?new Response(new Uint8Array(1),{headers}):undefined;},
    async put(url,response){
     writes++;for await(const chunk of response.body){} // Drain before committing, like CacheStorage.
     if(options.failWrite)throw new DOMException('Full','QuotaExceededError');
     entries.set(url,Object.fromEntries(response.headers));
    },
    async delete(url){return entries.delete(url);}
   };
  }
 };
 const c={window:{caches:storage},caches:storage,navigator:{storage:{estimate:async()=>({quota:options.lowSpace?100:20e9,usage:0})}},DOMException,Response,ReadableStream,TransformStream,
  fetch:async(url,{signal})=>{downloads++;return new Response(new ReadableStream({start(controller){if(options.abort)options.abort.abort();controller.enqueue({byteLength:options.incomplete?4:2008432640});controller.close();}}));}
 };
 vm.createContext(c);vm.runInContext(fs.readFileSync('ai-model.js','utf8'),c);
 return{model:c.window.VNameModel,stores,counts:()=>({downloads,writes})};
}
test('status never downloads, cached starts reuse one model, and deletion only affects this app',async()=>{
 const h=setup();assert.equal((await h.model.status()).saved,false);assert.equal(h.counts().downloads,0);
 await h.model.obtain();assert.equal((await h.model.status()).saved,true);assert.equal(h.counts().downloads,1);
 await h.model.obtain();await h.model.obtain({save:false});assert.equal(h.counts().downloads,1);assert.equal(h.counts().writes,1);
 assert.equal([...h.stores.keys()].filter(k=>k.startsWith('vname-ai-model-')).length,1);
 await h.model.remove();assert.deepEqual([...h.stores.keys()],['another-app']);assert.equal((await h.model.status()).bytes,0);
});
test('insufficient storage is detected before any model download',async()=>{
 const h=setup({lowSpace:true});await assert.rejects(h.model.obtain(),/CACHE_SPACE/);assert.equal(h.counts().downloads,0);
});
test('incomplete or failed writes never appear as a saved model and do not silently download again',async()=>{
 for(const options of [{incomplete:true},{failWrite:true}]){const h=setup(options);await assert.rejects(h.model.obtain(),/CACHE_/);assert.equal((await h.model.status()).saved,false);assert.equal(h.counts().downloads,1);}
});
test('cancellation cannot leave a partial cached model',async()=>{
 const abort=new AbortController(),h=setup({abort});await assert.rejects(h.model.obtain({signal:abort.signal}),error=>error.name==='AbortError');assert.equal((await h.model.status()).saved,false);
});
test('one-session mode remains available when persistent storage is unavailable',async()=>{
 const h=setup({unavailable:true});assert.equal((await h.model.status()).supported,false);
 const stream=await h.model.obtain({save:false});for await(const chunk of stream){}
 assert.equal(h.counts().downloads,1);assert.equal(h.counts().writes,0);
});
