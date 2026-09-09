"""Run a broad SearXNG discovery sweep for specialist/regional VTubers.

This module only expands discovery queries. Publication still goes through
verify_searxng_candidates.py, which must fetch a direct creator/platform page.
"""
import sys
import discover_primary_search as discovery

SPECIALTIES = [
    # Medicine / health / care
    '医療','医師','看護師','薬剤師','歯科医師','歯科衛生士','獣医','臨床検査技師','診療放射線技師','理学療法士','作業療法士','言語聴覚士','管理栄養士','栄養士','心理士','公認心理師','カウンセラー','精神科','脳科学','健康','筋トレ','フィットネス','睡眠','介護','福祉',
    # Law / public / finance / business
    '法律','弁護士','司法書士','行政書士','社労士','税理士','公認会計士','会計','簿記','FP','金融','投資','経済','経営','起業','マーケティング','広告','人事','採用','広報','不動産','保険','銀行','証券','自治体','公務員','地方創生',
    # Science / academia
    '数学','物理','化学','生物','生命科学','医学','薬学','農学','地学','地質学','気象','天文','宇宙','科学','研究者','博士','大学院','統計学','データ分析','心理学','社会学','哲学','倫理学','宗教学','考古学','民俗学','文化人類学','歴史学','日本史','世界史','地理','言語学','文学','古典','美術史','博物館','学芸員','恐竜','昆虫','植物','海洋','深海','鳥類','魚類','菌類',
    # Education / languages
    '教育','教師','教員','塾講師','受験','勉強','英語','英会話','日本語教育','中国語','韓国語','フランス語','ドイツ語','スペイン語','イタリア語','ロシア語','ラテン語','手話','資格勉強',
    # Tech / engineering / manufacturing
    'エンジニア','プログラミング','Python','JavaScript','Rust','C++','Linux','OSS','AI','生成AI','機械学習','深層学習','データサイエンス','サイバーセキュリティ','ネットワーク','クラウド','AWS','Azure','GCP','Web開発','ゲーム開発','Unity','Unreal Engine','Godot','Blender','3DCG','VR','XR','メタバース','電子工作','ロボット','半導体','電気','電子工学','機械工学','建築','土木','ものづくり','3Dプリンタ','CAD','ドローン','無線','アマチュア無線',
    # Creative / media / music
    'イラスト','漫画','アニメ','映像制作','動画編集','写真','カメラ','デザイン','UIデザイン','Webデザイン','小説','脚本','創作','同人','作曲','DTM','ボカロ','歌','ピアノ','ギター','ベース','ドラム','バイオリン','クラシック','ジャズ','音楽理論','MIX','声優','演技','朗読','落語','演劇',
    # Food / lifestyle / crafts
    '料理','寿司','ラーメン','カレー','パン','お菓子','製菓','コーヒー','紅茶','日本茶','日本酒','ワイン','ウイスキー','ビール','農業','畜産','漁業','園芸','家庭菜園','DIY','木工','手芸','裁縫','ファッション','美容','コスメ','香水','文房具','時計','ガジェット',
    # Transport / outdoors / travel
    '鉄道','新幹線','航空','飛行機','空港','船','船舶','自動車','車','バイク','モータースポーツ','道路','交通','旅行','観光','温泉','ホテル','キャンプ','登山','アウトドア','釣り','自転車','ロードバイク',
    # Games / competition / hobbies
    'レトロゲーム','RTA','格ゲー','FPS','TPS','音ゲー','カードゲーム','TCG','TRPG','ボードゲーム','麻雀','将棋','囲碁','チェス','ポーカー','競馬','競輪','野球','サッカー','バスケ','バレー','テニス','卓球','ゴルフ','プロレス','格闘技','柔道','剣道','弓道','筋トレ','Minecraft','ポケモン','原神','FF14','ストリートファイター','スプラトゥーン',
    # Culture / niche
    '神話','妖怪','怪談','オカルト','都市伝説','占い','タロット','星占い','寺','神社','仏教','城','刀剣','軍事','ミリタリー','防災','災害','地震','天気','動物','猫','犬','爬虫類','水族館','動物園','宝石','鉱物','化石','宇宙開発','特撮','プラモデル','模型',
    # International / English specialist discovery
    'science','mathematics','physics','chemistry','biology','medicine','doctor','nurse','law','lawyer','history','archaeology','linguistics','programming','software engineer','cybersecurity','machine learning','AI','astronomy','space','railway','aviation','marine biology','education','teacher','finance','economics','music theory','indie game developer',
]

PREFECTURES = ['北海道','青森','岩手','宮城','秋田','山形','福島','茨城','栃木','群馬','埼玉','千葉','東京','神奈川','新潟','富山','石川','福井','山梨','長野','岐阜','静岡','愛知','三重','滋賀','京都','大阪','兵庫','奈良','和歌山','鳥取','島根','岡山','広島','山口','徳島','香川','愛媛','高知','福岡','佐賀','長崎','熊本','大分','宮崎','鹿児島','沖縄']

# YouTube video search gives high recall for actual activity, while general web
# channel searches are better at resolving channel/profile pages. Both are kept.
queries = list(discovery.BASE_QUERIES)
for term in dict.fromkeys(SPECIALTIES):
    queries.extend([
        f'!yt "{term}" VTuber',
        f'site:youtube.com/@ "{term}" VTuber',
    ])
for place in PREFECTURES:
    queries.extend([
        f'!yt "{place}" VTuber',
        f'site:youtube.com/@ "{place}" VTuber',
    ])

# Additional platform-oriented discovery. These remain leads only.
queries.extend([
    'site:twitch.tv "専門" VTuber',
    'site:twitch.tv "解説" VTuber',
    'site:tiktok.com/@ "専門" VTuber',
    'site:showroom-live.com "専門" Vライバー',
    'site:web.iriam.app/s/user "専門"',
    'site:reality.app/profile "専門"',
    'site:17.live/profile "Vライバー"',
    'site:mirrativ.com/user "Vライバー"',
])

discovery.QUERIES = list(dict.fromkeys(queries))

if __name__ == '__main__':
    # Process the entire catalogue unless explicit discovery args are supplied.
    if len(sys.argv) == 1:
        sys.argv.extend(['--limit', str(len(discovery.QUERIES)), '--pages', '2'])
    discovery.main()
