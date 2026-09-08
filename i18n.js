'use strict';
const translations={
  "en": {
    "ぶいネーム": "ぶいネーム",
    "その名前で、はじめよう。": "Start with that name.",
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
    "辞書を読み込んでいます…": "Loading dictionary…"
  },
  "zh": {
    "ぶいネーム": "ぶいネーム",
    "その名前で、はじめよう。": "就用这个名字，开始吧。",
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
    "辞書を読み込んでいます…": "正在加载词典…"
  },
  "ko": {
    "ぶいネーム": "ぶいネーム",
    "その名前で、はじめよう。": "그 이름으로, 시작해요.",
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
translations["en"]["AIVTuberタグはAIVナビ・AITuberList・配信予定一覧・公開紹介情報などに基づきます。VTuberタグはAI不使用を保証するものではありません。"]="The AIVTuber tag is based on AIV Navi, AITuberList, streaming directories and public introductions. The VTuber tag does not confirm that AI is not used.";
translations["zh"]["AIVTuberタグはAIVナビ・AITuberList・配信予定一覧・公開紹介情報などに基づきます。VTuberタグはAI不使用を保証するものではありません。"]="AIVTuber标签依据AIV Navi、AITuberList、直播目录及公开介绍信息。VTuber标签不保证未使用AI。";
translations["ko"]["AIVTuberタグはAIVナビ・AITuberList・配信予定一覧・公開紹介情報などに基づきます。VTuberタグはAI不使用を保証するものではありません。"]="AIVTuber 태그는 AIV Navi, AITuberList, 방송 목록 및 공개 소개 정보를 기준으로 합니다. VTuber 태그가 AI 미사용을 보장하지는 않습니다.";
translations["en"]["関連リンク"]="Related links";
translations["zh"]["関連リンク"]="相关链接";
translations["ko"]["関連リンク"]="관련 링크";
translations["en"]["開発者のX"]="Developer’s X";
translations["zh"]["開発者のX"]="开发者的X";
translations["ko"]["開発者のX"]="개발자의 X";
translations["en"]["掲載対象は、実際にVTuber／AIVTuberとして活動を開始している方です。活動開始前の「VTuber準備中」の方は対象外です。引退・休止した方も、活動実績が確認できれば対象です。"]="Listings cover people who have started activities as VTubers or AIVTubers. Those still preparing to begin VTuber activities are outside the listing scope. Retired and inactive creators are also eligible when past activity is documented.";
translations["zh"]["掲載対象は、実際にVTuber／AIVTuberとして活動を開始している方です。活動開始前の「VTuber準備中」の方は対象外です。引退・休止した方も、活動実績が確認できれば対象です。"]="收录对象为已正式开始以VTuber／AIVTuber身份活动的人。尚未开始活动、仅处于“VTuber准备中”阶段的人不属于收录范围。已引退或暂停活动者，如有过往活动记录，也属于收录范围。";
translations["ko"]["掲載対象は、実際にVTuber／AIVTuberとして活動を開始している方です。活動開始前の「VTuber準備中」の方は対象外です。引退・休止した方も、活動実績が確認できれば対象です。"]="실제로 VTuber／AIVTuber 활동을 시작한 분을 수록 대상으로 합니다. 활동을 시작하지 않은 “VTuber 준비 중”인 분은 대상에서 제외됩니다. 은퇴하거나 활동을 쉬고 있어도 과거 활동이 확인되면 대상에 포함됩니다.";
translations["en"]["収集元：VTuber Database・VTuber Post・ユーザーローカル・AIVナビ・VSTATS・liverfun.jp・TaiwanVTuberData・タイVTuber名簿・インドネシアの保存データ・学術系Vtuber名鑑・AI VTuberDB・HoloListと2019年の保存データ・本人の公開プロフィール。個人勢や小規模な活動者も対象です。掲載・活動状況の反映には遅れや漏れがあり、全員を網羅するものではありません。収録件数にはグループやチャンネルが含まれる場合があります。"]="Sources: VTuber Database, VTuber Post, User Local, AIV Navi, VSTATS, liverfun.jp, TaiwanVTuberData, the Thai VTuber roster, an Indonesian snapshot, the Academic VTuber Directory, AI VTuberDB, HoloList and 2019 snapshots, and creators’ public profiles. Independent and small creators are included. Listings and activity status may be delayed or incomplete; coverage is not exhaustive. Counts may include groups and channels.";
translations["zh"]["収集元：VTuber Database・VTuber Post・ユーザーローカル・AIVナビ・VSTATS・liverfun.jp・TaiwanVTuberData・タイVTuber名簿・インドネシアの保存データ・学術系Vtuber名鑑・AI VTuberDB・HoloListと2019年の保存データ・本人の公開プロフィール。個人勢や小規模な活動者も対象です。掲載・活動状況の反映には遅れや漏れがあり、全員を網羅するものではありません。収録件数にはグループやチャンネルが含まれる場合があります。"]="来源：VTuber Database、VTuber Post、User Local、AIV Navi、VSTATS、liverfun.jp、TaiwanVTuberData、泰国VTuber名册、印度尼西亚存档、学术系Vtuber名鉴、AI VTuberDB、HoloList和2019年存档，以及创作者的公开资料。收录范围包括个人势和小规模活动者。收录与活动状态的更新可能延迟或遗漏，并非涵盖所有人。条数可能包含团体和频道。";
translations["ko"]["収集元：VTuber Database・VTuber Post・ユーザーローカル・AIVナビ・VSTATS・liverfun.jp・TaiwanVTuberData・タイVTuber名簿・インドネシアの保存データ・学術系Vtuber名鑑・AI VTuberDB・HoloListと2019年の保存データ・本人の公開プロフィール。個人勢や小規模な活動者も対象です。掲載・活動状況の反映には遅れや漏れがあり、全員を網羅するものではありません。収録件数にはグループやチャンネルが含まれる場合があります。"]="출처: VTuber Database, VTuber Post, User Local, AIV Navi, VSTATS, liverfun.jp, TaiwanVTuberData, 태국 VTuber 명단, 인도네시아 저장 자료, 학술계 Vtuber 명감, AI VTuberDB, HoloList 및 2019년 저장 자료, 활동자 본인의 공개 프로필. 개인 및 소규모 활동자도 대상입니다. 수록 및 활동 상태 반영에 지연이나 누락이 있을 수 있으며, 모든 활동자를 망라하지는 않습니다. 건수에는 그룹이나 채널이 포함될 수 있습니다.";
translations["en"]["掲載元"]="Listing source";
translations["zh"]["掲載元"]="收录来源";
translations["ko"]["掲載元"]="수록 출처";
let language='ja';
try{language=localStorage.getItem('vname-language')||(navigator.language||'ja').slice(0,2)}catch(e){}
if(!['ja','en','zh','ko'].includes(language))language='en';
const originalText=new WeakMap(), originalAttributes=new WeakMap();
function translated(value){const jp=value.trim();if(!jp||language==='ja')return value;let out=translations[language][jp];
if(!out){let m=jp.match(/^収録 ([\d,]+) 件$/);if(m)out={en:`${m[1]} records`,zh:`收录 ${m[1]} 条`,ko:`수록 ${m[1]}건`}[language];
m=jp.match(/^同じ表示名が ([\d,]+) 件あります。下の結果を確認してください。$/);if(m)out={en:`${m[1]} exact display-name matches. Check the results below.`,zh:`有 ${m[1]} 条显示名称完全一致，请查看下方结果。`,ko:`표시 이름이 일치하는 결과 ${m[1]}건입니다. 아래 결과를 확인하세요.`}[language];
m=jp.match(/^読み・英字、または名前の一部が一致する候補が ([\d,]+) 件あります。$/);if(m)out={en:`${m[1]} candidates match a reading, alias, or part of a name.`,zh:`有 ${m[1]} 条读音、别名或部分名字匹配的结果。`,ko:`발음, 다른 표기 또는 이름 일부가 일치하는 결과 ${m[1]}건입니다.`}[language];}
if(!out){let m=jp.match(/^同名・同じ読みの候補: ([\d,]+) 件$/);if(m)out={en:`Same-name or reading matches: ${m[1]}`,zh:`同名或同读音候选：${m[1]} 条`,ko:`동일 이름·발음 후보: ${m[1]}건`}[language];
m=jp.match(/^AIモデルを読み込み中: ([\d,]+) MB$/);if(m)out={en:`Loading AI model: ${m[1]} MB`,zh:`正在加载AI模型：${m[1]} MB`,ko:`AI 모델 불러오는 중: ${m[1]} MB`}[language];}
const tagMatch=jp.match(/^タグ「(.+)」に一致する掲載が ([\d,]+) 件あります。$/);if(tagMatch)out={en:`${tagMatch[2]} records tagged ${tagMatch[1]}.`,zh:`标签“${tagMatch[1]}”有 ${tagMatch[2]} 条记录。`,ko:`${tagMatch[1]} 태그의 기록 ${tagMatch[2]}건입니다.`}[language];
const countMatch=jp.match(/^([\d,]+) 件の活動者を表示$/);if(countMatch)out={en:`${countMatch[1]} creator records`,zh:`显示 ${countMatch[1]} 条创作者记录`,ko:`활동자 기록 ${countMatch[1]}건`}[language];
const dateMatch=jp.match(/^確認日: (.+)$/);if(dateMatch)out={en:`Checked: ${dateMatch[1]}`,zh:`确认日期: ${dateMatch[1]}`,ko:`확인일: ${dateMatch[1]}`}[language];
return out?value.replace(jp,out):value;}
function translateUI(){document.documentElement.lang=language==='zh'?'zh-Hans':language;document.title='ぶいネーム';
const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let node;while(node=walker.nextNode()){if(node.parentElement.closest('script,style,.name,.fields dd:not([data-i18n]),[data-query],option:not([data-i18n]),.chat-message.user .chat-body,[data-generated],.candidate-name,.candidate-reading,.candidate-reason,[data-word]'))continue;if(!originalText.has(node))originalText.set(node,node.nodeValue);node.nodeValue=translated(originalText.get(node))}
for(const el of document.querySelectorAll('[aria-label],[placeholder]')){if(!originalAttributes.has(el))originalAttributes.set(el,{});const saved=originalAttributes.get(el);for(const attr of ['aria-label','placeholder'])if(el.hasAttribute(attr)){if(!(attr in saved))saved[attr]=el.getAttribute(attr);el.setAttribute(attr,translated(saved[attr]))}}
document.getElementById('language').value=language;}
function setLanguage(value){if(!['ja','en','zh','ko'].includes(value))return;language=value;try{localStorage.setItem('vname-language',value)}catch(e){}translateUI()}

translations["en"]["過去の活動実績も対象にしています。保存データの掲載情報は、その時点の記録であり、現在の活動状況を示すものではありません。"]="Past activity is included. Archived listings describe the source at its recorded date, not the creator’s current activity status.";
translations["zh"]["過去の活動実績も対象にしています。保存データの掲載情報は、その時点の記録であり、現在の活動状況を示すものではありません。"]="收录范围包含过往活动。存档信息仅反映记录当时的情况，并不代表目前的活动状态。";
translations["ko"]["過去の活動実績も対象にしています。保存データの掲載情報は、その時点の記録であり、現在の活動状況を示すものではありません。"]="과거 활동도 수록 대상입니다. 저장된 자료는 기록 당시의 정보이며 현재 활동 상태를 나타내지 않습니다.";

translations["en"]["VTuber・AIVTuber・Vライバーの名前・読み・別名をチェック。"]="Check VTuber, AIVTuber, and V-liver names, readings, and aliases.";
translations["zh"]["VTuber・AIVTuber・Vライバーの名前・読み・別名をチェック。"]="查询VTuber、AIVTuber和虚拟主播的名字、读音与别名。";
translations["ko"]["VTuber・AIVTuber・Vライバーの名前・読み・別名をチェック。"]="VTuber·AIVTuber·V라이버의 이름, 발음, 다른 표기를 검색하세요.";
translations["en"]["YouTube・TikTok・IRIAM・Avvyなど、配信媒体を問わず掲載対象です。"]="Creators on YouTube, TikTok, IRIAM, Avvy and other streaming platforms are eligible.";
translations["zh"]["YouTube・TikTok・IRIAM・Avvyなど、配信媒体を問わず掲載対象です。"]="收录范围不限平台，包括YouTube、TikTok、IRIAM、Avvy等。";
translations["ko"]["YouTube・TikTok・IRIAM・Avvyなど、配信媒体を問わず掲載対象です。"]="YouTube·TikTok·IRIAM·Avvy 등 방송 플랫폼에 관계없이 수록 대상입니다.";
translations["en"]["主な活動媒体"]="Main platforms";
translations["zh"]["主な活動媒体"]="主要活动平台";
translations["ko"]["主な活動媒体"]="주요 활동 플랫폼";
translations["en"]["確認できた媒体"]="Documented platforms";
translations["zh"]["確認できた媒体"]="已确认的平台";
translations["ko"]["確認できた媒体"]="확인된 플랫폼";
translations["en"]["活動媒体の出典"]="Platform source";
translations["zh"]["活動媒体の出典"]="活动平台来源";
translations["ko"]["活動媒体の出典"]="활동 플랫폼 출처";
translations["en"]["媒体別の追加収集元：321公式Vライバー一覧・Clover公式プロフィール・Avvy配信者インタビュー。主な活動媒体は本人・所属先の明記がある場合に表示し、アカウントの存在だけでは判定しません。"]="Additional platform sources: the official 321 V-liver roster, Clover profiles, and Avvy broadcaster interviews. Main platforms are displayed only when the creator or agency explicitly identifies broadcast destinations; account links alone do not establish this.";
translations["zh"]["媒体別の追加収集元：321公式Vライバー一覧・Clover公式プロフィール・Avvy配信者インタビュー。主な活動媒体は本人・所属先の明記がある場合に表示し、アカウントの存在だけでは判定しません。"]="平台补充来源：321官方虚拟主播名册、Clover官方资料和Avvy主播访谈。仅在本人或所属机构明确列出配信平台时显示主要活动平台，不根据账号链接推断。";
translations["ko"]["媒体別の追加収集元：321公式Vライバー一覧・Clover公式プロフィール・Avvy配信者インタビュー。主な活動媒体は本人・所属先の明記がある場合に表示し、アカウントの存在だけでは判定しません。"]="플랫폼별 추가 출처: 321 공식 V라이버 목록, Clover 공식 프로필, Avvy 방송자 인터뷰. 본인이나 소속사가 방송 플랫폼을 명시한 경우에만 주요 활동 플랫폼을 표시하며, 계정 링크만으로 판단하지 않습니다.";
translations["en"]["掲載対象は、実際にVTuber／AIVTuber／Vライバーとして活動を開始している方です。活動開始前の「VTuber準備中」の方は対象外です。引退・休止した方も、活動実績が確認できれば対象です。"]="Listings cover creators who have started activities as VTubers, AIVTubers, or V-livers. Creators who have not begun virtual activities are excluded. Retired and inactive creators are eligible when past activity is documented.";
translations["zh"]["掲載対象は、実際にVTuber／AIVTuber／Vライバーとして活動を開始している方です。活動開始前の「VTuber準備中」の方は対象外です。引退・休止した方も、活動実績が確認できれば対象です。"]="收录已开始以VTuber、AIVTuber或虚拟主播身份活动的人。尚未开始虚拟活动的准备阶段不在范围内；已引退或暂停活动者，如有活动记录，也可收录。";
translations["ko"]["掲載対象は、実際にVTuber／AIVTuber／Vライバーとして活動を開始している方です。活動開始前の「VTuber準備中」の方は対象外です。引退・休止した方も、活動実績が確認できれば対象です。"]="VTuber·AIVTuber·V라이버로 활동을 시작한 분을 수록합니다. 아직 버추얼 활동을 시작하지 않은 준비 단계는 제외하며, 은퇴·휴식 중이어도 과거 활동이 확인되면 대상입니다.";

// Naming consultation and dictionary statistics. Creator names and chat content are excluded from UI translation.
for (const [jp, values] of Object.entries({
  '名前のツール':['Naming tools','命名工具','이름 도구'],
  '名前をチェック':['Check a name','查询名字','이름 확인'],
  'AIに名前相談':['Ask AI about names','向AI咨询名字','AI에게 이름 상담'],
  '名前の傾向':['Name patterns','名字倾向','이름 경향'],
  'AIと、あなたらしい名前を考えよう':['Find your name with AI','与AI一起构思适合你的名字','AI와 나다운 이름을 생각해 보세요'],
  'モチーフや雰囲気を相談すると、名前の候補と理由を提案します。候補はこの辞書で自動チェックします。':['Describe a theme or mood to get name ideas and reasons. Suggestions are automatically checked against this dictionary.','描述主题或氛围，AI将提出名字候选及理由，并自动在本词典中查询。','모티프나 분위기를 알려주면 이름 후보와 이유를 제안합니다. 후보는 이 사전에서 자동으로 확인합니다.'],
  'Gemma 4 E2Bが、この端末のブラウザ内で動きます。モデル約2GBの取得と、WebGPU対応のブラウザ・十分なメモリが必要です。AI相談は試験機能です。':['Gemma 4 E2B runs in this device’s browser. It requires an approximately 2 GB model download, a WebGPU browser, and enough memory. AI consultation is experimental.','Gemma 4 E2B在此设备的浏览器中运行。需要下载约2GB模型、支持WebGPU的浏览器及足够内存。AI咨询为试验功能。','Gemma 4 E2B가 이 기기의 브라우저에서 실행됩니다. 약 2GB 모델 다운로드, WebGPU 지원 브라우저와 충분한 메모리가 필요합니다. AI 상담은 시험 기능입니다.'],
  'スマホは端末・ブラウザによって動作しない場合があります。Wi-Fi環境でお試しください。名前検索と傾向分析はAIなしで使えます。':['Mobile support depends on the device and browser. Try using Wi-Fi. Name search and pattern analysis work without AI.','手机能否运行取决于设备和浏览器。建议在Wi-Fi下尝试。名字查询和倾向分析无需AI。','스마트폰은 기기와 브라우저에 따라 작동하지 않을 수 있습니다. Wi-Fi에서 시도해 주세요. 이름 검색과 경향 분석은 AI 없이 사용할 수 있습니다.'],
  'AIを読み込む（約2GB）':['Load AI (about 2 GB)','加载AI（约2GB）','AI 불러오기 (약 2GB)'],
  'AIを終了':['Unload AI','关闭AI','AI 종료'],
  'AIモデルの読み込み':['AI model loading','AI模型加载','AI 모델 불러오기'],
  '相談内容はAIサーバーへ送信されません。モデルと実行プログラムを外部から取得します。':['Your conversation is not sent to an AI server. The model and runtime are downloaded from external hosts.','咨询内容不会发送到AI服务器。模型与运行程序从外部下载。','상담 내용은 AI 서버로 전송되지 않습니다. 모델과 실행 프로그램은 외부에서 다운로드합니다.'],
  '猫モチーフでかわいく':['Cute cat theme','可爱的猫咪主题','귀여운 고양이 모티프'],
  '海外でも呼びやすく':['Easy to say worldwide','海外也容易称呼','해외에서도 부르기 쉽게'],
  '夜・星のイメージ':['Night and stars','夜晚与星星的意象','밤과 별의 이미지'],
  '名前の相談履歴':['Naming conversation','名字咨询记录','이름 상담 기록'],
  'どんな名前にしたい？':['What kind of name would you like?','想取什么样的名字？','어떤 이름을 원하나요?'],
  '例：猫がモチーフ。漢字の苗字＋ひらがなで、呼びやすい名前にしたい。':['Example: a cat theme, with a kanji surname and hiragana given name that is easy to say.','例如：猫咪主题，汉字姓氏加平假名，想要容易称呼的名字。','예: 고양이 모티프. 한자 성과 히라가나 이름으로 부르기 쉽게 만들고 싶어요.'],
  '相談する':['Ask AI','开始咨询','상담하기'],
  '回答を止める':['Stop response','停止回答','답변 중지'],
  '相談をやり直す':['Start a new conversation','重新咨询','새로 상담하기'],
  '候補の読みはAIによる提案です。辞書に一致がなくても、名前が未使用とは限りません。':['Suggested readings are AI-generated. No dictionary match does not mean a name is unused.','候选读音由AI提出。词典中没有匹配，并不代表名字尚未被使用。','후보 발음은 AI의 제안입니다. 사전에 일치 항목이 없어도 미사용 이름이라는 뜻은 아닙니다.'],
  '収録されている名前の傾向':['Patterns in the dictionary','已收录名字的倾向','수록된 이름의 경향'],
  '文字数・表記・よく使われる漢字を、現在の辞書から集計します。AIの読み込みは不要です。':['Explore name lengths, scripts and frequent kanji in the current dictionary. No AI download is needed.','根据当前词典统计字数、文字种类及常用汉字，无需加载AI。','현재 사전의 이름 길이, 문자 구성과 자주 쓰이는 한자를 집계합니다. AI를 불러올 필요가 없습니다.'],
  '媒体で絞り込む':['Filter by platform','按平台筛选','플랫폼으로 필터'],
  'すべての媒体':['All platforms','所有平台','모든 플랫폼'],
  '表示名のレコード数を集計しています。空白を除いた文字数です。漢字には日本語以外の名前も含みます。収集元・言語の偏りやチャンネル名を含むため、VTuber全体の人気や最近の流行を示すものではありません。':['Statistics count display-name records and exclude spaces from lengths. Kanji counts include non-Japanese names. Sources and languages are uneven, and some records are channels; these figures do not measure overall popularity or recent trends.','统计单位为显示名称记录，字数不计空白。汉字统计包含非日语名字。数据存在来源及语言偏差，也可能含频道名，不能代表全体VTuber的人气或近期流行。','표시 이름 레코드를 집계하며 글자 수에서 공백을 제외합니다. 한자에는 일본어 이외의 이름도 포함됩니다. 출처·언어의 편중과 채널명이 포함되어 VTuber 전체의 인기나 최근 유행을 나타내지는 않습니다.'],
  'この傾向をもとにAIに相談':['Discuss these patterns with AI','根据此倾向咨询AI','이 경향으로 AI에게 상담'],
  '集計対象':['Records analyzed','统计对象','집계 대상'],
  '平均文字数':['Average length','平均字数','평균 글자 수'],
  '名前の文字数':['Name length','名字字数','이름 글자 수'],
  '文字の構成':['Writing systems','文字构成','문자 구성'],
  'よく使われる漢字':['Frequent kanji','常用汉字','자주 쓰이는 한자'],
  'よく使われる漢字2文字':['Frequent kanji pairs','常用双字汉字组合','자주 쓰이는 한자 두 글자'],
  '表記':['Text','表记','표기'],
  '含むレコード数':['Records containing it','包含的记录数','포함하는 레코드 수'],
  '1〜4文字':['1–4 characters','1～4字','1~4글자'],
  '5〜8文字':['5–8 characters','5～8字','5~8글자'],
  '9〜12文字':['9–12 characters','9～12字','9~12글자'],
  '13文字以上':['13+ characters','13字以上','13글자 이상'],
  '漢字':['Kanji / Han characters','汉字','한자'],
  'ひらがな':['Hiragana','平假名','히라가나'],
  'カタカナ':['Katakana','片假名','가타카나'],
  '英字':['Latin letters','拉丁字母','영문'],
  '複数の文字種':['Mixed scripts','多种文字','여러 문자 종류'],
  '数字・その他':['Numbers / other','数字及其他','숫자·기타'],
  'あなた':['You','你','나'],
  '名前相談AI':['Naming AI','名字咨询AI','이름 상담 AI'],
  'この名前を調べる':['Check this name','查询此名字','이 이름 검색'],
  '名前を考えています…':['Thinking of names…','正在构思名字…','이름을 생각하고 있습니다…'],
  'このブラウザではWebGPUを利用できません。対応するPC版Chromeなどでお試しください。名前検索と傾向分析はそのまま使えます。':['WebGPU is unavailable in this browser. Try a supported browser such as desktop Chrome. Search and analysis are still available.','此浏览器无法使用WebGPU。请尝试支持的浏览器，如电脑版Chrome。名字查询和倾向分析仍可使用。','이 브라우저에서 WebGPU를 사용할 수 없습니다. PC용 Chrome 등 지원 브라우저에서 시도해 주세요. 검색과 분석은 계속 이용할 수 있습니다.'],
  'AIの動作環境を確認しています…':['Checking AI support…','正在检查AI运行环境…','AI 실행 환경을 확인하고 있습니다…'],
  'AIモデルを読み込んでいます。約2GBの取得に時間がかかる場合があります。':['Loading the AI model. The approximately 2 GB download may take a while.','正在加载AI模型。下载约2GB可能需要一些时间。','AI 모델을 불러옵니다. 약 2GB 다운로드에 시간이 걸릴 수 있습니다.'],
  'AIに相談できます。':['AI is ready.','可以向AI咨询了。','AI에게 상담할 수 있습니다.'],
  'GPUを利用できません。ブラウザの設定や対応状況を確認してください。':['GPU access is unavailable. Check browser settings and compatibility.','无法使用GPU。请检查浏览器设置及兼容性。','GPU를 사용할 수 없습니다. 브라우저 설정과 지원 여부를 확인해 주세요.'],
  'AIを起動できませんでした。対応ブラウザ・空きメモリ・通信環境を確認して、再度読み込んでください。':['AI could not start. Check browser support, available memory and your connection, then try loading it again.','AI启动失败。请检查浏览器兼容性、可用内存及网络后重新加载。','AI를 시작하지 못했습니다. 브라우저 지원, 여유 메모리와 통신 상태를 확인하고 다시 불러와 주세요.'],
  'AIを終了しています…':['Unloading AI…','正在关闭AI…','AI를 종료하고 있습니다…'],
  'AIを終了しました。名前検索と傾向分析はそのまま使えます。':['AI has been unloaded. Name search and analysis remain available.','AI已关闭，名字查询和倾向分析仍可使用。','AI를 종료했습니다. 이름 검색과 경향 분석은 계속 이용할 수 있습니다.'],
  '会話が長くなりました。「相談をやり直す」で条件をまとめて相談してください。':['This conversation is near its limit. Start a new conversation with a summary of your preferences.','对话即将达到长度上限。请点击“重新咨询”，汇总条件后再次咨询。','대화가 길어졌습니다. “새로 상담하기”로 조건을 요약해 다시 상담해 주세요.'],
  '回答を停止しました。':['Response stopped.','已停止回答。','답변을 중지했습니다.'],
  '続けて希望を伝えると、候補を絞り込めます。':['Share more preferences to refine the suggestions.','继续补充要求，可以缩小候选范围。','원하는 조건을 더 알려주면 후보를 좁힐 수 있습니다.'],
  '回答を作れませんでした。「相談をやり直す」か、AIを読み込み直してください。':['Could not generate a response. Start a new conversation or reload AI.','无法生成回答。请重新咨询或重新加载AI。','답변을 만들지 못했습니다. 새로 상담하거나 AI를 다시 불러와 주세요.'],
  'AIを読み込むと相談を始められます。':['Load AI to start a conversation.','加载AI后即可开始咨询。','AI를 불러오면 상담을 시작할 수 있습니다.'],
  '回答をうまく整理できませんでした。条件を短くして、もう一度相談してください。':['The response could not be parsed. Try again with a shorter description.','未能整理回答。请缩短条件后再次咨询。','답변을 정리하지 못했습니다. 조건을 짧게 해서 다시 상담해 주세요.'],
  '候補を考えました。':['Here are some ideas.','已构思一些候选。','후보를 생각해 보았습니다.']
})) ['en','zh','ko'].forEach((lang,i)=>translations[lang][jp]=values[i]);

for (const [jp,values] of Object.entries({
 'ぶいネーム ホーム':['ぶいネーム home','ぶいネーム首页','ぶいネーム 홈'],
 'その名前から、はじまる。':['It starts with your name.','从这个名字开始。','그 이름에서 시작됩니다.'],
 'あなたらしい活動名を、ここから。':['Your creator name starts here.','在这里，找到适合你的活动名。','나다운 활동명을 여기서부터.'],
 '気になる名前をチェック':['Check a name you like','查询感兴趣的名字','마음에 드는 이름 확인'],
 '一緒に、あなたらしい名前を。':['Let’s find a name that feels like you.','一起构思适合你的名字。','함께, 나다운 이름을.'],
 'PC推奨':['Desktop recommended','推荐使用电脑','PC 권장'],
 'インストール不要':['No installation','无需安装','설치 불필요'],
 'この端末で動くAI':['AI on this device','在此设备上运行的AI','이 기기에서 실행되는 AI'],
 '手を振る名前相談ロボット':['A friendly naming robot waving hello','挥手致意的名字咨询机器人','손을 흔드는 이름 상담 로봇'],
 '名前相談ルーム':['Naming room','名字咨询室','이름 상담실'],
 'AIの準備が必要です':['AI setup needed','需要准备AI','AI 준비가 필요합니다'],
 '準備中':['Getting ready','准备中','준비 중'],
 '相談できます':['Ready to chat','可以咨询了','상담할 수 있습니다'],
 'どんなあなたになりたい？':['Who would you like to become?','你想成为怎样的自己？','어떤 내가 되고 싶나요?'],
 '好きなもの、なりたい雰囲気。小さなヒントから、一緒に考えよう。':['Things you love, a mood you like. Let’s start with a little inspiration.','喜欢的事物、想呈现的氛围。从小小的提示开始，一起想吧。','좋아하는 것, 원하는 분위기. 작은 힌트부터 함께 생각해 봐요.'],
 'AIの準備':['AI setup','AI准备','AI 준비'],
 '相談を始める準備':['Get ready to chat','准备开始咨询','상담 시작 준비'],
 '初回に約2GBを取得します。保存済みなら、次回から同じモデルを使います。':['The first download is about 2 GB. A saved model is reused on later visits.','首次下载约2GB。保存后，下次将重复使用同一模型。','처음에 약 2GB를 다운로드합니다. 저장하면 다음부터 같은 모델을 재사용합니다.'],
 'モデルを端末に保存':['Save model on this device','将模型保存在此设备','모델을 기기에 저장'],
 '保存状態を確認しています…':['Checking saved model…','正在检查保存状态…','저장 상태를 확인합니다…'],
 'AIを準備する（初回 約2GB）':['Set up AI (first download ≈2 GB)','准备AI（首次约2GB）','AI 준비 (처음 약 2GB)'],
 '保存済みAIを起動':['Start saved AI','启动已保存的AI','저장된 AI 시작'],
 'AIを準備したら、好きなモチーフを教えてください。':['Once AI is ready, tell it a theme you like.','AI准备好后，告诉它你喜欢的主题。','AI가 준비되면 좋아하는 모티프를 알려 주세요.'],
 'AI相談はPC推奨です':['Desktop is recommended for AI','AI咨询推荐使用电脑','AI 상담은 PC를 권장합니다'],
 'スマホはメモリ不足などで回答できない場合があります。名前検索と傾向分析はスマホでも使えます。':['Phones may fail to generate due to memory or other limits. Search and analysis also work on phones.','手机可能因内存等限制无法生成回答。名字查询和倾向分析也可在手机使用。','스마트폰은 메모리 등의 한계로 답변을 만들지 못할 수 있습니다. 이름 검색과 경향 분석은 스마트폰에서도 사용할 수 있습니다.'],
 '利用条件と保存について':['Requirements and storage','使用条件与保存','이용 조건과 저장 안내'],
 'Gemma 4 E2Bが端末内で動く試験機能です。WebGPU対応ブラウザと十分なメモリが必要です。取得にはWi-Fiをおすすめします。':['This experimental feature runs Gemma 4 E2B on your device. A WebGPU browser and sufficient memory are required. Use Wi-Fi for the download.','此试验功能在设备上运行Gemma 4 E2B，需要支持WebGPU的浏览器及足够内存。建议使用Wi-Fi下载。','Gemma 4 E2B가 기기에서 실행되는 시험 기능입니다. WebGPU 지원 브라우저와 충분한 메모리가 필요합니다. 다운로드에는 Wi-Fi를 권장합니다.'],
 '保存量は約2GBです。ブラウザのデータ削除などで消えた場合は、再取得が必要です。起動時は別途メモリを使います。':['The saved model uses about 2 GB. If browser data is removed, it must be downloaded again. Running it also uses memory.','模型保存占用约2GB。若浏览器数据被清除，需要重新下载。运行时还会使用内存。','저장된 모델은 약 2GB를 사용합니다. 브라우저 데이터가 삭제되면 다시 다운로드해야 합니다. 실행 중에는 별도로 메모리를 사용합니다.'],
 '保存したAIを削除':['Delete saved AI','删除已保存的AI','저장된 AI 삭제'],
 'モデル保存済み：約2GB。同じモデルを再利用します。':['Model saved: about 2 GB. The same model will be reused.','模型已保存：约2GB。将重复使用同一模型。','모델 저장됨: 약 2GB. 같은 모델을 재사용합니다.'],
 '保存済みのモデルはありません。':['No saved model.','没有已保存的模型。','저장된 모델이 없습니다.'],
 'このブラウザではモデルを保存できません。':['This browser cannot save the model.','此浏览器无法保存模型。','이 브라우저에서는 모델을 저장할 수 없습니다.'],
 'この端末でAIを起動しています…':['Starting AI on this device…','正在此设备上启动AI…','이 기기에서 AI를 시작합니다…'],
 'モデルを保存できませんでした。空き容量を確認するか「モデルを端末に保存」をオフにしてお試しください。':['Could not save the model. Check free storage or turn off “Save model on this device” to try without saving.','无法保存模型。请检查可用空间，或关闭“将模型保存在此设备”后重试。','모델을 저장하지 못했습니다. 여유 공간을 확인하거나 “모델을 기기에 저장”을 끄고 시도해 주세요.'],
 'AIを起動できませんでした。PCの対応ブラウザで、空きメモリと通信環境を確認してください。':['AI could not start. Try a supported desktop browser and check free memory and your connection.','AI启动失败。请使用支持的电脑浏览器，并检查可用内存及网络。','AI를 시작하지 못했습니다. 지원되는 PC 브라우저에서 여유 메모리와 통신 상태를 확인해 주세요.'],
 '回答を受け取れませんでした。PCで条件を短くして、もう一度お試しください。':['No response was received. Try again on a desktop with a shorter request.','未收到回答。请在电脑上缩短条件后重试。','답변을 받지 못했습니다. PC에서 조건을 짧게 해서 다시 시도해 주세요.'],
 '回答が途中で終わりました。条件を短くして、もう一度相談してください。':['The response ended early. Try again with a shorter request.','回答中途结束。请缩短条件后再次咨询。','답변이 도중에 끝났습니다. 조건을 짧게 해서 다시 상담해 주세요.'],
 'この端末では回答を生成できませんでした。PCで、条件を短くしてお試しください。':['This device could not generate a response. Try a shorter request on a desktop.','此设备未能生成回答。请在电脑上缩短条件后尝试。','이 기기에서 답변을 만들지 못했습니다. PC에서 조건을 짧게 해서 시도해 주세요.'],
 '保存したAIモデルを削除しました。':['Saved AI model deleted.','已删除保存的AI模型。','저장된 AI 모델을 삭제했습니다.'],
 '削除できませんでした。ブラウザのサイトデータ設定から削除できます。':['Could not delete it here. You can remove it from the browser’s site data settings.','此处删除失败，可在浏览器的网站数据设置中删除。','여기서 삭제하지 못했습니다. 브라우저의 사이트 데이터 설정에서 삭제할 수 있습니다.'],
 'Vライバー':['V-liver','虚拟主播','V라이버']
})) ['en','zh','ko'].forEach((lang,i)=>translations[lang][jp]=values[i]);
for(const [jp,values] of Object.entries({
 'モチーフや雰囲気から、名前の候補と理由を提案します。カードに表示した候補は、辞書で自動チェック。':['Get name ideas and reasons from a theme or mood. Names shown on suggestion cards are checked against the dictionary.','根据主题或氛围提出名字与理由，卡片中显示的候选将自动在词典中查询。','모티프나 분위기에 맞는 이름과 이유를 제안합니다. 카드에 표시된 후보는 사전에서 자동 확인합니다.'],
 '文章で回答しました。候補の名前は「名前をチェック」で確認してください。':['AI replied in text. Check any suggested names using the name search.','AI以文字形式回答了。请使用“查询名字”确认候选名称。','AI가 글로 답변했습니다. 후보 이름은 “이름 확인”에서 검색해 주세요.']
})) ['en','zh','ko'].forEach((lang,i)=>translations[lang][jp]=values[i]);

for(const [jp,values] of Object.entries({
 '気になる名前を調べる。AIと新しい名前を考える。':['Look up a name. Create a new one with AI.','查询感兴趣的名字，与AI一起构思新名字。','궁금한 이름을 검색하고, AI와 새로운 이름을 생각해 보세요.'],
 'VTuber・AIVTuber・Vライバーに対応':['For VTubers, AIVTubers and V-livers','支持VTuber、AIVTuber和虚拟主播','VTuber·AIVTuber·V라이버 지원'],
 'その他のアカウント':['Other accounts','其他账号','다른 계정'],
 '相談の会話履歴':['Conversation history','咨询记录','상담 대화 기록']
})) ['en','zh','ko'].forEach((lang,i)=>translations[lang][jp]=values[i]);

for(const [jp,values] of Object.entries({
 'AIの準備後に、相談のきっかけを提案します。':['AI will suggest conversation starters once it is ready.','AI准备好后会生成咨询建议。','AI가 준비되면 상담 주제를 제안합니다.'],
 '相談のきっかけを考えています…':['Creating conversation starters…','正在构思咨询建议…','상담 주제를 생각하고 있습니다…'],
 'AIからの相談ヒント':['Ideas from AI','AI的咨询建议','AI의 상담 힌트'],
 'AIが考えた相談候補':['AI-generated conversation ideas','AI生成的咨询建议','AI가 만든 상담 주제'],
 '続けて、希望を自由に入力してください。':['Tell AI what you would like next.','请继续自由输入您的要求。','이어서 원하는 내용을 자유롭게 입력해 주세요.'],
 '候補を生成できませんでした。希望を直接入力して相談できます。':['Ideas could not be generated. You can still type your request to chat.','未能生成建议，您仍可直接输入要求进行咨询。','상담 주제를 만들지 못했습니다. 원하는 내용을 직접 입력해 상담할 수 있습니다.']
})) ['en','zh','ko'].forEach((lang,i)=>translations[lang][jp]=values[i]);

for(const [jp,values] of Object.entries({
 'タグで絞り込む':['Filter by tag','按标签筛选','태그로 필터링'],
 'すべてのタグ':['All tags','全部标签','모든 태그'],
 'タグだけでも検索できます。':['You can search by tag alone.','也可以只按标签搜索。','태그만으로도 검색할 수 있습니다.'],
 'タグが一致':['Tag match','标签匹配','태그 일치'],
 '名前を入力するか、タグを選んで検索してください。':['Enter a name or select a tag to search.','请输入名字或选择标签进行搜索。','이름을 입력하거나 태그를 선택해 검색하세요.'],
 '表記で絞り込む':['Filter by writing system','按文字类型筛选','문자 종류로 필터링'],
 'すべての表記':['All writing systems','全部文字类型','모든 문자 종류'],
 'かなを含む':['Contains Japanese kana','包含日语假名','일본어 가나 포함'],
 '漢字を含む':['Contains Han characters','包含汉字','한자 포함'],
 '英字を含む':['Contains Latin letters','包含英文字母','영문자 포함'],
 '該当件数':['Records','记录数','해당 기록 수'],
 '割合':['Share','比例','비율'],
 '文字数の中央値':['Median length','字数中位数','글자 수 중앙값'],
 'よくある文字数':['Most common length','最常见字数','가장 흔한 글자 수'],
 'よく使われる先頭2文字':['Common first two characters','常见开头两字','자주 쓰이는 첫 두 글자'],
 'よく使われる末尾2文字':['Common last two characters','常见结尾两字','자주 쓰이는 마지막 두 글자'],
 '条件に一致する掲載がありません。':['No records match these filters.','没有符合条件的记录。','조건에 맞는 기록이 없습니다.'],
 '文字数・表記・よく使われる文字を、媒体やタグごとに比較できます。集計にAIの読み込みは不要です。':['Compare name lengths, writing systems and common characters by platform and tag. Analysis does not require loading AI.','按平台和标签比较名字长度、文字类型与常用文字。统计无需加载AI。','플랫폼과 태그별로 이름 길이, 문자 종류, 자주 쓰이는 글자를 비교합니다. 집계에는 AI 로딩이 필요 없습니다.'],
 '先頭・末尾は表示名の2文字を比較しています。苗字や語源の分類ではありません。漢字は各レコードで1回だけ数え、割合は選択中の集計対象に対する値です。':['First and last pairs are the two characters at each end of a display name, not inferred surnames or etymology. Each Han character is counted once per record. Shares use the selected records as their denominator.','开头与结尾比较的是显示名的两字，并非姓氏或词源分类。每个汉字在每条记录中仅计一次，比例以当前筛选记录为分母。','처음과 끝은 표시 이름의 두 글자를 비교하며 성씨나 어원을 분류하지 않습니다. 한자는 기록마다 한 번만 세며, 비율은 현재 선택한 기록을 기준으로 합니다.'],
 '傾向との比較':['Comparison with the data','与统计趋势比较','경향과 비교'],
 '同じ文字数の収録名':['Listed names of the same length','相同字数的收录名字','같은 글자 수의 수록 이름'],
 '集計対象内の件数です。名前の未使用を保証するものではありません。':['Counts within the selected records do not guarantee a name is unused.','这是筛选范围内的记录数，不保证名字未被使用。','집계 대상 내의 건수이며 이름이 사용되지 않았음을 보장하지 않습니다.'],
 '名前の候補を補っています…':['Generating the missing name ideas…','正在补充具体名字…','빠진 이름 후보를 생성하고 있습니다…'],
 '具体的な名前候補を生成できませんでした。希望を短くまとめて、もう一度相談してください。':['No concrete name ideas could be generated. Try again with a shorter request.','未能生成具体名字，请简要整理要求后再次咨询。','구체적인 이름 후보를 만들지 못했습니다. 원하는 내용을 짧게 정리해 다시 상담해 주세요.'],
 '回答が途中で終わったため、読み取れた内容を表示しています。':['The response ended early. The recoverable content is shown.','回答中途结束，当前显示可恢复的内容。','답변이 도중에 끝나 읽을 수 있는 내용을 표시합니다.'],
 '生成できた名前の候補です。':['Here are the available name ideas.','以下是已生成的名字候选。','생성된 이름 후보입니다.'],
 '希望に合わせた名前の候補です。':['Here are name ideas based on your preferences.','以下是根据您的要求生成的名字。','원하는 조건에 맞춘 이름 후보입니다.'],
 '回答を確認できませんでした。':['No usable answer was received.','未能取得有效回答。','사용할 수 있는 답변을 받지 못했습니다.']
})) ['en','zh','ko'].forEach((lang,i)=>translations[lang][jp]=values[i]);

for(const [jp,values] of Object.entries({
 'AIと活動名を考えて、同じ名前や読みもチェック。':['Create your name with AI, then check for matching names and readings.','与AI一起构思活动名，再确认是否存在同名或同读音。','AI와 활동명을 생각하고, 같은 이름과 발음도 확인하세요.'],
 '選択したタグでは一致する名前が見つかりませんでした。':['No matching names were found within the selected tag.','所选标签中未找到匹配的名字。','선택한 태그에서는 일치하는 이름을 찾지 못했습니다.']
})) ['en','zh','ko'].forEach((lang,i)=>translations[lang][jp]=values[i]);

translations.en["公式サイト"]="Official website";
translations.zh["公式サイト"]="官方网站";
translations.ko["公式サイト"]="공식 사이트";

for(const [jp,values] of Object.entries({
 '名前・読み・別名で検索':['Search names, readings or aliases','搜索名字、读音或别名','이름·발음·다른 표기 검색'],
 'クリア':['Clear','清除','지우기'],
 'タグ':['Tags','标签','태그'],
 '配信媒体':['Platforms','直播平台','방송 플랫폼'],
 'すべて':['All','全部','전체'],
 '活動者一覧':['Browse creators','创作者列表','활동자 목록'],
 '検索結果':['Search results','搜索结果','검색 결과'],
 '並べ替え':['Sort by','排序方式','정렬'],
 '人気順':['Popularity','人气顺序','인기순'],
 '名前順':['Name','名字顺序','이름순'],
 'ランダム':['Random','随机','무작위'],
 'もう一度シャッフル':['Shuffle again','重新随机排列','다시 섞기'],
 '人気順は確認できた登録者・フォロワー数が基準です。数値未確認の方は後ろに表示します。':['Popularity uses available subscriber and follower counts. Creators without counts appear afterwards.','人气顺序依据已确认的订阅者和关注者数量。未确认数量的创作者排在后面。','인기순은 확인된 구독자·팔로워 수 기준입니다. 수치가 없는 활동자는 뒤에 표시됩니다.'],
 '読み未確認':['Reading unverified','读音未确认','발음 미확인'],
 '詳細・出典':['Details & sources','详情与来源','상세 정보·출처'],
 'YouTube登録者':['YouTube subscribers','YouTube订阅者','YouTube 구독자'],
 'Twitchフォロワー':['Twitch followers','Twitch关注者','Twitch 팔로워'],
 '登録者・フォロワー数の出典':['Audience count source','订阅者与关注者数量来源','구독자·팔로워 수 출처'],
 '条件に一致する活動者が見つかりませんでした。':['No creators match these filters.','没有符合条件的创作者。','조건에 맞는 활동자를 찾지 못했습니다.'],
 '名前やタグ・配信媒体を変えてお試しください。':['Try another name, tag or platform.','请尝试其他名字、标签或平台。','이름·태그·플랫폼을 바꿔 보세요.'],
 'この条件では一致する名前が見つかりませんでした。未使用を保証する結果ではありません。':['No matching names under these filters. This does not guarantee a name is unused.','当前条件下没有匹配的名字。这不代表名字尚未被使用。','현재 조건에 일치하는 이름이 없습니다. 미사용을 보장하지는 않습니다.'],
 '一覧のページ':['Creator list pages','创作者列表分页','활동자 목록 페이지']
})) ['en','zh','ko'].forEach((lang,i)=>translations[lang][jp]=values[i]);

for(const [jp,values] of Object.entries({
 '検索欄に入力した名前は外部に送信されません。':['Names entered in the search box are not sent externally.','搜索框中输入的名字不会发送到外部。','검색창에 입력한 이름은 외부로 전송되지 않습니다.'],
 '登録内容や確認したチャンネル情報は、AIの学習に使わず、外部の生成AIサービスにも送りません。登録内容はサーバーに保存し、承認後に活動名や公開URLなどを掲載します。':['Registration details and checked channel information are not used to train AI or sent to external generative AI services. Submissions are stored on a server; approved names and public URLs are published.','登记内容及审核时参考的频道信息不会用于AI训练，也不会发送至外部生成式AI服务。登记内容会保存在服务器上，审核通过后将公开活动名及公开链接等信息。','등록 내용과 확인한 채널 정보는 AI 학습에 사용하거나 외부 생성형 AI 서비스에 보내지 않습니다. 등록 내용은 서버에 저장되며, 승인 후 활동명과 공개 URL 등이 게시됩니다.'],
 'まだ掲載されていませんか？':['Not listed yet?','还未收录？','아직 등록되지 않았나요?'],
 '自分の名前を登録':['Register your name','登记自己的名字','내 이름 등록'],
 '無料・ログイン不要。AIが公開プロフィールや活動実績を確認し、問題がなければ掲載します。':['Free, no login required. AI checks public profiles and activity before listing.','免费，无需登录。Gemma 4 E2B确认公开信息后，若无明显问题即可收录。','무료·로그인 불필요. Gemma 4 E2B가 공개 정보를 검토한 뒤 문제가 없으면 등록합니다.'],
 '利用者登録・AI確認':['User submission · AI screened','用户登记・AI初审','이용자 등록·AI 검토'],
 'Gemma 4 E2Bが登録内容を確認しました。本人確認や情報の正しさを保証するものではありません。':['Gemma 4 E2B screened this submission. This does not verify ownership or guarantee accuracy.','Gemma 4 E2B已初步审核登记内容，但不代表身份已核实或信息保证准确。','Gemma 4 E2B가 등록 내용을 검토했습니다. 본인 확인이나 정보의 정확성을 보장하지 않습니다.'],
 '利用者登録分を読み込めませんでした。既存の辞書は検索できます。時間をおいて再読み込みしてください。':['User registrations could not be loaded. The existing dictionary is available. Please reload later.','无法加载用户登记内容。仍可搜索现有词典，请稍后刷新。','이용자 등록 내용을 불러오지 못했습니다. 기존 사전은 검색할 수 있습니다. 나중에 새로고침해 주세요.']
})) ['en','zh','ko'].forEach((lang,i)=>translations[lang][jp]=values[i]);

for (const [jp, values] of Object.entries({
 "百科事典の出典：": ["Encyclopedia sources: ", "百科事典来源：", "백과사전 출처: "],
 "ピクシブ百科事典": ["Pixiv Encyclopedia", "Pixiv百科事典", "픽시브 백과사전"],
 "ニコニコ大百科": ["Niconico Encyclopedia", "Niconico大百科", "니코니코 대백과"]
})) ["en", "zh", "ko"].forEach((lang, i) => translations[lang][jp] = values[i]);

for(const [jp,values] of Object.entries({
 ' （推定）':[' (estimated)','（推测）',' (추정)'],
 '読み（推定）':['Reading (estimated)','读音（推测）','발음 (추정)'],
 '一致がなくても、名前が未使用とは限りません。確認済みの読みを優先し、補完した読みには「推定」と表示します。':['No match does not guarantee a name is unused. Verified readings take priority; supplemented readings are marked as estimated.','没有匹配结果不代表名字未被使用。优先使用已确认读音，补充读音标为推测。','검색 결과가 없어도 미사용을 보장하지 않습니다. 확인된 발음을 우선하며 보완한 발음에는 추정 표시가 붙습니다.'],
 '。全件の読みの確認は完了していません。推定の読みは実際と異なる場合があります。読み候補がない場合は「読み未確認」と表示します。':['. Not all readings have been verified. Estimated readings may differ from the actual pronunciation. Names without a candidate are marked as unverified.','。尚未确认所有读音。推测读音可能与实际不同。没有候选读音时显示未确认。','. 모든 발음을 확인하지는 못했습니다. 추정 발음은 실제와 다를 수 있으며 후보가 없으면 미확인으로 표시됩니다.']
})) ['en','zh','ko'].forEach((lang,i)=>translations[lang][jp]=values[i]);
for(const [jp,values] of Object.entries({
 '名前に含む文字':['Text in name','名字包含的文字','이름에 포함된 문자'],
 '例：星、ねこ':['e.g. 星, ねこ','例：星、ねこ','예: 星, ねこ'],
 '読みの確認状況':['Reading verification','读音确认状态','발음 확인 상태'],
 '確認済み':['Verified','已确认','확인됨'],
 '推定あり':['Estimated','有推测读音','추정 있음'],
 '未確認':['Unverified','未确认','미확인'],
 '集計をCSV保存':['Export summary CSV','导出统计CSV','통계 CSV 저장'],
 '異なる名前表記':['Distinct name spellings','不同名字表记','서로 다른 이름 표기'],
 '同じ名前表記のグループ':['Repeated spelling groups','相同表记的组数','동일 표기 그룹'],
 'よく使われるかな':['Common kana','常用假名','자주 쓰이는 가나'],
 '文字の組み合わせ・2文字':['Two-character combinations','两字组合','두 글자 조합'],
 '文字の組み合わせ・3文字':['Three-character combinations','三字组合','세 글자 조합'],
 '同じ名前表記の登録':['Records sharing a spelling','同名表记的记录','같은 이름 표기 등록'],
 '読みの登録状況':['Reading coverage','读音收录状态','발음 등록 현황'],
 '確認済みの読み':['Verified readings','已确认读音','확인된 발음'],
 '推定の読み':['Estimated readings','推测读音','추정 발음'],
 '読みの文字数':['Reading character length','读音字数','발음 글자 수'],
 '媒体ごとの比較':['Platform comparison','平台比较','플랫폼 비교'],
 'タグごとの比較':['Category comparison','分类比较','태그 비교'],
 '分類':['Group','分类','분류'],
 '件数':['Records','记录数','건수'],
 'かなを含む割合':['Names containing kana','包含假名的比例','가나 포함 비율'],
 '文字の組み合わせ・名前の重複・読みの登録状況まで、媒体やタグごとに比較できます。':['Compare character combinations, repeated names and reading coverage by platform or category.','按平台或分类比较文字组合、同名和读音收录情况。','플랫폼이나 태그별로 문자 조합, 이름 중복, 발음 등록 현황을 비교합니다.']
})) ['en','zh','ko'].forEach((lang,i)=>translations[lang][jp]=values[i]);

// Public reply-based listing requests.
for(const [jp,values] of Object.entries({"名前の掲載・修正を希望する方へ":["Request a listing or correction","申请收录或更正名字","이름 등재·수정 신청"],"Xの募集ポストへの返信で、①活動名 ②読み ③活動プラットフォームのURLをお知らせください。":["Reply to the recruitment post on X with: ① Activity name ② Name pronunciation ③ Activity platform URL.","请回复X上的征集帖，提供：①活动名 ②读音 ③活动平台URL。","X 모집 게시물에 ①활동명 ②읽는 법 ③활동 플랫폼 URL을 답글로 보내 주세요."],"返信内容は公開されます。公開してよい活動情報だけをお送りください。":["Replies are public. Send only activity information you are comfortable making public.","回复内容会公开。请只发送可以公开的活动信息。","답글은 공개됩니다. 공개해도 되는 활동 정보만 보내 주세요."],"内容を確認してから反映します。返信による自動登録は行いません。":["Requests are reviewed before being reflected. Replies are not registered automatically.","确认内容后再予以反映，回复不会自动登记。","내용 확인 후 반영합니다. 답글만으로 자동 등록되지는 않습니다."],"Xのリプ欄で申請する":["Apply in the X replies","前往X回复申请","X 답글로 신청"]})) ['en','zh','ko'].forEach((lang,i)=>translations[lang][jp]=values[i]);
