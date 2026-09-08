'use strict';
(() => {
  const BOOTH_URL='https://booth.pm/ja/items/8617663';
  const GITHUB_URL='https://github.com/Kirakun0328/text-to-vrma';
  const copy={
    ja:{
      supportKicker:'応援',supportTitle:'ぶいネームを応援してね！',supportText:'フォロー・RP・いいねで応援してもらえると、今後の更新の励みになります。',supportLink:'きらっちのXへ ↗',supportNote:'応援は任意です。申請・掲載の条件ではありません。',
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
  function init(){applyCurrentNameOverrides();ensureCss();mergeCommunity();enhanceTool();applyCopy();q('#language')?.addEventListener('change',()=>queueMicrotask(applyCopy));}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
