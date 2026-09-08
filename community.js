'use strict';
window.VNameCommunity = (() => {
  function clean(row) {
    if(!row||!/^community:[a-f0-9]{64}$/.test(row.source_id||'')||row.registration_status!=='ai_screened'||row.review_model!=='gemma-4-E2B-it'||typeof row.display_name!=='string'||!row.display_name.trim()||row.display_name.length>80||/[<>\u0000-\u001f]/.test(row.display_name)||!['VTuber','AIVTuber','Vライバー'].includes(row.category))return null;
    const profile=window.VNamePlatforms.safeURL(row.source_url),activity=window.VNamePlatforms.safeURL(row.activity_source);
    if(!profile||!activity)return null;
    const account=window.VNamePlatforms.account(profile.href);
    const x=['x.com','twitter.com'].includes(profile.hostname)&&/^\/[\w]{1,15}$/.test(profile.pathname);
    if(!account&&!x)return null;
    return {source_id:row.source_id,display_name:row.display_name,category:row.category,reading:'',romanized_name:'',aliases:[],source_url:profile.href,activity_source:activity.href,platform_accounts:account?[account]:[],...(x?{official_website:profile.href}:{}),registration_status:'ai_screened',review_model:'gemma-4-E2B-it'};
  }
  async function loadAll(origin,fetcher=fetch){
    const rows=[],seen=new Set();let after=0;
    for(let page=0;page<100;page++){
      const response=await fetcher(origin+'/api/registrations?after='+after,{credentials:'omit',signal:AbortSignal.timeout(15000)});
      if(!response.ok)throw new Error('Registration data unavailable');
      const data=await response.json();if(!Array.isArray(data.records)||data.records.length>1000)throw new Error('Invalid registration data');
      for(const value of data.records){const row=clean(value);if(row&&!seen.has(row.source_id)){rows.push(row);seen.add(row.source_id);}}
      if(data.next===null)return rows;
      if(!Number.isSafeInteger(data.next)||data.next<=after)throw new Error('Invalid registration page');
      after=data.next;
    }
    throw new Error('Too many registration pages');
  }
  return {clean,loadAll};
})();

// Registration has been discontinued. No automatic network requests.

document.addEventListener('DOMContentLoaded',()=>{
  const anchor=document.querySelector('.creator-tools')||document.querySelector('#register');
  if(!anchor||document.querySelector('.data-policy-card'))return;
  const section=document.createElement('section');
  section.className='community-actions data-policy-card';
  const article=document.createElement('article');
  article.className='community-card';
  const kicker=document.createElement('span');kicker.className='community-kicker';kicker.textContent='データについて';
  const title=document.createElement('h2');title.textContent='外部名簿の一括転載は行いません';
  const body=document.createElement('div');body.className='support-message';
  const p1=document.createElement('p');p1.textContent='一般VTuber・Vライバーの新規掲載は、本人申請や本人・配信サービス・所属先の個別公開プロフィールを確認して反映します。第三者DB・ランキング・配信者一覧をそのまま大量に公開辞書へ追加する運用は停止しています。';
  const p2=document.createElement('p');p2.textContent='既存データには過去の公開名簿等を参考にしたレコードが含まれるため、出典を残しながら個別再確認を進めています。';
  const link=document.createElement('a');link.className='community-button';link.href='DATA_SOURCES.md';link.textContent='取得元と確認方針を見る →';
  body.append(p1,p2);article.append(kicker,title,body,link);section.append(article);anchor.before(section);
});
