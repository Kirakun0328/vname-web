'use strict';
// Primary platforms require an explicit source; linked accounts never imply primacy.
window.VNamePlatforms = (() => {
  const labels = {youtube:'YouTube', tiktok:'TikTok LIVE', iriam:'IRIAM', avvy:'Avvy', reality:'REALITY', twitch:'Twitch', '17live':'17LIVE', showroom:'SHOWROOM', twitcasting:'ツイキャス', niconico:'ニコニコ', mirrativ:'Mirrativ', bilibili:'bilibili', spoon:'Spoon', kick:'Kick', soop:'SOOP', topia:'topia', palmu:'Palmu', mixch:'ミクチャ', bigo:'BIGO LIVE', acfun:'AcFun', whowatch:'ふわっち', pococha:'Pococha', colorsing:'ColorSing', pikapika:'ピカピカ', everylive:'everylive', standfm:'stand.fm', radiotalk:'Radiotalk', openrec:'mellow-fan（旧OPENREC.tv）', pokekara:'Pokekara', instagram:'Instagram Live', facebook:'Facebook Live', chzzk:'CHZZK', rplay:'RPLAY'};
  const hosts = {'youtube.com':'youtube','m.youtube.com':'youtube','tiktok.com':'tiktok','twitch.tv':'twitch','m.twitch.tv':'twitch','s.avvy.live':'avvy','web.iriam.app':'iriam','reality.app':'reality','17.live':'17live','showroom-live.com':'showroom','twitcasting.tv':'twitcasting','nicovideo.jp':'niconico','com.nicovideo.jp':'niconico','mirrativ.com':'mirrativ','space.bilibili.com':'bilibili','spooncast.net':'spoon','kick.com':'kick','ch.sooplive.co.kr':'soop','bj.afreecatv.com':'soop','user.topia.tv':'topia','palmu.me':'palmu','mixch.tv':'mixch','bigo.tv':'bigo','acfun.cn':'acfun','topia.tv':'topia','whowatch.tv':'whowatch','pococha.com':'pococha','web.colorsing.com':'colorsing','pikapika.live':'pikapika','stand.fm':'standfm','radiotalk.jp':'radiotalk','openrec.tv':'openrec','mellow-fan.com':'openrec','u.pokekara.com':'pokekara','instagram.com':'instagram','facebook.com':'facebook','sp.nicovideo.jp':'niconico','cas.nicovideo.jp':'niconico','app.palmu.jp':'palmu','chzzk.naver.com':'chzzk','m.chzzk.naver.com':'chzzk','rplay.live':'rplay'};
  function safeURL(value) {
    try {const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password&&!u.port?u:null;} catch {return null;}
  }
  function account(value) {
    const u=safeURL(value);if(!u)return null;
    const host=u.hostname.replace(/^www\./,'');
    if(host==='mirrativ.page.link'){const target=safeURL(u.searchParams.get('link'));return target&&['mirrativ.com','www.mirrativ.com'].includes(target.hostname)?account(target.href):null;}
    const platform=hosts[host];if(!platform)return null;
    let path;try{path=decodeURIComponent(u.pathname);}catch{return null;}
    if(platform==='youtube'&&/^\/@[\p{L}\p{N}\p{M}_.·\-]+\/?$/u.test(path))u.pathname=path.toLowerCase();
    else if(platform==='youtube'&&!/^\/channel\/UC[\w-]{22}\/?$/.test(path))return null;
    const patterns={youtube:/^\/(?:channel\/UC[\w-]{22}|@[\w.\-]+)\/?$/,tiktok:/^\/@[\w.\-]+(?:\/live)?\/?$/,twitch:/^\/[\w]+\/?$/,avvy:/^\/u\/[0-9a-hjkmnp-tv-z]{26}\/?$/,iriam:/^\/s\/user\/[^/]+\/?$/,reality:/^\/profile\/[^/]+\/?$/,'17live':/^\/(?:s\/u|(?:[a-z]{2}\/)?profile)\/[^/]+\/?$/,showroom:/^\/(?:r\/)?[\w-]+\/?$/,twitcasting:/^\/[\w:.-]+\/?$/,niconico:/^\/(?:user\/\d+|community\/co\d+)\/?$/,mirrativ:/^\/user\/\d+\/?$/,bilibili:/^\/\d+\/?$/,spoon:/^\/(?:[a-z]{2}\/)?(?:profile\/[^/]+|channel\/\d+(?:\/tab\/home)?)\/?$/,kick:/^\/[\w-]+\/?$/,soop:/^\/[\w-]+\/?$/,topia:/^\/(?:p\/)?[\w-]+\/?$/,palmu:/^\/users\/[^/]+\/?$/,mixch:/^\/u\/\d+\/?$/,bigo:/^\/[\w-]+\/?$/,acfun:/^\/u\/\d+\/?$/,whowatch:/^\/profile\/w:[\w.-]+\/?$/,pococha:/^\/app\/users\/[\w-]+\/?$/,pikapika:/^\/index\/roomuser\/uid\/\d+\/?$/,standfm:/^\/channels\/[a-f0-9]{24}\/?$/,radiotalk:/^\/program\/\d+\/?$/,openrec:/^\/(?:m\/)?user\/[\w-]+\/?$/,pokekara:/^\/user\/\d+\/?$/,instagram:/^\/[\w.]+\/?$/,facebook:/^\/[\w.]+\/?$/,chzzk:/^\/[a-f0-9]{32}\/?$/,rplay:/^\/(?:c\/[\w.-]+|creatorhome\/[a-f0-9]{24})\/?$/};
    if(platform==='colorsing'){const id=u.searchParams.get('user_id')||'';return path==='/share/user'&&/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(id)?{platform,url:'https://web.colorsing.com/share/user?user_id='+id}:null;}
    if(platform==='topia'&&!(host==='topia.tv'?/^\/p\/[\w-]+\/?$/:/^\/[\w-]+\/?$/).test(path))return null;
    if(platform==='iriam'&&path==='/s/user'&&/^[\w-]+$/.test(u.searchParams.get('id')||'')){
      return {platform,url:'https://web.iriam.app/s/user?id='+encodeURIComponent(u.searchParams.get('id'))};
    }
    if((platform!=='youtube'&&!patterns[platform]?.test(path))||/^\/(?:home|directory|explore|search|login|signup)\/?$/.test(u.pathname))return null;
    u.hostname=platform==='youtube'?'www.youtube.com':platform==='twitch'?'www.twitch.tv':platform==='tiktok'?'www.tiktok.com':platform==='soop'?'ch.sooplive.co.kr':host;
    if(['tiktok','twitch','kick','soop','twitcasting'].includes(platform))u.pathname=u.pathname.toLowerCase();
    if(platform==='tiktok')u.pathname=u.pathname.replace(/\/live\/?$/,'');
    if(platform==='niconico'&&/^\/user\//.test(path))u.hostname='www.nicovideo.jp';
    u.hash='';u.search='';return {platform,url:u.href.replace(/\/$/,'')};
  }
  function details(r) {
    const linked=new Map();
    const add=value=>{const a=account(value);if(a)linked.set(a.platform+' '+a.url,a);};
    for(const a of r.platform_accounts||[])add(a.url);
    for(const f of ['source_url','broadcast_url','twitch_url','youtube_url'])add(r[f]);
    if(/^[a-zA-Z0-9_]+$/.test(r.twitch_login||''))add('https://www.twitch.tv/'+r.twitch_login);
    if(r.youtube_handle?.startsWith('@'))add('https://www.youtube.com/'+r.youtube_handle);
    const cid=r.youtube_channel_id||(r.source_id.startsWith('youtube:')?r.source_id.slice(8):'');
    if(/^UC[\w-]{22}$/.test(cid))add('https://www.youtube.com/channel/'+cid);
    // These two fields are the channel/handle pair supplied by a profile source.
    // Do not collapse arbitrary channels merely because they share a platform.
    const handle=account('https://www.youtube.com/'+(r.youtube_handle||''));
    const channelLinks=[...linked.values()].filter(a=>a.platform==='youtube'&&new URL(a.url).pathname.startsWith('/channel/'));
    if(channelLinks.length===1&&/^UC[\w-]{22}$/.test(cid)&&handle)linked.delete('youtube '+handle.url);
    const known=new Set([...linked.values()].map(a=>a.platform));
    for(const p of r.platforms||[])if(labels[p]&&safeURL(r.platform_sources?.[p]))known.add(p);
    const primarySource=safeURL(r.primary_platform_source);
    const primary=primarySource&&r.primary_platform_evidence?[...new Set((r.primary_platforms||[]).filter(p=>labels[p]))]:[];
    primary.forEach(p=>known.add(p));
    const accounts=[...linked.values()].map(a=>({...a,label:labels[a.platform]}));
    const groups=[...new Set(accounts.map(a=>a.platform))].map(platform=>({platform,label:labels[platform],accounts:accounts.filter(a=>a.platform===platform)}));
    return {primary:primary.map(p=>labels[p]),primarySource:primary.length?primarySource.href:'',known:[...known].map(p=>labels[p]),accounts,groups};
  }
  return {labels,details,account,safeURL};
})();
