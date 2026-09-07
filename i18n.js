'use strict';
const translations={
  "en": {
    "ぶいネーム": "VName",
    "VTuber名前チェック": "VTuber Name Checker",
    "その名前、もう使われてる？": "Is that name already taken?",
    "名前・読み・英字から、同じ名前や似た名前をチェック。": "Find matching VTuber names, readings, and aliases.",
    "名前を入力": "Enter a name",
    "調べたい名前": "Name to check",
    "ひらがな・カタカナ・英字でもOK": "Japanese, English, and other name variants welcome",
    "名前を調べる": "Check name",
    "試してみる": "Try an example",
    "入力した名前は外部に送信されません。": "Your search stays on your device.",
    "チェック結果": "Search results",
    "名前を入力して「名前を調べる」を押してください。": "Enter a name and select “Check name”.",
    "気になる名前から、調べてみよう": "Start with a name you have in mind",
    "一致した名前と、その読み・英字を表示します。": "Matching names, readings, and aliases appear here.",
    "前へ": "Previous",
    "次へ": "Next",
    "一致がなくても、名前が未使用とは限りません。読み・英字には機械変換による参考情報を含みます。": "No match does not guarantee a name is unused. Some readings and romanizations are machine-generated.",
    "データと読みについて": "About the data and readings",
    "収集元：VTuber Database・VTuber Post／収集日：2026年9月7日。未収録の名前やグループ・チャンネル名も含まれます。一部ページは取得に失敗しています。": "Sources: VTuber Database and VTuber Post. Collected September 7, 2026. Coverage is incomplete and may include groups or channels. Some pages could not be retrieved.",
    "確認できた名前は個別の読みを優先します。補正の出典：": "Individual corrections take priority. Correction source:",
    "ホロライブ公式タレント一覧": "Official hololive talent list",
    "。全件の読みを確認した辞書ではありません。": ". Not all readings have been verified.",
    "表示名が一致": "Exact display name",
    "読み・英字が一致": "Matching reading or alias",
    "名前の一部が一致": "Partial name match",
    "読み": "Reading",
    "英字": "English / romanization",
    "別名": "Other names",
    "不明": "Unknown",
    "個別補正済み": "Individually corrected",
    "読み・英字は参考情報（機械変換を含む）": "Readings and romanizations are reference information (may be machine-generated)",
    "文字を含む名前を入力してください。": "Please enter a name containing letters or numbers.",
    "この辞書では一致する名前が見つかりませんでした。未使用を保証する結果ではありません。": "No matching names in this dictionary. This does not guarantee the name is unused.",
    "辞書を読み込めませんでした。ページを再読み込みしてください。": "Could not load the dictionary. Please reload the page.",
    "名前を検索": "Search names",
    "検索結果": "Search results",
    "検索結果のページ": "Result pages",
    "例：兎田ぺこら": "e.g. Usada Pekora",
    "ぶいネーム｜VTuber名前チェック": "VName | VTuber Name Checker",
    "辞書を読み込んでいます…": "Loading dictionary…"
  },
  "zh": {
    "ぶいネーム": "VName",
    "VTuber名前チェック": "VTuber名称查询",
    "その名前、もう使われてる？": "这个名字已经有人用了吗？",
    "名前・読み・英字から、同じ名前や似た名前をチェック。": "搜索相同或相似的名字、读音和别名。",
    "名前を入力": "输入名字",
    "調べたい名前": "想查询的名字",
    "ひらがな・カタカナ・英字でもOK": "支持日语、英语及其他名字写法",
    "名前を調べる": "查询名字",
    "試してみる": "试一试",
    "入力した名前は外部に送信されません。": "输入的名字不会发送到外部。",
    "チェック結果": "查询结果",
    "名前を入力して「名前を調べる」を押してください。": "输入名字后，点击“查询名字”。",
    "気になる名前から、調べてみよう": "先查一下你喜欢的名字",
    "一致した名前と、その読み・英字を表示します。": "这里会显示匹配的名字、读音和别名。",
    "前へ": "上一页",
    "次へ": "下一页",
    "一致がなくても、名前が未使用とは限りません。読み・英字には機械変換による参考情報を含みます。": "没有匹配结果不代表名字未被使用。部分读音和罗马字为机器转换结果。",
    "データと読みについて": "关于数据与读音",
    "収集元：VTuber Database・VTuber Post／収集日：2026年9月7日。未収録の名前やグループ・チャンネル名も含まれます。一部ページは取得に失敗しています。": "来源：VTuber Database、VTuber Post。采集日期：2026年9月7日。数据并不完整，可能包含团体或频道。部分页面未能获取。",
    "確認できた名前は個別の読みを優先します。補正の出典：": "优先使用已单独修正的读音。修正来源：",
    "ホロライブ公式タレント一覧": "hololive官方艺人列表",
    "。全件の読みを確認した辞書ではありません。": "。并非所有读音都经过核实。",
    "表示名が一致": "显示名称完全一致",
    "読み・英字が一致": "读音或别名一致",
    "名前の一部が一致": "名字部分匹配",
    "読み": "读音",
    "英字": "英文／罗马字",
    "別名": "别名",
    "不明": "未知",
    "個別補正済み": "已单独修正",
    "読み・英字は参考情報（機械変換を含む）": "读音和罗马字仅供参考（可能包含机器转换）",
    "文字を含む名前を入力してください。": "请输入包含文字或数字的名字。",
    "この辞書では一致する名前が見つかりませんでした。未使用を保証する結果ではありません。": "词典中没有匹配的名字。这并不代表名字未被使用。",
    "辞書を読み込めませんでした。ページを再読み込みしてください。": "无法加载词典，请刷新页面。",
    "名前を検索": "搜索名字",
    "検索結果": "查询结果",
    "検索結果のページ": "结果分页",
    "例：兎田ぺこら": "例如：Usada Pekora",
    "ぶいネーム｜VTuber名前チェック": "VName｜VTuber名称查询",
    "辞書を読み込んでいます…": "正在加载词典…"
  },
  "ko": {
    "ぶいネーム": "VName",
    "VTuber名前チェック": "VTuber 이름 검색",
    "その名前、もう使われてる？": "이미 사용 중인 이름일까요?",
    "名前・読み・英字から、同じ名前や似た名前をチェック。": "이름, 발음, 다른 표기로 같거나 비슷한 이름을 찾아보세요.",
    "名前を入力": "이름 입력",
    "調べたい名前": "검색할 이름",
    "ひらがな・カタカナ・英字でもOK": "일본어, 영어 및 다른 이름 표기 지원",
    "名前を調べる": "이름 검색",
    "試してみる": "예시 검색",
    "入力した名前は外部に送信されません。": "입력한 이름은 외부로 전송되지 않습니다.",
    "チェック結果": "검색 결과",
    "名前を入力して「名前を調べる」を押してください。": "이름을 입력하고 “이름 검색”을 누르세요.",
    "気になる名前から、調べてみよう": "마음에 드는 이름부터 검색해 보세요",
    "一致した名前と、その読み・英字を表示します。": "일치하는 이름, 발음, 다른 표기가 여기에 표시됩니다.",
    "前へ": "이전",
    "次へ": "다음",
    "一致がなくても、名前が未使用とは限りません。読み・英字には機械変換による参考情報を含みます。": "검색 결과가 없어도 사용되지 않는 이름이라는 뜻은 아닙니다. 일부 발음과 로마자 표기는 기계 변환 결과입니다.",
    "データと読みについて": "데이터와 발음 안내",
    "収集元：VTuber Database・VTuber Post／収集日：2026年9月7日。未収録の名前やグループ・チャンネル名も含まれます。一部ページは取得に失敗しています。": "출처: VTuber Database, VTuber Post. 수집일: 2026년 9월 7일. 누락된 이름이 있으며 그룹이나 채널이 포함될 수 있습니다. 일부 페이지는 가져오지 못했습니다.",
    "確認できた名前は個別の読みを優先します。補正の出典：": "개별 수정된 발음을 우선 사용합니다. 수정 출처:",
    "ホロライブ公式タレント一覧": "hololive 공식 탤런트 목록",
    "。全件の読みを確認した辞書ではありません。": ". 모든 발음을 검증한 것은 아닙니다.",
    "表示名が一致": "표시 이름 일치",
    "読み・英字が一致": "발음 또는 다른 표기 일치",
    "名前の一部が一致": "이름 일부 일치",
    "読み": "발음",
    "英字": "영문 / 로마자",
    "別名": "다른 표기",
    "不明": "알 수 없음",
    "個別補正済み": "개별 수정 완료",
    "読み・英字は参考情報（機械変換を含む）": "발음과 로마자 표기는 참고용입니다 (기계 변환 포함)",
    "文字を含む名前を入力してください。": "문자나 숫자가 포함된 이름을 입력하세요.",
    "この辞書では一致する名前が見つかりませんでした。未使用を保証する結果ではありません。": "이 사전에 일치하는 이름이 없습니다. 사용되지 않는 이름임을 보장하지 않습니다.",
    "辞書を読み込めませんでした。ページを再読み込みしてください。": "사전을 불러오지 못했습니다. 페이지를 새로고침하세요.",
    "名前を検索": "이름 검색",
    "検索結果": "검색 결과",
    "検索結果のページ": "결과 페이지",
    "例：兎田ぺこら": "예: Usada Pekora",
    "ぶいネーム｜VTuber名前チェック": "VName | VTuber 이름 검색",
    "辞書を読み込んでいます…": "사전을 불러오는 중…"
  }
};

