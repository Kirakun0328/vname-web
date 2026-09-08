'use strict';
(() => {
  const BOOTH_URL='https://booth.pm/ja/items/8617663';
  const GITHUB_URL='https://github.com/Kirakun0328/text-to-vrma';
  const copy={
    ja:{
      supportKicker:'応援',supportTitle:'フォロー・RP・いいねしてくれたらめちゃくちゃ嬉しいです！',supportText:'ぶいネームが役立ったら、フォロー・RP・いいねで応援してもらえると嬉しいです！ 今後もVTuber・AIVTuber・Vライバーや配信者向けの便利なものをいろいろ作っていく予定です。',supportLink:'きらっちのXへ ↗',supportNote:'応援は任意です。申請・掲載の条件ではありません。',
      toolKicker:'開発者のツール紹介',toolHeading:'Text-To-VRMA',toolCardHeading:'文章から、VRMモーションを自動生成。',toolLead:'「手を振る」「ジャンプする」など、欲しい動きをテキストで入力するだけ。',toolBody:'AIがキャラクターの動きを考え、VRM向けアニメーションとして生成します。VRMA形式で保存して、配信・動画・ゲーム制作などに使えます。',booth:'BOOTH版を使う（おすすめ） ↗',github:'GitHubを見る ↗',chips:['文章 → モーション','VRMAで保存','VRM向け']
    },
    en:{
      supportKicker:'SUPPORT',supportTitle:'Support V Name',supportText:'Follows, reposts, and likes help support future updates.',supportLink:'View Kiratchi on X ↗',supportNote:'Support is optional and is not required for listing requests.',
      toolKicker:'CREATOR TOOL',toolHeading:'Text-To-VRMA',toolCardHeading:'Generate VRM motion from text.',toolLead:'Type motions like “wave” or “jump” and let AI turn them into character animation.',toolBody:'AI designs the motion and generates animation for VRM characters. Save it as VRMA for streaming, videos, games, and other projects.',booth:'Get the BOOTH version (recommended) ↗',github:'View on GitHub ↗',chips:['Text → Motion','Save as VRMA','Made for VRM']
    },
    zh:{
      supportKicker:'支持',supportTitle:'支持 V Name！',supportText:'关注、转发和点赞都会成为持续更新的动力。',supportLink:'查看 Kiratchi 的 X ↗',supportNote:'支持完全自愿，不是申请收录的条件。',
      toolKicker:'开发者工具介绍',toolHeading:'Text-To-VRMA',toolCardHeading:'从文字自动生成 VRM 动作。',toolLead:'输入“挥手”“跳跃”等想要的动作即可。',toolBody:'AI 会设计角色动作并生成适用于 VRM 的动画，可保存为 VRMA，用于直播、视频、游戏等制作。',booth:'使用 BOOTH 版（推荐） ↗',github:'查看 GitHub ↗',chips:['文字 → 动作','保存为 VRMA','面向 VRM']
    },
    ko:{
      supportKicker:'응원',supportTitle:'V Name을 응원해 주세요!',supportText:'팔로우·리포스트·좋아요는 앞으로의 업데이트에 큰 힘이 됩니다.',supportLink:'Kiratchi의 X 보기 ↗',supportNote:'응원은 선택 사항이며 등록 신청 조건이 아닙니다.',
      toolKicker:'개발자 도구 소개',toolHeading:'Text-To-VRMA',toolCardHeading:'텍스트에서 VRM 모션을 자동 생성.',toolLead:'“손 흔들기”, “점프하기”처럼 원하는 동작을 텍스트로 입력하면 됩니다.',toolBody:'AI가 캐릭터 동작을 설계하고 VRM용 애니메이션을 생성합니다. VRMA로 저장해 방송, 영상, 게임 제작 등에 사용할 수 있습니다.',booth:'BOOTH 버전 사용하기 (추천) ↗',github:'GitHub 보기 ↗',chips:['문장 → 모션','VRMA 저장','VRM용']
    }
  };
  const q=(s,r=document)=>r.querySelector(s);
  const normalizeName=s=>String(s||'').normalize('NFKC').replace(/\s/g,'').toLowerCase();
  const normalizeAccountUrl=value=>{
    try{
      const u=new URL(value);let host=u.hostname.toLowerCase().replace(/^www\./,'');if(host==='twitter.com')host='x.com';
      let path;try{path=decodeURIComponent(u.pathname);}catch{path=u.pathname;}
      return host+path.replace(/\/+$/,'').toLowerCase();
    }catch{return String(value||'').trim().toLowerCase();}
  };
  const MANUAL_APPLICATIONS=[
    {source_id:'manual:youtube:are_studio',display_name:'荊伽鬼 アール',category:'VTuber',reading:'ばらかおり あーる',aliases:[],source_url:'https://www.youtube.com/@Are_Studio',activity_source:'https://www.youtube.com/@Are_Studio',name_source:'https://www.youtube.com/@Are_Studio',platform_accounts:[{platform:'youtube',id:'@Are_Studio',url:'https://www.youtube.com/@Are_Studio'}]},
    {source_id:'manual:youtube:maruri_games',display_name:'マルガリータ',category:'VTuber',reading:'まるがりーた',aliases:[],source_url:'https://www.youtube.com/@maruri_games',activity_source:'https://www.youtube.com/@maruri_games',name_source:'https://www.youtube.com/@maruri_games',platform_accounts:[{platform:'youtube',id:'@maruri_games',url:'https://www.youtube.com/@maruri_games'}]},
    {source_id:'manual:youtube:shiroganemoka',display_name:'白銀モカ',category:'VTuber',reading:'しろがねもか',aliases:[],source_url:'https://www.youtube.com/@shiroganemoka',activity_source:'https://www.youtube.com/@shiroganemoka',name_source:'https://www.youtube.com/@shiroganemoka',platform_accounts:[{platform:'youtube',id:'@shiroganemoka',url:'https://www.youtube.com/@shiroganemoka'}]},
    {source_id:'youtube:UClQ_JfAZ2h7rfXSZh3Z6uPA',display_name:'宵月 灯',category:'VTuber',reading:'よいつき ともり',aliases:[],source_url:'https://www.youtube.com/channel/UClQ_JfAZ2h7rfXSZh3Z6uPA',activity_source:'https://www.youtube.com/channel/UClQ_JfAZ2h7rfXSZh3Z6uPA',name_source:'https://www.youtube.com/channel/UClQ_JfAZ2h7rfXSZh3Z6uPA',platform_accounts:[{platform:'youtube',id:'channel/UClQ_JfAZ2h7rfXSZh3Z6uPA',url:'https://www.youtube.com/channel/UClQ_JfAZ2h7rfXSZh3Z6uPA'}]},
    {source_id:'manual:youtube:tkinoworks',display_name:'ときの喜乃',category:'VTuber',reading:'ときのきの',aliases:[],source_url:'https://www.youtube.com/@tkinoworks',activity_source:'https://www.youtube.com/@tkinoworks',name_source:'https://www.youtube.com/@tkinoworks',platform_accounts:[{platform:'youtube',id:'@tkinoworks',url:'https://www.youtube.com/@tkinoworks'}]},
    {source_id:'manual:twitch:aoto_hiiragi',display_name:'柊木蒼桜音',category:'VTuber',reading:'ひいらぎあおと',aliases:[],source_url:'https://www.twitch.tv/aoto_hiiragi',activity_source:'https://www.twitch.tv/aoto_hiiragi',name_source:'https://www.twitch.tv/aoto_hiiragi',platform_accounts:[{platform:'twitch',id:'aoto_hiiragi',url:'https://www.twitch.tv/aoto_hiiragi'}]},
    {source_id:'manual:youtube:hoshitsukinyao',display_name:'星槻にゃお',category:'VTuber',reading:'ほしつきにゃお',aliases:[],source_url:'https://www.youtube.com/@%E6%98%9F%E6%A7%BB%E3%81%AB%E3%82%83%E3%81%8A_Ch',activity_source:'https://www.youtube.com/@%E6%98%9F%E6%A7%BB%E3%81%AB%E3%82%83%E3%81%8A_Ch',name_source:'https://www.youtube.com/@%E6%98%9F%E6%A7%BB%E3%81%AB%E3%82%83%E3%81%8A_Ch',platform_accounts:[{platform:'youtube',id:'@星槻にゃお_Ch',url:'https://www.youtube.com/@%E6%98%9F%E6%A7%BB%E3%81%AB%E3%82%83%E3%81%8A_Ch'}]},
    {source_id:'manual:youtube:renitigoc',display_name:'れん いちご🍓🥛',category:'VTuber',reading:'れん いちご',aliases:[],source_url:'https://www.youtube.com/@RenItigochannel',activity_source:'https://www.youtube.com/@RenItigochannel',name_source:'https://www.youtube.com/@RenItigochannel',platform_accounts:[{platform:'youtube',id:'@RenItigochannel',url:'https://www.youtube.com/@RenItigochannel'}]},
    {source_id:'youtube:UCBlg-qFBr6TYP0rcWuNSpNg',display_name:'ADらこん',category:'VTuber',reading:'えーでぃーらこん',aliases:[],source_url:'https://www.youtube.com/channel/UCBlg-qFBr6TYP0rcWuNSpNg',activity_source:'https://www.youtube.com/channel/UCBlg-qFBr6TYP0rcWuNSpNg',name_source:'https://www.youtube.com/channel/UCBlg-qFBr6TYP0rcWuNSpNg',platform_accounts:[{platform:'youtube',id:'channel/UCBlg-qFBr6TYP0rcWuNSpNg',url:'https://www.youtube.com/channel/UCBlg-qFBr6TYP0rcWuNSpNg'}]},
    {source_id:'manual:x:prairialvtuber',display_name:'萱草プレリアル',category:'VTuber',reading:'かやぐさぷれりある',aliases:['萱草プレリアル＠ボードゲーム系Vtuber🌿♟️📕（惨劇推し）'],source_url:'https://x.com/PrairialVtuber',activity_source:'https://x.com/PrairialVtuber',name_source:'https://x.com/PrairialVtuber',platform_accounts:[{platform:'x',id:'PrairialVtuber',url:'https://x.com/PrairialVtuber'}]},
    {source_id:'manual:youtube:asuka_omoci',display_name:'おもちのASUKAさん',category:'VTuber',reading:'おもちのあすかさん',aliases:[],source_url:'https://www.youtube.com/@asuka_omoci',activity_source:'https://www.youtube.com/@asuka_omoci',name_source:'https://www.youtube.com/@asuka_omoci',platform_accounts:[{platform:'youtube',id:'@asuka_omoci',url:'https://www.youtube.com/@asuka_omoci'}]},
    {source_id:'manual:youtube:forestwingskftw',display_name:'森ﾂﾊﾞｻ',category:'VTuber',reading:'もりつばさ',aliases:[],source_url:'https://www.youtube.com/@ForestWingsKFtW',activity_source:'https://www.youtube.com/@ForestWingsKFtW',name_source:'https://www.youtube.com/@ForestWingsKFtW',platform_accounts:[{platform:'youtube',id:'@ForestWingsKFtW',url:'https://www.youtube.com/@ForestWingsKFtW'}]},
    {source_id:'manual:youtube:kagurasakitanio',display_name:'神楽裂タニオ',category:'VTuber',reading:'かぐらさきたにお',aliases:[],source_url:'https://www.youtube.com/@kagurasakitanio',activity_source:'https://www.youtube.com/@kagurasakitanio',name_source:'https://www.youtube.com/@kagurasakitanio',platform_accounts:[{platform:'youtube',id:'@kagurasakitanio',url:'https://www.youtube.com/@kagurasakitanio'}]}
  ].map(r=>({...r,reading_source:'manual:application',reading_source_kind:'manual',manual_submitted_at:'2026-09-08'}));
  function accountKeys(r){return [r.source_url,r.activity_source,r.official_website,...(r.platform_accounts||[]).map(a=>a.url),...(r.media?.accounts||[]).map(a=>a.url)].filter(Boolean).map(normalizeAccountUrl);}
  function applyManualFields(target,app){
    const previous=target.display_name;
    target.display_name=app.display_name;target.category=app.category;target.reading=app.reading;target.reading_source='manual:application';target.reading_source_kind='manual';target.reading_inferred=false;target.manual_submitted_at=app.manual_submitted_at;target.name_source=app.name_source;
    if(!target.source_url)target.source_url=app.source_url;if(!target.activity_source)target.activity_source=app.activity_source;
    target.aliases=[...new Set([...(target.aliases||[]),...(app.aliases||[]),...(previous&&previous!==app.display_name?[previous]:[])])];
    const accounts=[...(target.platform_accounts||[])];const seen=new Set(accounts.map(a=>normalizeAccountUrl(a.url)));
    for(const a of app.platform_accounts||[])if(!seen.has(normalizeAccountUrl(a.url))){accounts.push(a);seen.add(normalizeAccountUrl(a.url));}target.platform_accounts=accounts;
    if(typeof key==='function')target.keys=[target.display_name,target.reading,target.romanized_name,...target.aliases].map(key);
  }
  function findManualTarget(app){
    if(typeof records==='undefined'||!Array.isArray(records))return null;
    const appKeys=new Set(accountKeys(app));let target=records.find(r=>r.source_id===app.source_id||accountKeys(r).some(k=>appKeys.has(k)));
    if(target)return target;
    const sameName=records.filter(r=>normalizeName(r.display_name)===normalizeName(app.display_name));return sameName.length===1?sameName[0]:null;
  }
  function applyManualApplications(){
    if(typeof records==='undefined'||!Array.isArray(records)||typeof window.VNameAddCommunity!=='function')return;
    const additions=[];let changed=false;
    for(const app of MANUAL_APPLICATIONS){const target=findManualTarget(app);if(target){applyManualFields(target,app);changed=true;}else additions.push({...app});}
    if(additions.length)window.VNameAddCommunity(additions);
    for(const app of MANUAL_APPLICATIONS){const target=findManualTarget(app);if(target){applyManualFields(target,app);changed=true;}}
    if(changed&&typeof search==='function')search();
  }
  function applyCurrentNameOverrides(){
    if(typeof records==='undefined'||!Array.isArray(records))return;
    const overrides=[{
      oldNames:['木乃伊綿巻','木乃伊 綿巻'],
      currentName:'木乃伊めんま',
      reading:'きのいめんま',
      sourceId:'youtube:UCsg2pWGJveeTKAGVSww05tg',
      youtubeId:'UCsg2pWGJveeTKAGVSww05tg',
      xHandle:'miira_mennma',
      source:'https://www.youtube.com/@kinoi_menma'
    }];
    let changed=false;
    for(const r of records){
      for(const override of overrides){
        const oldKeys=new Set(override.oldNames.map(normalizeName));
        const accounts=[...(r.platform_accounts||[]),...(r.media?.accounts||[])];
        const accountMatch=accounts.some(a=>String(a.id||a.url||'').includes(override.youtubeId)||String(a.id||a.url||'').includes(override.xHandle));
        if(!oldKeys.has(normalizeName(r.display_name))&&r.source_id!==override.sourceId&&!accountMatch)continue;
        const previous=r.display_name;
        r.display_name=override.currentName;
        r.aliases=[...new Set([...(r.aliases||[]),...(previous&&previous!==override.currentName?[previous]:[]),...override.oldNames])];
        r.reading=override.reading;
        r.reading_inferred=false;
        r.name_source=override.source;
        r.reading_source=override.source;
        r.reading_source_kind='official';
        r.current_name_checked_at='2026-09-08';
        if(typeof key==='function')r.keys=[r.display_name,r.reading,r.romanized_name,...r.aliases].map(key);
        changed=true;
        break;
      }
    }
    if(changed&&typeof search==='function')search();
  }
  function ensureCss(){
    if(q('link[data-ui-polish]'))return;
    const link=document.createElement('link');link.rel='stylesheet';link.href='ui-polish.css?v=3';link.dataset.uiPolish='true';document.head.append(link);
  }
  function mergeCommunity(){
    const register=q('#register');if(!register||register.dataset.unified==='true')return;
    const request=q('.community-card:not(.support-card)',register),support=q('.support-card',register);if(!request||!support)return;
    register.classList.add('community-actions--unified');request.classList.add('community-card--unified','community-card--split');

    const requestPane=document.createElement('div');requestPane.className='community-request-pane';
    while(request.firstChild)requestPane.append(request.firstChild);

    const requestCopy=document.createElement('div');requestCopy.className='community-request-copy';
    const requestActions=document.createElement('div');requestActions.className='community-request-actions';
    for(const node of [q('.community-kicker',requestPane),q('h2',requestPane),q('.request-fields',requestPane)])if(node)requestCopy.append(node);
    for(const node of [q('.primary-action',requestPane),q('.community-notes',requestPane)])if(node)requestActions.append(node);
    requestPane.replaceChildren(requestCopy,requestActions);

    const supportPane=document.createElement('aside');supportPane.className='community-support-inline community-support-pane';
    const copyBox=document.createElement('div');copyBox.className='community-support-copy';
    copyBox.innerHTML='<span class="community-support-kicker" data-polish="supportKicker"></span><strong data-polish="supportTitle"></strong><p data-polish="supportText"></p><small data-polish="supportNote"></small>';
    supportPane.append(copyBox);

    const link=q('.community-button',support);if(link){link.classList.remove('primary-action');link.classList.add('community-support-link');link.dataset.polish='supportLink';supportPane.append(link);}
    request.replaceChildren(requestPane,supportPane);support.remove();register.dataset.unified='true';
  }
  function enhanceTool(){
    const section=q('.creator-tools'),card=q('.tool-promo');if(!section||!card||card.dataset.polished==='true')return;
    const kicker=q('.creator-tools-heading .community-kicker',section),heading=q('.creator-tools-heading h2',section),image=q('.tool-promo-image',card),body=q('.tool-promo-body',card),cardHeading=q('h3',body),lead=q('.tool-promo-lead',body),paragraphs=body?[...body.querySelectorAll('p')]:[];
    if(kicker)kicker.dataset.polish='toolKicker';if(heading)heading.dataset.polish='toolHeading';if(cardHeading)cardHeading.dataset.polish='toolCardHeading';if(lead)lead.dataset.polish='toolLead';
    const bodyText=paragraphs.find(p=>!p.classList.contains('tool-promo-lead'));if(bodyText)bodyText.dataset.polish='toolBody';
    if(image){image.href=BOOTH_URL;image.setAttribute('aria-label','Text-To-VRMAのBOOTHページを開く');}
    const existing=q('.community-button',body);if(existing){existing.href=BOOTH_URL;existing.dataset.polish='booth';existing.classList.add('tool-booth-button');}
    const chips=document.createElement('div');chips.className='tool-feature-chips';chips.innerHTML='<span data-polish-chip="0"></span><span data-polish-chip="1"></span><span data-polish-chip="2"></span>';
    const github=document.createElement('a');github.className='community-button tool-github-button';github.href=GITHUB_URL;github.target='_blank';github.rel='noopener noreferrer';github.dataset.polish='github';
    const actions=document.createElement('div');actions.className='tool-promo-actions';if(existing)actions.append(existing);actions.append(github);
    if(bodyText){bodyText.after(chips,actions);}else if(body){body.append(chips,actions);}
    card.dataset.polished='true';
  }
  function applyCopy(){
    const lang=q('#language')?.value||document.documentElement.lang||'ja',t=copy[lang]||copy.ja;
    document.querySelectorAll('[data-polish]').forEach(node=>{const keyName=node.dataset.polish;if(t[keyName])node.textContent=t[keyName];});
    document.querySelectorAll('[data-polish-chip]').forEach(node=>{node.textContent=t.chips[Number(node.dataset.polishChip)]||'';});
  }
  function init(){applyManualApplications();applyCurrentNameOverrides();ensureCss();mergeCommunity();enhanceTool();applyCopy();q('#language')?.addEventListener('change',()=>queueMicrotask(applyCopy));}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
