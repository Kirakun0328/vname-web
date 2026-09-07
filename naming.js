'use strict';
(() => {
  const insight=window.VNameInsights;
  const SDK='https://cdn.jsdelivr.net/npm/@litert-lm/core@0.17.0/+esm';
  const MODEL='https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm/resolve/main/gemma-4-E2B-it-web.litertlm';
  let engine=null, conversation=null, loading=false, unloading=false, busy=false, cancelled=false, generation=0, aborter=null;
  let activeLoad=null, activeSend=null;
  let conversationLanguage=null;
  let mediaIndex=null, stats=null, lastChecks=[];
  const tabs=[...document.querySelectorAll('[data-tab]')];
  const el=(tag,textValue,className)=>{const e=document.createElement(tag);if(textValue!==undefined)e.textContent=textValue;if(className)e.className=className;return e;};
  function setStatus(value,error=false){$('ai-status').textContent=value;$('ai-status').dataset.error=String(error);translateUI();}
  function controls(){
    $('ai-start').hidden=!!engine;$('ai-start').disabled=loading||unloading;
    $('ai-unload').hidden=!engine&&!loading&&!unloading;$('ai-unload').disabled=unloading;
    $('ai-send').disabled=!engine||busy||loading||unloading;
    $('ai-stop').hidden=!busy;
    $('ai-reset').disabled=busy||loading||unloading;
  }
  function selectTab(name,updateHash=true){
    if(!['search','consult','trends'].includes(name))name='search';
    for(const b of tabs){const active=b.dataset.tab===name;b.setAttribute('aria-selected',String(active));b.tabIndex=active?0:-1;}
    for(const panel of ['search','consult','trends'])$('panel-'+panel).hidden=panel!==name;
    if(updateHash)history.replaceState(null,'','#'+name);
    if(name==='trends')renderTrends();
  }
  tabs.forEach((button,i)=>{
    button.onclick=()=>selectTab(button.dataset.tab);
    button.onkeydown=event=>{
      let next;if(event.key==='ArrowRight')next=(i+1)%tabs.length;else if(event.key==='ArrowLeft')next=(i+tabs.length-1)%tabs.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=tabs.length-1;else return;
      event.preventDefault();tabs[next].focus();selectTab(tabs[next].dataset.tab);
    };
  });
  window.addEventListener('hashchange',()=>selectTab(location.hash.slice(1),false));
  function openSearch(name){selectTab('search');$('query').value=name;search();$('query').focus();}
  function prepareMedia(){
    if(mediaIndex)return;
    mediaIndex=new Map();
    for(const r of records){
      const d=window.VNamePlatforms.details(r);
      for(const [id,label] of Object.entries(window.VNamePlatforms.labels))if(d.known.includes(label)){
        if(!mediaIndex.has(id))mediaIndex.set(id,[]);mediaIndex.get(id).push(r);
      }
    }
    for(const [id,label] of Object.entries(window.VNamePlatforms.labels))if(mediaIndex.has(id)){
      const option=el('option',label);option.value=id;$('trend-platform').append(option);
    }
  }
  function selectedRows(){prepareMedia();return $('trend-platform').value==='all'?records:(mediaIndex.get($('trend-platform').value)||[]);}
  function currentStats(){const rows=selectedRows();return {...insight.analyze(rows),platform:window.VNamePlatforms.labels[$('trend-platform').value]||'all'};}
  function bars(title,rows,total){
    const box=el('section',undefined,'insight-card');box.append(el('h3',title));
    for(const r of rows){
      const row=el('div',undefined,'insight-row'),track=el('div',undefined,'track'),bar=el('div',undefined,'bar');
      bar.style.width=(total?r.count/total*100:0)+'%';track.setAttribute('aria-hidden','true');track.append(bar);
      row.append(el('span',r.label),track,el('span',r.count.toLocaleString(), 'numeric'));box.append(row);
    }
    return box;
  }
  function ranking(title,rows){
    const box=el('section',undefined,'insight-card');box.append(el('h3',title));
    const table=el('table'),head=el('thead'),header=el('tr'),body=el('tbody');header.append(el('th','表記'),el('th','含むレコード数'));head.append(header);
    for(const r of rows){const row=el('tr'),cell=el('td'),b=el('button',r.label);b.type='button';b.dataset.word=r.label;b.onclick=()=>openSearch(r.label);cell.append(b);row.append(cell,el('td',r.count.toLocaleString()));body.append(row);}
    table.append(head,body);box.append(table);return box;
  }
  function renderTrends(){
    stats=currentStats();const box=$('trend-content');box.replaceChildren();
    const summary=el('div',undefined,'insight-stats');
    for(const [label,value] of [['集計対象',stats.total.toLocaleString()],['平均文字数',String(stats.averageLength)]]){
      const metric=el('div',undefined,'insight-stat');metric.append(el('span',label),el('strong',value));summary.append(metric);
    }
    const grid=el('div',undefined,'insight-grid');
    grid.append(bars('名前の文字数',stats.lengths,stats.total),bars('文字の構成',stats.scripts,stats.total),ranking('よく使われる漢字',stats.characters),ranking('よく使われる漢字2文字',stats.pairs));box.append(summary,grid);translateUI();
  }
  $('trend-platform').onchange=()=>{stats=null;renderTrends();};
  $('trend-consult').onclick=()=>{selectTab('consult');$('ai-message').value='収録されている名前の傾向を踏まえて、かぶりにくく覚えやすい名前の方向性を一緒に考えてください。';$('ai-message').focus();};
  document.querySelectorAll('[data-prompt]').forEach(button=>button.onclick=()=>{$('ai-message').value=button.dataset.prompt;$('ai-message').focus();});
  function message(role,text){
    const box=el('div',undefined,'chat-message '+role);box.append(el('strong',role==='user'?'あなた':'名前相談AI'));const body=el('div',text,'chat-body');box.append(body);$('ai-log').append(box);$('ai-log').scrollTop=$('ai-log').scrollHeight;return {box,body};
  }
  async function resetConversation(){const old=conversation;conversation=null;conversationLanguage=null;lastChecks=[];if(old)await old.delete();}
  async function loadAI(){
    if(loading||unloading||engine)return;
    if(!navigator.gpu){setStatus('このブラウザではWebGPUを利用できません。対応するPC版Chromeなどでお試しください。名前検索と傾向分析はそのまま使えます。',true);return;}
    const attempt=++generation;loading=true;aborter=new AbortController();controls();setStatus('AIの動作環境を確認しています…');
    try{
      const adapter=await navigator.gpu.requestAdapter();if(!adapter)throw new Error('GPU_UNAVAILABLE');
      const {Engine}=await import(SDK);
      if(attempt!==generation)return;
      setStatus('AIモデルを読み込んでいます。約2GBの取得に時間がかかる場合があります。');
      const response=await fetch(MODEL,{signal:aborter.signal});if(!response.ok||!response.body)throw new Error('MODEL_DOWNLOAD');
      const total=Number(response.headers.get('content-length'))||0;let received=0,lastUpdate=0;
      $('ai-progress').hidden=false;if(total)$('ai-progress').max=total;else $('ai-progress').removeAttribute('value');
      const stream=response.body.pipeThrough(new TransformStream({transform(chunk,controller){
        received+=chunk.byteLength;
        if(attempt===generation&&performance.now()-lastUpdate>1000){lastUpdate=performance.now();if(total)$('ai-progress').value=received;setStatus('AIモデルを読み込み中: '+Math.round(received/1024/1024).toLocaleString()+' MB');}
        controller.enqueue(chunk);
      }}));
      const ready=await Engine.create({model:stream,mainExecutorSettings:{maxNumTokens:8192}});
      if(attempt!==generation){await ready.delete();return;}
      engine=ready;setStatus('AIに相談できます。');
    }catch(error){if(attempt===generation)setStatus(error.message==='GPU_UNAVAILABLE'?'GPUを利用できません。ブラウザの設定や対応状況を確認してください。':'AIを起動できませんでした。対応ブラウザ・空きメモリ・通信環境を確認して、再度読み込んでください。',true);}
    finally{if(attempt===generation){loading=false;aborter=null;$('ai-progress').hidden=true;controls();}}
  }
  async function unloadAI(){
    if(unloading)return;unloading=true;
    generation++;cancelled=true;aborter?.abort();aborter=null;
    if(conversation){try{conversation.cancel();}catch{}}
    controls();setStatus('AIを終了しています…');
    await Promise.allSettled([activeLoad,activeSend]);
    try{await resetConversation();}catch{}
    const old=engine;engine=null;try{if(old)await old.delete();}catch{}
    loading=false;busy=false;unloading=false;$('ai-progress').hidden=true;controls();setStatus('AIを終了しました。名前検索と傾向分析はそのまま使えます。');
  }
  function showSuggestions(box,suggestions){
    lastChecks=[];if(!suggestions.length)return;
    const grid=el('div',undefined,'suggestion-grid');
    for(const s of suggestions){
      const queries=[s.name,...(s.reading?[s.reading]:[])];const matching=new Map();
      for(const q of queries)for(const h of find(q))if(h.type<2)matching.set(h.r.source_id,h.r);
      lastChecks.push({name:s.name,reading:s.reading,matching_records:matching.size});
      const card=el('article',undefined,'name-suggestion');card.append(el('h3',s.name,'candidate-name'));
      if(s.reading)card.append(el('p',s.reading,'candidate-reading'));
      card.append(el('p',s.reason,'candidate-reason'));
      card.append(el('p','同名・同じ読みの候補: '+matching.size.toLocaleString()+' 件',matching.size?'collision':''));
      const button=el('button','この名前を調べる');button.type='button';button.onclick=()=>openSearch(s.name);card.append(button);grid.append(card);
    }
    box.append(grid);
  }
  async function send(event){
    event.preventDefault();const input=$('ai-message').value.trim().slice(0,1200);if(!input||!engine||busy||loading||unloading)return;
    const attempt=generation;busy=true;cancelled=false;controls();let answer;
    try{
      const replyLanguage=typeof language==='string'?language:'ja';
      if(conversation&&conversationLanguage!==replyLanguage)await resetConversation();
      if(attempt!==generation)return;
      if(!conversation){
        const summary=currentStats();const ready=await engine.createConversation({prefillPrefaceOnInit:true,preface:{messages:[{role:'system',content:insight.prompt(summary,replyLanguage)}],extra_context:{enable_thinking:false}},sessionConfig:{maxOutputTokens:900}});
        if(attempt!==generation){await ready.delete();return;}conversation=ready;conversationLanguage=replyLanguage;
      }
      const checkContext=lastChecks.length?'\n前回の候補の辞書照合結果（未収録者もいるため未使用の保証ではありません）:'+JSON.stringify(lastChecks):'';
      const tokenCount=await conversation.getTokenCount();
      if(attempt!==generation)return;
      // UTF-8 bytes give a conservative bound for the next message; reserve output and template space.
      if(tokenCount+new TextEncoder().encode(input+checkContext).length+1200>8192){setStatus('会話が長くなりました。「相談をやり直す」で条件をまとめて相談してください。');return;}
      if(cancelled)return;
      $('ai-message').value='';message('user',input);answer=message('assistant','名前を考えています…');
      let raw='';
      for await(const chunk of conversation.sendMessageStreaming(input+checkContext)){
        if(cancelled||attempt!==generation)break;
        for(const item of chunk.content||[])if(item.type==='text')raw+=item.text||'';
      }
      if(attempt!==generation)return;
      if(cancelled){answer.body.textContent='回答を停止しました。';await resetConversation();}
      else{const result=insight.parseReply(raw);answer.body.textContent=result.reply;if(result.valid)answer.body.dataset.generated='true';showSuggestions(answer.box,result.suggestions);setStatus('続けて希望を伝えると、候補を絞り込めます。');}
    }catch(error){
      if(attempt===generation){const text=cancelled?'回答を停止しました。':'回答を作れませんでした。「相談をやり直す」か、AIを読み込み直してください。';if(answer)answer.body.textContent=text;else setStatus(text,true);try{await resetConversation();}catch{conversation=null;}}
    }finally{if(attempt===generation){busy=false;controls();$('ai-log').scrollTop=$('ai-log').scrollHeight;translateUI();}}
  }
  $('ai-start').onclick=()=>activeLoad=loadAI();$('ai-unload').onclick=unloadAI;$('ai-form').onsubmit=event=>activeSend=send(event);
  $('ai-stop').onclick=()=>{cancelled=true;conversation?.cancel();};
  $('ai-reset').onclick=async()=>{if(busy||loading||unloading)return;busy=true;controls();try{await resetConversation();$('ai-log').replaceChildren();setStatus(engine?'AIに相談できます。':'AIを読み込むと相談を始められます。');}finally{busy=false;controls();}};
  selectTab(location.hash.slice(1),false);controls();translateUI();
})();
