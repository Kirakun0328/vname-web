'use strict';
(() => {
  const BOOTH_URL='https://booth.pm/ja/items/8617663';
  const GITHUB_URL='https://github.com/Kirakun0328/text-to-vrma';
  const copy={
    ja:{
      supportTitle:'ぶいネームを応援',supportText:'フォロー・RP・いいねで応援してもらえると、今後の更新の励みになります！',supportLink:'きらっちのXを見る ↗',supportNote:'応援は任意です。申請・掲載の条件ではありません。',
      toolKicker:'開発者ツール',toolHeading:'VRMキャラクターを、文章ひとつで動かす。',toolLead:'「手を振って」「かわいくジャンプ」——文章から、そのままキャラクターの動きへ。',toolBody:'Text-To-VRMAは、入力した文章からAIがVRM向けモーションを考えて生成し、VRMA形式で保存できるツールです。配信・動画・ゲーム制作の「この動きがほしい」を、専門的なアニメーション作業なしで形にできます。',toolBadge:'BOOTH版がおすすめ',booth:'BOOTH版を使う ↗',github:'GitHubを見る ↗',chips:['文章 → モーション','VRMAで保存','VRM向け']
    },
    en:{
      supportTitle:'Support V Name',supportText:'Follows, reposts, and likes help support future updates!',supportLink:'View Kiratchi on X ↗',supportNote:'Support is optional and is not required for listing requests.',
      toolKicker:'CREATOR TOOL',toolHeading:'Move your VRM character with just a sentence.',toolLead:'“Wave your hand.” “Do a cute jump.” Turn words directly into character motion.',toolBody:'Text-To-VRMA uses AI to generate motion for VRM characters from text and saves it as VRMA. Create the motions you want for streaming, videos, or games without doing full animation work by hand.',toolBadge:'BOOTH recommended',booth:'Get the BOOTH version ↗',github:'View on GitHub ↗',chips:['Text → Motion','Save as VRMA','Made for VRM']
    },
    zh:{
      supportTitle:'支持 V Name',supportText:'关注、转发和点赞都会成为持续更新的动力！',supportLink:'查看 Kiratchi 的 X ↗',supportNote:'支持完全自愿，不是申请收录的条件。',
      toolKicker:'开发者工具',toolHeading:'只需一句话，让 VRM 角色动起来。',toolLead:'“挥挥手”“可爱地跳一下”——把文字直接变成角色动作。',toolBody:'Text-To-VRMA 可根据输入文字用 AI 生成适用于 VRM 角色的动作，并保存为 VRMA。无需手工制作完整动画，也能快速为直播、视频和游戏制作所需动作。',toolBadge:'推荐 BOOTH 版',booth:'使用 BOOTH 版 ↗',github:'查看 GitHub ↗',chips:['文字 → 动作','保存为 VRMA','面向 VRM']
    },
    ko:{
      supportTitle:'V Name 응원하기',supportText:'팔로우·리포스트·좋아요는 앞으로의 업데이트에 큰 힘이 됩니다!',supportLink:'Kiratchi의 X 보기 ↗',supportNote:'응원은 선택 사항이며 등록 신청 조건이 아닙니다.',
      toolKicker:'개발자 도구',toolHeading:'문장 하나로 VRM 캐릭터를 움직이세요.',toolLead:'“손을 흔들어 줘”, “귀엽게 점프해 줘” — 문장을 바로 캐릭터 모션으로.',toolBody:'Text-To-VRMA는 입력한 문장에서 AI가 VRM용 모션을 생성하고 VRMA 형식으로 저장하는 도구입니다. 전문적인 애니메이션 작업 없이도 방송·영상·게임에 필요한 움직임을 만들 수 있습니다.',toolBadge:'BOOTH 버전 추천',booth:'BOOTH 버전 사용하기 ↗',github:'GitHub 보기 ↗',chips:['문장 → 모션','VRMA 저장','VRM용']
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
    const strip=document.createElement('div');strip.className='community-support-inline';strip.innerHTML='<div class="community-support-copy"><strong data-polish="support-title"></strong><p data-polish="support-text"></p><small data-polish="support-note"></small></div>';
    const link=q('.community-button',support);if(link){link.classList.remove('primary-action');link.classList.add('community-support-link');link.dataset.polish='support-link';strip.append(link);}
    request.append(strip);support.remove();register.dataset.unified='true';
  }
  function enhanceTool(){
    const section=q('.creator-tools'),card=q('.tool-promo');if(!section||!card||card.dataset.polished==='true')return;
    const kicker=q('.creator-tools-heading .community-kicker',section),heading=q('.creator-tools-heading h2',section),image=q('.tool-promo-image',card),body=q('.tool-promo-body',card),lead=q('.tool-promo-lead',body),paragraphs=body?[...body.querySelectorAll('p')]:[];
    if(kicker)kicker.dataset.polish='tool-kicker';if(heading)heading.dataset.polish='tool-heading';if(lead)lead.dataset.polish='tool-lead';
    const bodyText=paragraphs.find(p=>!p.classList.contains('tool-promo-lead'));if(bodyText)bodyText.dataset.polish='tool-body';
    if(image){image.href=BOOTH_URL;image.setAttribute('aria-label','Text-To-VRMAのBOOTHページを開く');}
    const existing=q('.community-button',body);if(existing){existing.href=BOOTH_URL;existing.dataset.polish='booth';existing.classList.add('tool-booth-button');}
    const chips=document.createElement('div');chips.className='tool-feature-chips';chips.innerHTML='<span data-polish-chip="0"></span><span data-polish-chip="1"></span><span data-polish-chip="2"></span>';
    const badge=document.createElement('span');badge.className='tool-recommend';badge.dataset.polish='tool-badge';
    const github=document.createElement('a');github.className='community-button tool-github-button';github.href=GITHUB_URL;github.target='_blank';github.rel='noopener noreferrer';github.dataset.polish='github';
    const actions=document.createElement('div');actions.className='tool-promo-actions';if(existing)actions.append(existing);actions.append(github);
    if(bodyText){bodyText.after(chips,badge,actions);}else if(body){body.append(chips,badge,actions);}
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
