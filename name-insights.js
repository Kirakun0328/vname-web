'use strict';
window.VNameInsights = (() => {
  const top=(map,n=10)=>[...map.entries()].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0],'ja')).slice(0,n).map(([label,count])=>({label,count}));
  function analyze(rows) {
    const lengths=new Map(), characters=new Map(), pairs=new Map(), scripts=new Map();
    let totalLength=0;
    for(const r of rows){
      const name=String(r.display_name||'').normalize('NFKC').replace(/\s/g,'');
      const chars=[...name];const size=chars.length;totalLength+=size;
      const bucket=size<=4?'1〜4文字':size<=8?'5〜8文字':size<=12?'9〜12文字':'13文字以上';
      lengths.set(bucket,(lengths.get(bucket)||0)+1);
      const types=[[/\p{Script=Han}/u,'漢字'],[/\p{Script=Hiragana}/u,'ひらがな'],[/\p{Script=Katakana}/u,'カタカナ'],[/[A-Za-z]/,'英字']].filter(([re])=>re.test(name)).map(([,label])=>label);
      const composition=types.length>1?'複数の文字種':types[0]||'数字・その他';scripts.set(composition,(scripts.get(composition)||0)+1);
      // Count records containing a character/pair, not repeated occurrences.
      for(const c of new Set(chars.filter(c=>/\p{Script=Han}/u.test(c))))characters.set(c,(characters.get(c)||0)+1);
      const seen=new Set();for(let i=0;i<chars.length-1;i++)if(/^\p{Script=Han}{2}$/u.test(chars[i]+chars[i+1]))seen.add(chars[i]+chars[i+1]);
      for(const pair of seen)pairs.set(pair,(pairs.get(pair)||0)+1);
    }
    return {total:rows.length,averageLength:rows.length?Number((totalLength/rows.length).toFixed(1)):0,
      lengths:['1〜4文字','5〜8文字','9〜12文字','13文字以上'].map(label=>({label,count:lengths.get(label)||0})),
      scripts:top(scripts,6),characters:top(characters),pairs:top(pairs)};
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
      if(reply){try{return{valid:true,structured:false,reply:JSON.parse(reply[1]),suggestions:[]};}catch{}}
      return{valid:false,reply:'回答が途中で終わりました。条件を短くして、もう一度相談してください。',suggestions:[]};
    }
    if(!value||typeof value!=='object')return{valid:false,reply:'回答を受け取れませんでした。PCで条件を短くして、もう一度お試しください。',suggestions:[]};
    const suggestions=[],seen=new Set();
    for(const item of Array.isArray(value.suggestions)?value.suggestions:[]){
      if(!item||typeof item.name!=='string')continue;
      const name=item.name.trim();if(!name||[...name].length>40||/[\u0000-\u001f]/.test(name)||seen.has(name))continue;
      seen.add(name);suggestions.push({name,reading:typeof item.reading==='string'?item.reading.slice(0,60):'',reason:typeof item.reason==='string'?item.reason.slice(0,400):''});if(suggestions.length===5)break;
    }
    return {valid:true,structured:true,reply:typeof value.reply==='string'?value.reply.slice(0,3500):'候補を考えました。',suggestions};
  }
  function prompt(stats,language='ja') {
    const languages={ja:'日本語',en:'English',zh:'简体中文',ko:'한국어'};
    return `あなたは「ぶいネーム」のVTuber・AIVTuber・Vライバー向け名前相談アシスタントです。ユーザーのモチーフ、雰囲気、読みやすさ、覚えやすさ、配信媒体、海外での呼びやすさを考え、対話で名前を一緒に考えてください。人間・AIキャラクター両方に対応します。希望が曖昧なら少数の仮案と短い質問を出してください。回答言語は${languages[language]||languages.ja}です。
次の辞書集計は現在の収録レコードの統計です。国・言語・収集元に偏りがあり、時系列・人気・売上・視聴者数のデータはありません。「最近流行」「人気が出る」などを統計から断定しないでください。アバター配信者以外のチャンネル・グループ名を含む場合があります。漢字集計には日本語以外も含まれます。
辞書集計: ${JSON.stringify(stats)}
候補の重複チェックはアプリが辞書を実際に検索します。あなた自身は候補が未使用・安全であると断定しないでください。読みは候補として提案してください。既存の有名人の名前をそのまま提案しないでください。
回答は必ずJSONオブジェクトのみ。形式は {"reply":"短い相談への回答や傾向の説明","suggestions":[{"name":"候補名","reading":"候補の読み","reason":"その名前が希望に合う理由"}]}。名前案は3件まで、各理由は短い1文。replyは150文字程度にまとめてください。説明だけ求められたらsuggestionsを空配列にできます。マークダウンのコードフェンスは不要です。`;
  }
  return {analyze,parseReply,prompt};
})();
