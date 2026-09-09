"""Ultra-scale SearXNG discovery catalogue for long-tail VTuber/V-liver leads.

This module only expands search coverage. Search results remain leads only;
publication still requires direct creator/profile verification by
verify_searxng_candidates.py.
"""
import sys

import discover_primary_search as discovery
import mass_searxng_discovery as mass


def unique(values):
    return list(dict.fromkeys(value.strip() for value in values if value and value.strip()))


EXTRA_SPECIALTIES = [
    # Streaming / creator formats
    'ASMR','睡眠導入','作業配信','朝活','深夜配信','耐久配信','歌枠','弾き語り','カラオケ','DJ','ラジオ','ポッドキャスト','雑談','ゲーム実況','同時視聴','ウォッチパーティ','朗読劇','シチュエーションボイス','声劇','ボイスドラマ','MMD','Live2D','VRM','モーションキャプチャ','フルトラ','トラッキング','配信技術','OBS','動画制作','ショート動画','Shorts',
    # Games / esports long tail
    'eスポーツ','esports','VALORANT','Apex Legends','Fortnite','Overwatch','League of Legends','LoL','Dota 2','Counter-Strike','Rainbow Six Siege','PUBG','Escape from Tarkov','Dead by Daylight','モンスターハンター','モンハン','ドラクエ','ドラゴンクエスト','ゼルダ','マリオ','カービィ','ソニック','ペルソナ','テイルズ','アトリエ','龍が如く','東方Project','ブルーアーカイブ','ブルアカ','崩壊スターレイル','ゼンレスゾーンゼロ','FGO','グラブル','ウマ娘','シャドウバース','遊戯王','デュエルマスターズ','Magic The Gathering','MTG','Warhammer','シミュレーションゲーム','ストラテジー','インディーゲーム','ホラーゲーム','ノベルゲーム','乙女ゲーム','美少女ゲーム',
    # Professional / technical long tail
    '医療事務','救急救命士','助産師','保健師','柔道整復師','鍼灸師','整体','スポーツ科学','トレーナー','薬膳','公衆衛生','疫学','バイオインフォマティクス','遺伝学','神経科学','認知科学','量子力学','素粒子','宇宙物理','材料工学','化学工学','情報工学','制御工学','航空宇宙工学','自動車工学','船舶工学','都市工学','測量','GIS','地図','気象予報士','防災士','司書','図書館','アーキビスト','翻訳','通訳','校正','編集者','記者','ジャーナリスト','放送','映像','映画','映画評論','アニメ評論','ゲーム評論','書評','評論','特許','弁理士','中小企業診断士','宅建','不動産鑑定士','証券アナリスト','デイトレード','暗号資産','Web3','ブロックチェーン','スタートアップ','SaaS','プロダクトマネジメント','PM','UX','UXデザイン','アクセシビリティ','セキュリティエンジニア','CTF','競技プログラミング','アルゴリズム','AtCoder','データベース','SQL','DevOps','SRE','Docker','Kubernetes','Raspberry Pi','Arduino','FPGA','自作PC','PCパーツ','オーディオ','イヤホン','ヘッドホン','キーボード','ガジェットレビュー',
    # Arts / lifestyle / niche
    '書道','茶道','華道','着物','和服','日本舞踊','能','狂言','歌舞伎','俳句','短歌','詩','陶芸','レザークラフト','刺繍','編み物','模型鉄道','ジオラマ','ミニ四駆','ラジコン','ドール','フィギュア','コスプレ','サバゲー','エアソフト','キャンピングカー','車中泊','離島','世界遺産','廃墟','地理院地図','地形','火山','台風','気候','自然観察','バードウォッチング','昆虫採集','きのこ','菌類','苔','多肉植物','アクアリウム','熱帯魚','爬虫類','両生類','競技クイズ','クイズ','謎解き','脱出ゲーム','マジック','手品','ジャグリング','大道芸','筋トレ','ボディビル','パワーリフティング','ランニング','マラソン','トライアスロン','サーフィン','スキー','スノーボード','スケート','eスポーツ実況','スポーツ実況',
]

