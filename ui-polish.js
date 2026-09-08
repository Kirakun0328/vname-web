'use strict';
(() => {
  const BOOTH_URL='https://booth.pm/ja/items/8617663';
  const GITHUB_URL='https://github.com/Kirakun0328/text-to-vrma';
  const copy={
    ja:{
      supportTitle:'応援してね！',supportText:'ぶいネームを気に入ってもらえたら、フォロー・RP・いいねで応援してもらえると嬉しいです！',supportLink:'きらっちのXへ ↗',supportNote:'応援は任意です。申請・掲載の条件ではありません。',
      toolKicker:'Text-To-VRMA',toolHeading:'文章を入れるだけ。VRMキャラクターのモーションをAI生成。',toolLead:'「手を振る」「かわいくジャンプ」など、欲しい動きを文章で入力するだけ。',toolBody:'Text-To-VRMAは、AIが文章からキャラクターの動きを考えてVRM向けモーションを生成し、VRMA形式で保存できるツールです。配信・動画・ゲームで使いたい動きを、専門的なアニメーション制作なしで手軽に形にできます。',booth:'BOOTH版を使う（おすすめ） ↗',github:'GitHubを見る ↗',chips:['文章 → モーション','VRMAで保存','VRM向け']
    },
    en:{
      supportTitle:'Support V Name',supportText:'If you like V Name, follows, reposts, and likes help support future updates!',supportLink:'View Kiratchi on X ↗',supportNote:'Support is optional and is not required for listing requests.',
      toolKicker:'Text-To-VRMA',toolHeading:'Type a sentence. Generate VRM character motion with AI.',toolLead:'“Wave your hand.” “Do a cute jump.” Just describe the motion you want.',toolBody:'Text-To-VRMA uses AI to turn text into motion for VRM characters and saves it as VRMA. Create motions for streaming, videos, and games without doing full animation work by hand.',booth:'Get the BOOTH version (recommended) ↗',github:'View on GitHub ↗',chips:['Text → Motion','Save as VRMA','Made for VRM']
    },
    zh:{
      supportTitle:'支持 V Name！',supportText:'如果你喜欢 V Name，欢迎通过关注、转发和点赞支持后续更新！',supportLink:'查看 Kiratchi 的 X ↗',supportNote:'支持完全自愿，不是申请收录的条件。',
      toolKicker:'Text-To-VRMA',toolHeading:'输入一句话，用 AI 生成 VRM 角色动作。',toolLead:'“挥挥手”“可爱地跳一下”——只需描述你想要的动作。',toolBody:'Text-To-VRMA 可根据输入文字用 AI 生成适用于 VRM 角色的动作，并保存为 VRMA。无需手工制作完整动画，也能快速为直播、视频和游戏制作所需动作。',booth:'使用 BOOTH 版（推荐） ↗',github:'查看 GitHub ↗',chips:['文字 → 动作','保存为 VRMA','面向 VRM']
    },
    ko:{
      supportTitle:'V Name을 응원해 주세요!',supportText:'V Name이 마음에 들었다면 팔로우·리포스트·좋아요로 앞으로의 업데이트를 응원해 주세요!',supportLink:'Kiratchi의 X 보기 ↗',supportNote:'응원은 선택 사항이며 등록 신청 조건이 아닙니다.',
      toolKicker:'Text-To-VRMA',toolHeading:'문장만 입력하면 AI가 VRM 캐릭터 모션을 생성합니다.',toolLead:'“손을 흔들어 줘”, “귀엽게 점프해 줘” — 원하는 움직임을 문장으로 입력하세요.',toolBody:'Text-To-VRMA는 입력한 문장에서 AI가 VRM용 모션을 생성하고 VRMA 형식으로 저장하는 도구입니다. 전문적인 애니메이션 작업 없이도 방송·영상·게임에 필요한 움직임을 만들 수 있습니다.',booth:'BOOTH 버전 사용하기 (추천) ↗',github:'GitHub 보기 ↗',chips:['문장 → 모션','VRMA 저장','VRM용']
    }
  };
  const q=(s,r=document)=>r.querySelector(s);
  function ensureCss(){
    if(q('link[data-ui-polish]'))return;
    const link=document.createElement('link');link.rel='stylesheet';link.href='ui-polish.css?v=1';link.dataset.uiPolish='true';document.head.append(link);
  }
  function mergeCommunity(){
    const register=q('#register');if(!register||register.dataset.unified==='true')return;
    const request=q('.community-card:not(.support-card)',register),support=q('.support-card',register);if(!request||!support)return;
    register.classList.add('community-actions--unified');request.classList.add('community-card--unified');
    const strip=document.createElement('div');strip.className='community-support-inline';strip.innerHTML='<div class="community-support-copy"><strong data-polish="supportTitle"></strong><p data-polish="supportText"></p><small data-polish="supportNote"></small></div>';
    const link=q('.community-button',support);if(link){link.classList.remove('primary-action');link.classList.add('community-support-link');link.dataset.polish='supportLink';strip.append(link);}
    request.append(strip);support.remove();register.dataset.unified='true';
  }
  function enhanceTool(){
    const section=q('.creator-tools'),card=q('.tool-promo');if(!section||!card||card.dataset.polished==='true')return;
    const kicker=q('.creator-tools-heading .community-kicker',section),heading=q('.creator-tools-heading h2',section),image=q('.tool-promo-image',card),body=q('.tool-promo-body',card),lead=q('.tool-promo-lead',body),paragraphs=body?[...body.querySelectorAll('p')]:[];
    if(kicker)kicker.dataset.polish='toolKicker';if(heading)heading.dataset.polish='toolHeading';if(lead)lead.dataset.polish='toolLead';
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
    document.querySelectorAll('[data-polish]').forEach(node=>{const key=node.dataset.polish;if(t[key])node.textContent=t[key];});
    document.querySelectorAll('[data-polish-chip]').forEach(node=>{node.textContent=t.chips[Number(node.dataset.polishChip)]||'';});
  }
  function init(){ensureCss();mergeCommunity();enhanceTool();applyCopy();q('#language')?.addEventListener('change',()=>queueMicrotask(applyCopy));}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
