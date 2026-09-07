'use strict';
window.VNameModel=(()=>{
  const revision='b3ca0d2f076785a8f4b2219ddbd2bdb99954eae1';
  const url='https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm/resolve/'+revision+'/gemma-4-E2B-it-web.litertlm';
  const bytes=2008432640, prefix='vname-ai-model-', cacheName=prefix+revision;
  const checkSignal=signal=>{if(signal?.aborted)throw new DOMException('Aborted','AbortError');};
  async function status(){
    try{
      if(!window.caches)return{supported:false,saved:false,bytes:0};
      const cache=await caches.open(cacheName), response=await cache.match(url);
      const saved=response?.headers.get('x-vname-model-bytes')===String(bytes);
      return{supported:true,saved:!!saved,bytes:saved?bytes:0};
    }catch{return{supported:false,saved:false,bytes:0};}
  }
  async function remove(){
    if(!window.caches)return;
    for(const key of await caches.keys())if(key.startsWith(prefix))await caches.delete(key);
  }
  async function obtain({signal,onProgress=()=>{},save=true}={}){
    const run=async()=>{
      checkSignal(signal);
      let cache;
      if(window.caches){
        try{
          cache=await caches.open(cacheName);
          const existing=await cache.match(url);
          if(existing?.headers.get('x-vname-model-bytes')===String(bytes)){
            checkSignal(signal);onProgress({phase:'cached',received:bytes,total:bytes});return existing.body;
          }
        }catch(error){if(signal?.aborted)throw error;if(save)throw new Error('CACHE_UNAVAILABLE');}
      }
      if(save){
        if(!window.caches)throw new Error('CACHE_UNAVAILABLE');
        for(const key of await caches.keys())if(key.startsWith(prefix)&&key!==cacheName)await caches.delete(key);
        const estimate=await navigator.storage?.estimate?.().catch(()=>null);
        if(estimate?.quota&&estimate.quota-(estimate.usage||0)<bytes+64*1024*1024)throw new Error('CACHE_SPACE');
      }
      checkSignal(signal);
      const response=await fetch(url,{signal,cache:'no-store'});
      if(!response.ok||!response.body)throw new Error('MODEL_DOWNLOAD');
      let received=0;
      const stream=response.body.pipeThrough(new TransformStream({
        transform(chunk,controller){checkSignal(signal);received+=chunk.byteLength;onProgress({phase:'download',received,total:bytes});controller.enqueue(chunk);},
        flush(){if(received!==bytes)throw new Error('MODEL_INCOMPLETE');}
      }));
      if(!save)return stream;
      // Consume directly into CacheStorage, then reopen. Do not clone/tee a 2 GB response into memory.
      try{await cache.put(url,new Response(stream,{headers:{'content-type':'application/octet-stream','x-vname-model-bytes':String(bytes)}}));}
      catch(error){await cache.delete(url);if(signal?.aborted)throw new DOMException('Aborted','AbortError');throw new Error(error.name==='QuotaExceededError'?'CACHE_SPACE':'CACHE_WRITE');}
      checkSignal(signal);
      const stored=await cache.match(url);if(!stored?.body)throw new Error('CACHE_WRITE');
      onProgress({phase:'saved',received:bytes,total:bytes});return stored.body;
    };
    // Coordinate concurrent tabs when Web Locks is available; only one cached model is retained.
    return save&&navigator.locks? navigator.locks.request(cacheName,{signal},run):run();
  }
  return{url,bytes,status,obtain,remove};
})();