translations["en"]["追加収集元：ユーザーローカルの公開ランキング。別名は同じレコードにまとめていますが、収録件数は人数を保証するものではありません。"]="Additional source: User Local public rankings. Aliases are grouped within records; the record count is not a verified count of individuals.";
translations["zh"]["追加収集元：ユーザーローカルの公開ランキング。別名は同じレコードにまとめていますが、収録件数は人数を保証するものではありません。"]="追加来源：User Local公开排行榜。别名归入同一条记录，但收录条数不代表经过核实的人数。";
translations["ko"]["追加収集元：ユーザーローカルの公開ランキング。別名は同じレコードにまとめていますが、収録件数は人数を保証するものではありません。"]="추가 출처: User Local 공개 순위. 다른 표기는 같은 레코드에 묶지만, 수록 건수가 검증된 인원수를 뜻하지는 않습니다.";
translations["en"]["出典のある読み"]="Reading with a source";
translations["zh"]["出典のある読み"]="有来源的读音";
translations["ko"]["出典のある読み"]="출처가 있는 발음";
translations["en"]["読みを確認できる情報がありません"]="No sourced reading available";
translations["zh"]["読みを確認できる情報がありません"]="暂无可确认读音的信息";
translations["ko"]["読みを確認できる情報がありません"]="발음을 확인할 수 있는 정보가 없습니다";
translations["en"]["読みの出典"]="Reading source";
translations["zh"]["読みの出典"]="读音来源";
translations["ko"]["読みの出典"]="발음 출처";
translations["en"]["一致がなくても、名前が未使用とは限りません。読みは出典を確認できたものだけ表示します。"]="No match does not guarantee a name is unused. Only readings with a source are displayed.";
translations["zh"]["一致がなくても、名前が未使用とは限りません。読みは出典を確認できたものだけ表示します。"]="没有匹配结果不代表名字未被使用。仅显示有来源的读音。";
translations["ko"]["一致がなくても、名前が未使用とは限りません。読みは出典を確認できたものだけ表示します。"]="검색 결과가 없어도 사용되지 않는 이름이라는 뜻은 아닙니다. 출처가 있는 발음만 표시합니다.";
translations["en"]["。全件の読みの確認は完了していません。未確認の読みは「不明」と表示します。"]=". Not all readings have been checked. Unsourced readings are shown as Unknown.";
translations["zh"]["。全件の読みの確認は完了していません。未確認の読みは「不明」と表示します。"]="。尚未核实所有读音。未确认的读音显示为“未知”。";
translations["ko"]["。全件の読みの確認は完了していません。未確認の読みは「不明」と表示します。"]=". 모든 발음을 확인한 것은 아닙니다. 미확인 발음은 “알 수 없음”으로 표시합니다.";
translations["en"]["VTuber・AIVTuberの名前・読み・別名をチェック。"]="Check VTuber and AIVTuber names, readings, and aliases.";
translations["zh"]["VTuber・AIVTuberの名前・読み・別名をチェック。"]="查询VTuber和AIVTuber的名字、读音和别名。";
translations["ko"]["VTuber・AIVTuberの名前・読み・別名をチェック。"]="VTuber·AIVTuber의 이름, 발음, 다른 표기를 검색하세요.";
translations["en"]["AIVTuberタグはAIVナビの掲載情報に基づきます。VTuberタグはAI不使用を保証するものではありません。"]="The AIVTuber tag is based on AIV Navi listings. The VTuber tag does not confirm that AI is not used.";
translations["zh"]["AIVTuberタグはAIVナビの掲載情報に基づきます。VTuberタグはAI不使用を保証するものではありません。"]="AIVTuber标签依据AIV Navi的收录信息。VTuber标签不保证未使用AI。";
translations["ko"]["AIVTuberタグはAIVナビの掲載情報に基づきます。VTuberタグはAI不使用を保証するものではありません。"]="AIVTuber 태그는 AIV Navi의 수록 정보를 기준으로 합니다. VTuber 태그가 AI 미사용을 보장하지는 않습니다.";
translations["en"]["関連リンク"]="Related links";
translations["zh"]["関連リンク"]="相关链接";
translations["ko"]["関連リンク"]="관련 링크";
translations["en"]["開発者のX"]="Developer’s X";
translations["zh"]["開発者のX"]="开发者的X";
translations["ko"]["開発者のX"]="개발자의 X";
let language='ja';
try{language=localStorage.getItem('vname-language')||(navigator.language||'ja').slice(0,2)}catch(e){}
if(!['ja','en','zh','ko'].includes(language))language='en';
const originalText=new WeakMap(), originalAttributes=new WeakMap();
function translated(value){const jp=value.trim();if(!jp||language==='ja')return value;let out=translations[language][jp];
if(!out){let m=jp.match(/^収録 ([\d,]+) 件$/);if(m)out={en:`${m[1]} records`,zh:`收录 ${m[1]} 条`,ko:`수록 ${m[1]}건`}[language];
m=jp.match(/^同じ表示名が ([\d,]+) 件あります。下の結果を確認してください。$/);if(m)out={en:`${m[1]} exact display-name matches. Check the results below.`,zh:`有 ${m[1]} 条显示名称完全一致，请查看下方结果。`,ko:`표시 이름이 일치하는 결과 ${m[1]}건입니다. 아래 결과를 확인하세요.`}[language];
m=jp.match(/^読み・英字、または名前の一部が一致する候補が ([\d,]+) 件あります。$/);if(m)out={en:`${m[1]} candidates match a reading, alias, or part of a name.`,zh:`有 ${m[1]} 条读音、别名或部分名字匹配的结果。`,ko:`발음, 다른 표기 또는 이름 일부가 일치하는 결과 ${m[1]}건입니다.`}[language];}
return out?value.replace(jp,out):value;}
function translateUI(){document.documentElement.lang=language==='zh'?'zh-Hans':language;document.title=translated('ぶいネーム｜VTuber名前チェック');
const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let node;while(node=walker.nextNode()){if(node.parentElement.closest('script,style,.name,.fields dd,[data-query],option'))continue;if(!originalText.has(node))originalText.set(node,node.nodeValue);node.nodeValue=translated(originalText.get(node))}
for(const el of document.querySelectorAll('[aria-label],[placeholder]')){if(!originalAttributes.has(el))originalAttributes.set(el,{});const saved=originalAttributes.get(el);for(const attr of ['aria-label','placeholder'])if(el.hasAttribute(attr)){if(!(attr in saved))saved[attr]=el.getAttribute(attr);el.setAttribute(attr,translated(saved[attr]))}}
document.getElementById('language').value=language;}
function setLanguage(value){if(!['ja','en','zh','ko'].includes(value))return;language=value;try{localStorage.setItem('vname-language',value)}catch(e){}translateUI()}