JAPAN_CITIES = [
    '札幌','函館','旭川','帯広','釧路','青森市','八戸','盛岡','仙台','秋田市','山形市','福島市','郡山','いわき','水戸','つくば','宇都宮','前橋','高崎','さいたま','川越','越谷','千葉市','船橋','柏','市川','浦安','松戸','東京','新宿','渋谷','秋葉原','池袋','八王子','町田','横浜','川崎','相模原','横須賀','湘南','鎌倉','新潟市','長岡','富山市','高岡','金沢','福井市','甲府','長野市','松本','岐阜市','高山','静岡市','浜松','名古屋','豊橋','岡崎','一宮','豊田','津','四日市','大津','京都市','宇治','大阪市','堺','東大阪','神戸','姫路','西宮','尼崎','奈良市','和歌山市','鳥取市','米子','松江','出雲','岡山市','倉敷','広島市','福山','呉','山口市','下関','徳島市','高松','松山','今治','高知市','北九州','福岡市','久留米','佐賀市','長崎市','佐世保','熊本市','大分市','別府','宮崎市','鹿児島市','那覇','沖縄市','石垣島','宮古島',
    '東北','関東','首都圏','北関東','南関東','甲信越','北陸','東海','中部','近畿','関西','中国地方','四国','九州','沖縄','北海道',
]

INTERNATIONAL_TERMS = [
    'EN VTuber','English VTuber','indie VTuber','small VTuber','new VTuber','male VTuber','female VTuber','VSinger','virtual streamer','virtual creator',
    'US VTuber','USA VTuber','Canada VTuber','UK VTuber','British VTuber','Ireland VTuber','Australia VTuber','New Zealand VTuber',
    'France VTuber','French VTuber','Germany VTuber','German VTuber','Spain VTuber','Spanish VTuber','Portugal VTuber','Portuguese VTuber','Italy VTuber','Italian VTuber','Netherlands VTuber','Dutch VTuber','Belgium VTuber','Sweden VTuber','Norway VTuber','Finland VTuber','Denmark VTuber','Poland VTuber','Czech VTuber','Romania VTuber','Hungary VTuber','Greece VTuber','Ukraine VTuber','Russia VTuber','Russian VTuber','Turkey VTuber',
    'Brazil VTuber','VTuber Brasil','Mexico VTuber','VTuber México','Argentina VTuber','Chile VTuber','Colombia VTuber','Peru VTuber','Latam VTuber','LATAM VTuber','VTuber latino','VTuber español',
    'Indonesia VTuber','VTuber Indonesia','Malaysia VTuber','Singapore VTuber','Philippines VTuber','Filipino VTuber','Thailand VTuber','Thai VTuber','Vietnam VTuber','VTuber Việt Nam','India VTuber','Pakistan VTuber','Bangladesh VTuber','Nepal VTuber','Sri Lanka VTuber',
    'Taiwan VTuber','台灣 VTuber','台灣Vtuber','香港 VTuber','Hong Kong VTuber','Korea VTuber','Korean VTuber','버튜버','버츄얼 유튜버','중소 버튜버','개인 버튜버','虚拟主播','虚拟YouTuber','虚拟UP主','个人势Vtuber','個人勢Vtuber',
    'Arabic VTuber','Middle East VTuber','Saudi VTuber','UAE VTuber','Israel VTuber','Egypt VTuber','South Africa VTuber','Africa VTuber',
]

