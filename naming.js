'use strict';
(() => {
  const insight=window.VNameInsights;
  const SDK='https://cdn.jsdelivr.net/npm/@litert-lm/core@0.17.0/+esm';
  const model=window.VNameModel;
  let engine=null, conversation=null, loading=false, unloading=false, busy=false, cancelled=false, generation=0, aborter=null;
  let activeLoad=null, activeSend=null;
  let conversationLanguage=null, conversationScope=null;
  let modelSaved=false, cacheSupported=true;
  let mediaIndex=null, stats=null, lastChecks=[];
  let promptConversation=null, initialPrompts=[];
  let followConversation=true;
  const conversationHistory=$('ai-history');
  conversationHistory.addEventListener('scroll',()=>{
    followConversation=conversationHistory.scrollHeight-conversationHistory.clientHeight-conversationHistory.scrollTop<=64;
  },{passive:true});
  function scrollConversation(force=false){
    if(force||followConversation){conversationHistory.scrollTop=conversationHistory.scrollHeight;followConversation=true;}
  }
  const tabs=[...document.querySelectorAll('[data-tab]')];
  const el=(tag,textValue,className)=>{const e=document.createElement(tag);if(textValue!==undefined)e.textContent=textValue;if(className)e.className=className;return e;};
  function setStatus(value,error=false){$('ai-status').textContent=value;$('ai-status').dataset.error=String(error);translateUI();}
  function controls(){
    $('ai-start').hidden=!!engine;$('ai-start').disabled=loading||unloading;
    $('ai-unload').hidden=!engine&&!loading&&!unloading;$('ai-unload').disabled=unloading;
    $('ai-send').disabled=!engine||busy||loading||unloading;
    $('ai-stop').hidden=!busy;
    $('ai-reset').disabled=busy||loading||unloading;
    $('ai-save').disabled=loading||busy||unloading||!cacheSupported;
    $('ai-delete').disabled=!modelSaved||loading||busy||unloading;
    $('ai-message').disabled=busy;
    $('ai-start').textContent=modelSaved?'保存済みAIを起動':'AIを準備する（初回 約2GB）';
    $('ai-ready').textContent=loading?'準備中':engine?'相談できます':'AIの準備が必要です';
    $('ai-ready').dataset.ready=String(!!engine&&!loading&&!unloading);
    for(const button of $('ai-prompts').children)button.disabled=!engine||busy||loading||unloading;
  }
  async function refreshStorage(){
    const saved=await model.status();modelSaved=saved.saved;cacheSupported=saved.supported;
    $('ai-storage').textContent=saved.saved?'モデル保存済み：約2GB。同じモデルを再利用します。':saved.supported?'保存済みのモデルはありません。':'このブラウザではモデルを保存できません。';
    if(!saved.supported)$('ai-save').checked=false;
    controls();translateUI();
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
  function openSearch(name){selectTab('search');$('query').value=name;$('search-tag').value='all';$('search-platform').value='all';search();$('query').focus();}
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
  function scopeKey(){return [$('trend-platform').value||'all',$('trend-tag').value||'all',$('trend-script').value||'all'].join(':');}
  function selectedRows(){
    prepareMedia();const media=$('trend-platform').value||'all',tag=$('trend-tag').value||'all',script=$('trend-script').value||'all';
    const writing={kana:/[\p{Script=Hiragana}\p{Script=Katakana}]/u,han:/\p{Script=Han}/u,latin:/[A-Za-z]/};
    return (media==='all'?records:(mediaIndex.get(media)||[])).filter(r=>(tag==='all'||categoryOf(r)===tag)&&(!writing[script]||writing[script].test(r.display_name.normalize('NFKC'))));
  }
  function currentStats(){
    const scope=scopeKey();if(stats?.scope===scope)return stats;
    const rows=selectedRows();stats={...insight.analyze(rows),scope,platform:window.VNamePlatforms.labels[$('trend-platform').value]||'all',tag:$('trend-tag').value||'all',writing:$('trend-script').value||'all'};return stats;
  }
  function bars(title,rows,total){
    const box=el('section',undefined,'insight-card');box.append(el('h3',title));
    for(const r of rows){
      const row=el('div',undefined,'insight-row'),track=el('div',undefined,'track'),bar=el('div',undefined,'bar');
      bar.style.width=(total?r.count/total*100:0)+'%';track.setAttribute('aria-hidden','true');track.append(bar);
      const number=el('span',r.count.toLocaleString(),'numeric');number.append(el('small',(total?(r.count/total*100).toFixed(1):'0.0')+'%'));row.append(el('span',r.label),track,number);box.append(row);
    }
    return box;
  }
  function ranking(title,rows){
    const box=el('section',undefined,'insight-card');box.append(el('h3',title));
    const table=el('table'),head=el('thead'),header=el('tr'),body=el('tbody');header.append(el('th','表記'),el('th','該当件数'),el('th','割合'));head.append(header);
    for(const r of rows){const row=el('tr'),cell=el('td'),b=el('button',r.label);b.type='button';b.dataset.word=r.label;b.onclick=()=>openSearch(r.label);cell.append(b);row.append(cell,el('td',r.count.toLocaleString()),el('td',(stats.total?(r.count/stats.total*100).toFixed(1):'0.0')+'%'));body.append(row);}
    table.append(head,body);box.append(table);return box;
  }
  function renderTrends(){
    stats=currentStats();const box=$('trend-content');box.replaceChildren();
    const summary=el('div',undefined,'insight-stats');
    for(const [label,value] of [['集計対象',stats.total.toLocaleString()],['平均文字数',String(stats.averageLength)],['文字数の中央値',String(stats.medianLength)],['よくある文字数',String(stats.commonLengths[0]?.length??'—')]]){
      const metric=el('div',undefined,'insight-stat');metric.append(el('span',label),el('strong',value));summary.append(metric);
    }
    const grid=el('div',undefined,'insight-grid');
    grid.append(bars('名前の文字数',stats.lengths,stats.total),bars('文字の構成',stats.scripts,stats.total),ranking('よく使われる漢字',stats.characters),ranking('よく使われる漢字2文字',stats.pairs),ranking('よく使われる先頭2文字',stats.prefixes),ranking('よく使われる末尾2文字',stats.suffixes));box.append(summary);
    if(!stats.total)box.append(el('p','条件に一致する掲載がありません。','trend-note'));
    box.append(grid,el('p','先頭・末尾は表示名の2文字を比較しています。苗字や語源の分類ではありません。漢字は各レコードで1回だけ数え、割合は選択中の集計対象に対する値です。','trend-note'));translateUI();
  }
  $('trend-platform').onchange=()=>{stats=null;renderTrends();};
  $('trend-tag').onchange=$('trend-script').onchange=$('trend-platform').onchange;
  $('trend-consult').onclick=()=>{selectTab('consult');$('ai-message').value='収録されている名前の傾向を踏まえて、かぶりにくく覚えやすい名前の方向性を一緒に考えてください。';$('ai-message').focus();};
  function showPrompts(prompts=[],emptyText='続けて、希望を自由に入力してください。'){
    const box=$('ai-prompts');box.replaceChildren();
    $('ai-prompts-status').textContent=prompts.length?'AIからの相談ヒント':emptyText;
    for(const prompt of prompts){const button=el('button',prompt);button.type='button';button.title=prompt;button.dataset.generated='true';button.onclick=()=>{if(busy||loading||unloading)return;$('ai-message').value=prompt;$('ai-message').focus();};box.append(button);}
    controls();translateUI();
  }
  async function createInitialPrompts(attempt){
    let current;
    showPrompts([],'相談のきっかけを考えています…');
    try{
      const lang=typeof language==='string'?language:'ja';
      const instruction=`VTuber・AIVTuber・Vライバーの名前相談のきっかけになる、ユーザーが送れる短い相談文を3件生成してください。方向性は毎回あなたが考え、3件で異なる雰囲気・モチーフ・希望にしてください。言語は${lang}。各文は日本語なら20文字程度、どの言語でも60文字以内。JSONのみ: {"next_prompts":["相談文","相談文","相談文"]}。説明やコードフェンスは不要です。`;
      current=await engine.createConversation({prefillPrefaceOnInit:true,preface:{messages:[{role:'system',content:instruction}],extra_context:{enable_thinking:false}},sessionConfig:{maxOutputTokens:256}});
      if(attempt!==generation)return;
      promptConversation=current;
      let raw='';
      for await(const chunk of current.sendMessageStreaming('名前相談のきっかけを提案してください。')){
        if(attempt!==generation)return;
        if(typeof chunk==='string')raw+=chunk;
        else if(typeof chunk.content==='string')raw+=chunk.content;
        else for(const item of chunk.content||[])if(item.type==='text')raw+=item.text||'';
      }
      if(attempt===generation){initialPrompts=insight.parseReply(raw).nextPrompts||[];showPrompts(initialPrompts,'候補を生成できませんでした。希望を直接入力して相談できます。');}
    }catch{if(attempt===generation)showPrompts([],'候補を生成できませんでした。希望を直接入力して相談できます。');}
    finally{if(promptConversation===current)promptConversation=null;if(current)try{await current.delete();}catch{}}
  }
  function message(role,text){
    $('ai-welcome').hidden=true;
    const box=el('div',undefined,'chat-message '+role);
    if(role==='assistant'){const avatar=el('img');avatar.src='assets/naming-robot.png';avatar.alt='';avatar.className='chat-avatar';avatar.width=40;avatar.height=40;box.append(avatar);}
    const content=el('div',undefined,'chat-message-content');content.append(el('strong',role==='user'?'あなた':'名前相談AI'));const body=el('div',text,'chat-body');content.append(body);box.append(content);$('ai-log').append(box);translateUI();scrollConversation(role==='user');return {box:content,body};
  }
  async function resetConversation(){const old=conversation;conversation=null;conversationLanguage=null;conversationScope=null;lastChecks=[];if(old)await old.delete();}
  async function loadAI(){
    if(loading||unloading||engine)return;
    if(!navigator.gpu){setStatus('このブラウザではWebGPUを利用できません。対応するPC版Chromeなどでお試しください。名前検索と傾向分析はそのまま使えます。',true);return;}
    const attempt=++generation;loading=true;aborter=new AbortController();controls();setStatus('AIの動作環境を確認しています…');
    try{
      const adapter=await navigator.gpu.requestAdapter();if(!adapter)throw new Error('GPU_UNAVAILABLE');
      const {Engine}=await import(SDK);
      if(attempt!==generation)return;
      let lastUpdate=0;
      const stream=await model.obtain({signal:aborter.signal,save:$('ai-save').checked,onProgress:progress=>{
        if(attempt!==generation)return;
        if(progress.phase==='download'&&performance.now()-lastUpdate>800){lastUpdate=performance.now();$('ai-progress').hidden=false;$('ai-progress').max=progress.total;$('ai-progress').value=progress.received;setStatus('AIモデルを読み込み中: '+Math.round(progress.received/1024/1024).toLocaleString()+' MB');}
      }});
      if(attempt!==generation){await stream.cancel();return;}
      $('ai-progress').hidden=false;$('ai-progress').removeAttribute('value');setStatus('この端末でAIを起動しています…');
      const ready=await Engine.create({model:stream,mainExecutorSettings:{maxNumTokens:8192}});
      if(attempt!==generation){await ready.delete();return;}
      engine=ready;setStatus('相談のきっかけを考えています…');await createInitialPrompts(attempt);if(attempt===generation)setStatus('AIに相談できます。');
    }catch(error){if(attempt===generation)setStatus(error.message==='GPU_UNAVAILABLE'?'GPUを利用できません。ブラウザの設定や対応状況を確認してください。':/^CACHE_/.test(error.message)?'モデルを保存できませんでした。空き容量を確認するか「モデルを端末に保存」をオフにしてお試しください。':'AIを起動できませんでした。PCの対応ブラウザで、空きメモリと通信環境を確認してください。',true);}
    finally{if(attempt===generation){loading=false;aborter=null;$('ai-progress').hidden=true;await refreshStorage();}}
  }
  async function unloadAI(){
    if(unloading)return;unloading=true;
    generation++;cancelled=true;aborter?.abort();aborter=null;
    if(conversation){try{conversation.cancel();}catch{}}
    if(promptConversation){try{promptConversation.cancel();}catch{}}
    controls();setStatus('AIを終了しています…');
    await Promise.allSettled([activeLoad,activeSend]);
    try{await resetConversation();}catch{}
    const old=engine;engine=null;try{if(old)await old.delete();}catch{}
    loading=false;busy=false;unloading=false;$('ai-progress').hidden=true;initialPrompts=[];showPrompts([],'AIの準備後に、相談のきっかけを提案します。');controls();setStatus('AIを終了しました。名前検索と傾向分析はそのまま使えます。');
  }
  function showSuggestions(box,suggestions,summary){
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
      if(summary){
        const length=[...s.name.normalize('NFKC').replace(/\s/g,'')].length;
        const evidence=el('p',undefined,'candidate-evidence'),scope=el('span',undefined,'candidate-scope');
        for(const label of [summary.platform==='all'?'すべての媒体':summary.platform,summary.tag==='all'?'すべてのタグ':summary.tag,{kana:'かなを含む',han:'漢字を含む',latin:'英字を含む'}[summary.writing]||'すべての表記'])scope.append(el('span',label));
        evidence.append(el('span','傾向との比較'),scope,el('span','同じ文字数の収録名'),el('strong',(summary.exactLengths[length]||0).toLocaleString()+' / '+summary.total.toLocaleString()),el('span','集計対象内の件数です。名前の未使用を保証するものではありません。'));card.append(evidence);
      }
      const button=el('button','この名前を調べる');button.type='button';button.onclick=()=>openSearch(s.name);card.append(button);grid.append(card);
    }
    box.append(grid);
  }
  async function receive(text,attempt){
    let raw='';for await(const chunk of conversation.sendMessageStreaming(text)){
      if(cancelled||attempt!==generation)break;
      if(typeof chunk==='string')raw+=chunk;else if(typeof chunk.content==='string')raw+=chunk.content;else for(const item of chunk.content||[])if(item.type==='text')raw+=item.text||'';
    }return raw;
  }
  async function send(event){
    event.preventDefault();const input=$('ai-message').value.trim().slice(0,1200);if(!input||!engine||busy||loading||unloading)return;
    const attempt=generation;busy=true;cancelled=false;controls();let answer;
    try{
      const replyLanguage=typeof language==='string'?language:'ja';
      const summary=currentStats();
      if(conversation&&(conversationLanguage!==replyLanguage||conversationScope!==summary.scope))await resetConversation();
      if(attempt!==generation)return;
      if(!conversation){
        const ready=await engine.createConversation({prefillPrefaceOnInit:true,preface:{messages:[{role:'system',content:insight.prompt(summary,replyLanguage)}],extra_context:{enable_thinking:false}},sessionConfig:{maxOutputTokens:1200}});
        if(attempt!==generation){await ready.delete();return;}conversation=ready;conversationLanguage=replyLanguage;conversationScope=summary.scope;
      }
      const checkContext=lastChecks.length?'\n前回の候補の辞書照合結果（未収録者もいるため未使用の保証ではありません）:'+JSON.stringify(lastChecks):'';
      const tokenCount=await conversation.getTokenCount();
      if(attempt!==generation)return;
      // UTF-8 bytes give a conservative bound for the next message; reserve output and template space.
      if(tokenCount+new TextEncoder().encode(input+checkContext).length+1500>8192){setStatus('会話が長くなりました。「相談をやり直す」で条件をまとめて相談してください。');return;}
      if(cancelled)return;
      const needsNames=insight.wantsNames(input,lastChecks.length>0);
      $('ai-message').value='';message('user',input);answer=message('assistant','名前を考えています…');
      let result=insight.parseReply(await receive(input+checkContext,attempt));
      if(attempt!==generation)return;
      if(needsNames&&!result.suggestions.length&&!cancelled){
        const repair=`前の回答には具体的な候補名がありません。元の希望「${input}」と選択中の辞書集計に合わせて、創作した名前の候補を3件、今ここで書いてください。説明の予告は不要。今回はJSONではなく、必ず1行1候補の「名前 | 読み | 希望に合う理由」の3列で出力してください。名前は40文字以内、理由は短い1文。固定例のコピーではなく新しく考えてください。回答言語は${replyLanguage}。`;
        const used=await conversation.getTokenCount();if(attempt!==generation)return;
        if(!cancelled&&used+new TextEncoder().encode(repair).length+1500<=8192){
          answer.body.textContent='名前の候補を補っています…';setStatus('名前の候補を補っています…');
          const completed=insight.parseRepair(await receive(repair,attempt));if(attempt!==generation)return;
          if(completed.suggestions.length)result=completed;
        }
      }
      if(attempt!==generation)return;
      if(cancelled){answer.body.textContent='回答を停止しました。';await resetConversation();}
      else if(needsNames&&!result.suggestions.length){answer.body.textContent='具体的な名前候補を生成できませんでした。希望を短くまとめて、もう一度相談してください。';showPrompts([]);setStatus(answer.body.textContent,true);}
      else{answer.body.textContent=result.reply;if(result.valid)answer.body.dataset.generated='true';showSuggestions(answer.box,result.suggestions,summary);showPrompts(result.nextPrompts);setStatus(result.incomplete?'回答が途中で終わったため、読み取れた内容を表示しています。':result.valid?(result.structured?'続けて希望を伝えると、候補を絞り込めます。':'文章で回答しました。候補の名前は「名前をチェック」で確認してください。'):'回答が途中で終わりました。条件を短くして、もう一度相談してください。',!result.valid||!!result.incomplete);}
    }catch(error){
      if(attempt===generation){const text=cancelled?'回答を停止しました。':'この端末では回答を生成できませんでした。PCで、条件を短くしてお試しください。';if(answer)answer.body.textContent=text;setStatus(text,!cancelled);try{await resetConversation();}catch{conversation=null;}}
    }finally{if(attempt===generation){busy=false;controls();translateUI();scrollConversation();}}
  }
  $('ai-start').onclick=()=>activeLoad=loadAI();$('ai-unload').onclick=unloadAI;$('ai-form').onsubmit=event=>activeSend=send(event);
  $('ai-stop').onclick=()=>{cancelled=true;conversation?.cancel();};
  $('ai-reset').onclick=async()=>{if(busy||loading||unloading)return;busy=true;controls();try{await resetConversation();$('ai-log').replaceChildren();$('ai-welcome').hidden=false;followConversation=true;conversationHistory.scrollTop=0;showPrompts(initialPrompts);setStatus(engine?'AIに相談できます。':'AIを読み込むと相談を始められます。');}finally{busy=false;controls();}};
  $('ai-delete').onclick=async()=>{if(loading||busy||unloading)return;await unloadAI();unloading=true;controls();try{await model.remove();await refreshStorage();setStatus('保存したAIモデルを削除しました。');}catch{setStatus('削除できませんでした。ブラウザのサイトデータ設定から削除できます。',true);}finally{unloading=false;controls();}};
  selectTab(location.hash.slice(1),false);controls();translateUI();refreshStorage();
})();
