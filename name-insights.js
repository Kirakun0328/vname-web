'use strict';
window.VNameInsights = (() => {
  const top=(map,n=10)=>[...map.entries()].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0],'ja')).slice(0,n).map(([label,count])=>({label,count}));
  function analyze(rows) {
    const lengths=new Map(), exactLengths=new Map(), characters=new Map(), pairs=new Map(), scripts=new Map(), prefixes=new Map(), suffixes=new Map();
    const sizes=[],names=new Map(),ngrams2=new Map(),ngrams3=new Map(),kanaCharacters=new Map(),readingLengths=new Map(),readingStatus=new Map();
    let totalLength=0;
    for(const r of rows){
      const name=String(r.display_name||'').normalize('NFKC').replace(/\s/g,'');
      const identity=name.toLocaleLowerCase();names.set(identity,{label:names.get(identity)?.label||name,count:(names.get(identity)?.count||0)+1});
      for(const [width,map] of [[2,ngrams2],[3,ngrams3]]){const seen=new Set();const points=[...name];for(let i=0;i<=points.length-width;i++){const word=points.slice(i,i+width).join('');if(/^[\p{L}\p{N}]+$/u.test(word))seen.add(word);}for(const word of seen)map.set(word,(map.get(word)||0)+1);}
      for(const c of new Set([...name].filter(c=>/[ぁ-ゖァ-ヶ]/u.test(c))))kanaCharacters.set(c,(kanaCharacters.get(c)||0)+1);
      const status=r.reading?(r.reading_inferred?'推定の読み':'確認済みの読み'):'読み未確認';readingStatus.set(status,(readingStatus.get(status)||0)+1);
      if(r.reading){const length=[...r.reading.replace(/\s/g,'')].length;const label=length<=4?'1〜4文字':length<=8?'5〜8文字':length<=12?'9〜12文字':'13文字以上';readingLengths.set(label,(readingLengths.get(label)||0)+1);}
      const chars=[...name];const size=chars.length;totalLength+=size;sizes.push(size);exactLengths.set(size,(exactLengths.get(size)||0)+1);
      if(size>=2)for(const [map,label] of [[prefixes,chars.slice(0,2).join('')],[suffixes,chars.slice(-2).join('')]])if(/^[\p{L}\p{N}]{2}$/u.test(label))map.set(label,(map.get(label)||0)+1);
      const bucket=size<=4?'1〜4文字':size<=8?'5〜8文字':size<=12?'9〜12文字':'13文字以上';
      lengths.set(bucket,(lengths.get(bucket)||0)+1);
      const types=[[/\p{Script=Han}/u,'漢字'],[/\p{Script=Hiragana}/u,'ひらがな'],[/\p{Script=Katakana}/u,'カタカナ'],[/[A-Za-z]/,'英字']].filter(([re])=>re.test(name)).map(([,label])=>label);
      const composition=types.length>1?'複数の文字種':types[0]||'数字・その他';scripts.set(composition,(scripts.get(composition)||0)+1);
      // Count records containing a character/pair, not repeated occurrences.
      for(const c of new Set(chars.filter(c=>/\p{Script=Han}/u.test(c))))characters.set(c,(characters.get(c)||0)+1);
      const seen=new Set();for(let i=0;i<chars.length-1;i++)if(/^\p{Script=Han}{2}$/u.test(chars[i]+chars[i+1]))seen.add(chars[i]+chars[i+1]);
      for(const pair of seen)pairs.set(pair,(pairs.get(pair)||0)+1);
    }
    sizes.sort((a,b)=>a-b);const middle=Math.floor(sizes.length/2);
    const medianLength=sizes.length?(sizes.length%2?sizes[middle]:(sizes[middle-1]+sizes[middle])/2):0;
    const commonLengths=[...exactLengths.entries()].sort((a,b)=>b[1]-a[1]||a[0]-b[0]).slice(0,5).map(([length,count])=>({length,count}));
    const duplicateNames=[...names.values()].filter(x=>x.count>1).sort((a,b)=>b.count-a.count||a.label.localeCompare(b.label,'ja'));
    return {uniqueNames:names.size,duplicateGroups:duplicateNames.length,duplicateRecords:duplicateNames.reduce((n,r)=>n+r.count,0),duplicateNames:duplicateNames.slice(0,20),ngrams2:top(ngrams2,20),ngrams3:top(ngrams3,20),kanaCharacters:top(kanaCharacters,20),readingStatus:top(readingStatus,3),readingLengths:top(readingLengths,4),readable:rows.filter(r=>r.reading).length,total:rows.length,averageLength:rows.length?Number((totalLength/rows.length).toFixed(1)):0,medianLength,commonLengths,exactLengths:Object.fromEntries(exactLengths),
      lengths:['1〜4文字','5〜8文字','9〜12文字','13文字以上'].map(label=>({label,count:lengths.get(label)||0})),
      scripts:top(scripts,6),characters:top(characters),pairs:top(pairs),prefixes:top(prefixes).filter(r=>r.count>1),suffixes:top(suffixes).filter(r=>r.count>1)};
  }
  function compare(rows,groups){
    const values=new Map();
    for(const row of rows)for(const group of new Set(groups(row))){if(!values.has(group))values.set(group,[]);values.get(group).push(row);}
    return [...values].map(([label,items])=>{const sizes=items.map(r=>[...r.display_name.normalize('NFKC').replace(/\s/g,'')].length);return {label,count:items.length,averageLength:Number((sizes.reduce((a,b)=>a+b,0)/items.length).toFixed(1)),kanaPercent:Number((items.filter(r=>/[ぁ-ゖァ-ヶ]/u.test(r.display_name.normalize('NFKC'))).length/items.length*100).toFixed(1))};}).sort((a,b)=>b.count-a.count||a.label.localeCompare(b.label,'ja'));
  }
  function normalizeSuggestions(items){
    const suggestions=[],seen=new Set();
    for(let item of Array.isArray(items)?items:[]){
      if(typeof item==='string')item={name:item};
      if(!item||typeof item.name!=='string')continue;
      const name=item.name.trim();if(!name||[...name].length>40||/[\u0000-\u001f]/.test(name)||seen.has(name))continue;
      seen.add(name);suggestions.push({name,reading:typeof item.reading==='string'?item.reading.slice(0,60):'',reason:typeof item.reason==='string'?item.reason.slice(0,400):''});if(suggestions.length===5)break;
    }
    return suggestions;
  }
  // Recover only fully closed array items. An unfinished name object is never
  // completed or invented by the app when a small model reaches its limit.
  function partialArray(text){
    const match=/"(?:suggestions|candidates|names)"\s*:\s*\[/.exec(text);if(!match)return [];
    const items=[];let start=-1,depth=0,quoted=false,escaped=false;
    const save=end=>{try{items.push(JSON.parse(text.slice(start,end)));}catch{}start=-1;};
    for(let i=match.index+match[0].length;i<text.length;i++){
      const c=text[i];
      if(start<0){if(c===']')break;if(/[\s,]/.test(c))continue;start=i;}
      if(quoted){if(escaped)escaped=false;else if(c==='\\')escaped=true;else if(c==='"'){quoted=false;if(depth===0)save(i+1);}continue;}
      if(c==='"'){quoted=true;continue;}
      if(c==='{'||c==='[')depth++;
      else if(c==='}'||c===']'){if(depth===0)break;if(--depth===0)save(i+1);}
      else if(c===','&&depth===0)save(i);
    }
    return items;
  }
  function parseReply(raw) {
    let value;
    const clean=String(raw||'').replace(/^\s*```(?:json)?\s*/,'').replace(/\s*```\s*$/,'').trim();
    if(!clean||['null','undefined','[]'].includes(clean))return {valid:false,reply:'回答を受け取れませんでした。PCで条件を短くして、もう一度お試しください。',suggestions:[]};
    try{value=JSON.parse(clean.slice(clean.indexOf('{'),clean.lastIndexOf('}')+1));}catch{
      // Small models may answer in prose or run out of output tokens inside JSON.
      // Preserve a useful answer instead of treating formatting as an inference failure.
      if(!clean.startsWith('{'))return{valid:true,structured:false,reply:clean.slice(0,6000),suggestions:[]};
      const reply=clean.match(/"reply"\s*:\s*("(?:[^"\\]|\\.)*")/s);
      const suggestions=normalizeSuggestions(partialArray(clean));
      if(reply||suggestions.length){try{return{valid:true,structured:!!suggestions.length,incomplete:true,reply:reply?JSON.parse(reply[1]):'生成できた名前の候補です。',suggestions,nextPrompts:[]};}catch{}}
      return{valid:false,reply:'回答が途中で終わりました。条件を短くして、もう一度相談してください。',suggestions:[]};
    }
    if(!value||typeof value!=='object')return{valid:false,reply:'回答を受け取れませんでした。PCで条件を短くして、もう一度お試しください。',suggestions:[]};
    const suggestions=normalizeSuggestions(value.suggestions||value.candidates||value.names);
    const nextPrompts=[...new Set((Array.isArray(value.next_prompts)?value.next_prompts:[]).filter(s=>typeof s==='string').map(s=>s.trim()).filter(s=>s&&[...s].length<=60&&!/[\u0000-\u001f]/.test(s)))].slice(0,3);
    const valid=!!(suggestions.length||nextPrompts.length||(typeof value.reply==='string'&&value.reply.trim()));
    return {valid,structured:true,reply:typeof value.reply==='string'?value.reply.slice(0,3500):suggestions.length?'候補を考えました。':'回答を確認できませんでした。',suggestions,nextPrompts};
  }
  function wantsNames(input,hasPrevious=false){
    if(/(?:分析|傾向|統計|説明|analysis|statistics|趋势|분석).{0,12}(?:だけ|のみ|only|就好|만)|(?:名前|候補).{0,8}(?:不要|いらない)|(?:no|without)\s+(?:name\s+)?suggestions/i.test(input))return false;
    return /(?:名前|候補|活動名|名付け|命名|ネーミング).{0,35}(?:欲|ほし|考|案|作|出|探|お願い)|(?:考|提案|作|出).{0,20}(?:名前|候補)|(?:name|naming).{0,25}(?:idea|suggest|creat|want)|(?:suggest|creat|want|give).{0,25}names?|起名|取名|名字.{0,10}(?:想|建议)|이름.{0,15}(?:추천|지어|만들|생각)/is.test(input)||(hasPrevious&&!/傾向|分析|統計|説明|why|analysis|statistics|趋势|분석/i.test(input));
  }
  function parseRepair(raw){
    const parsed=parseReply(raw);if(parsed.suggestions.length)return parsed;
    const items=String(raw||'').split('\n').map(line=>line.trim().replace(/^(?:[-*]\s+|\d+[.)、]\s*)/,'').replace(/^\||\|$/g,'').split(/[|｜\t]/).map(s=>s.trim().replace(/^\*\*|\*\*$/g,'')))
      .filter(c=>c.length===3&&!/^(?:名前|候補名|name|name idea|名字|이름|[-:]+)$/i.test(c[0])&&c[0]&&c[2]).map(([name,reading,reason])=>({name,reading,reason}));
    const suggestions=normalizeSuggestions(items);
    return suggestions.length?{valid:true,structured:true,reply:'希望に合わせた名前の候補です。',suggestions,nextPrompts:[]}:parsed;
  }
  function prompt(stats,language='ja') {
    const languages={ja:'日本語',en:'English',zh:'简体中文',ko:'한국어'};
    return `あなたは「ぶいネーム」のVTuber・AIVTuber・Vライバー向け名前相談アシスタントです。主な利用者は、これから活動を始めたいが名前が決まらない人です。方向性が固まっていなくても少数の具体案を出し、選びやすく手伝ってください。ユーザーのモチーフ、雰囲気、読みやすさ、覚えやすさ、配信媒体、海外での呼びやすさを考え、対話で名前を一緒に考えてください。人間・AIキャラクター両方に対応します。希望が曖昧なら少数の仮案と短い質問を出してください。回答言語は${languages[language]||languages.ja}です。
次の辞書集計は選択された媒体・タグ・表記の収録レコードの統計です。国・言語・収集元に偏りがあり、時系列・人気・売上・視聴者数のデータはありません。「最近流行」「人気が出る」などを統計から断定しないでください。アバター配信者以外のチャンネル・グループ名を含む場合があります。漢字集計には日本語以外も含まれます。prefixes/suffixesは表示名の先頭/末尾2文字で、苗字や語源の分類ではありません。
辞書集計: ${JSON.stringify({...stats,exactLengths:undefined})}
分析を求められたら、集計対象と件数を踏まえ、文字数・文字種・よく使われる文字の具体的な数値を挙げて説明してください。提案では「辞書で多い特徴」と「ユーザーの希望に合う理由」を分けて考え、上位の文字を使う案だけに偏らないでください。未掲載者もいるため、低頻度を独自性の保証にしないでください。
候補の重複チェックはアプリが辞書を実際に検索します。あなた自身は候補が未使用・安全であると断定しないでください。読みは候補として提案してください。既存の有名人の名前をそのまま提案しないでください。
回答は必ずJSONオブジェクトのみ。名前を求められた場合、説明より先に具体的な名前をsuggestionsへ必ず入れてください。「提案します」という予告だけでは回答になりません。形式は {"suggestions":[{"name":"候補名","reading":"候補の読み","reason":"希望に合う理由を短く1文"}],"reply":"短い回答や数値に基づく傾向の説明","next_prompts":["ユーザーが次に送れる相談文"]}。名前案は3件、各理由は40文字程度。replyは100文字程度。説明・分析だけの依頼ではsuggestionsを空にできます。next_promptsは会話に合う次の相談文を2件まで、各60文字以内で生成。マークダウンのコードフェンスは不要です。`;
  }
  return {analyze,compare,parseReply,parseRepair,wantsNames,prompt};
})();