DISCOVERY_PHRASES = [
    '新人VTuber','個人勢VTuber','個人VTuber','男性VTuber','女性VTuber','バ美肉VTuber','セルフ受肉VTuber','ご当地VTuber','地域VTuber','企業勢VTuber','学生VTuber','社会人VTuber','専門VTuber','解説VTuber','教育VTuber','学術VTuber','研究VTuber','技術VTuber','クリエイターVTuber','音楽VTuber','歌うVTuber','ゲームVTuber','ASMR VTuber','雑談VTuber','朝活VTuber','深夜VTuber','VRChat VTuber','3D VTuber','Live2D VTuber','AIVTuber','AI VTuber','Vライバー','個人勢Vライバー','新人Vライバー','VSinger','個人VSinger',
    'VTuber 自己紹介','VTuber 初配信','VTuber デビュー','VTuber 100の質問','VTuber shorts','VTuber ショート','VTuber 配信','VTuber 生放送','VTuber 雑談','VTuber 歌枠','VTuber ゲーム実況','VTuber お絵描き','VTuber 作業配信','VTuber 耐久','VTuber コラボ','VTuber 切り抜き禁止',
    'indie vtuber debut','indie vtuber introduction','small vtuber stream','new vtuber debut','vtuber self introduction','vtuber livestream','independent vtuber',
]

OTHER_PLATFORM_TERMS = [
    'VTuber','Vライバー','個人勢VTuber','新人VTuber','個人勢Vライバー','AIVTuber','VSinger','バーチャルライバー',
]

# Build a large but deterministic catalogue. Channel-page searches are included
# heavily because they produce higher-quality leads than video-only search.
queries = list(discovery.BASE_QUERIES)

topics = unique([*mass.SPECIALTIES, *EXTRA_SPECIALTIES])
for term in topics:
    queries.extend([
        f'!yt "{term}" VTuber',
        f'!yt "{term}" "個人勢VTuber"',
        f'!yt "{term}" Vライバー',
        f'site:youtube.com/@ "{term}" VTuber',
        f'site:youtube.com/channel "{term}" VTuber',
        f'site:youtube.com/@ "{term}" "個人勢VTuber"',
        f'site:youtube.com/@ "{term}" Vライバー',
    ])

locations = unique([*mass.PREFECTURES, *JAPAN_CITIES])
for place in locations:
    queries.extend([
        f'!yt "{place}" VTuber',
        f'!yt "{place}" "ご当地VTuber"',
        f'!yt "{place}" Vライバー',
        f'site:youtube.com/@ "{place}" VTuber',
        f'site:youtube.com/channel "{place}" VTuber',
        f'site:youtube.com/@ "{place}" "ご当地VTuber"',
        f'site:youtube.com/@ "{place}" Vライバー',
    ])

for phrase in unique(DISCOVERY_PHRASES):
    queries.extend([
        f'!yt "{phrase}"',
        f'site:youtube.com/@ "{phrase}"',
        f'site:youtube.com/channel "{phrase}"',
    ])

for term in unique(INTERNATIONAL_TERMS):
    queries.extend([
        f'!yt "{term}"',
        f'site:youtube.com/@ "{term}"',
        f'site:youtube.com/channel "{term}"',
        f'site:twitch.tv "{term}"',
    ])

for term in OTHER_PLATFORM_TERMS:
    queries.extend([
        f'site:twitch.tv "{term}"',
        f'site:tiktok.com/@ "{term}"',
        f'site:web.iriam.app/s/user "{term}"',
        f'site:reality.app/profile "{term}"',
        f'site:s.avvy.live/u "{term}"',
        f'site:showroom-live.com "{term}"',
        f'site:17.live/profile "{term}"',
        f'site:mirrativ.com/user "{term}"',
        f'site:twitcasting.tv "{term}"',
        f'site:nicovideo.jp/user "{term}"',
        f'site:spooncast.net/profile "{term}"',
        f'site:topia.tv/p "{term}"',
        f'site:palmu.me/users "{term}"',
        f'site:mixch.tv/u "{term}"',
        f'site:pococha.com/app/users "{term}"',
        f'site:whowatch.tv/profile "{term}"',
        f'site:kick.com "{term}"',
    ])

discovery.QUERIES = unique(queries)

if __name__ == '__main__':
    # The workflow supplies --limit/--pages so the catalogue can be traversed
    # over multiple runs without keeping a home-hosted SearXNG tunnel up all day.
    if len(sys.argv) == 1:
        sys.argv.extend(['--limit', '1800', '--pages', '3'])
    print(f'Ultra query catalogue: {len(discovery.QUERIES)} families', flush=True)
    discovery.main()
