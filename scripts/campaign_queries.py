"""Deterministic, multilingual discovery of creator-owned pages via SearXNG.

This is a search plan, not a creator list. No names are fabricated or published
from queries/snippets. Every candidate retains the existing primary-source gate.
"""
import sys
from itertools import zip_longest

import ultra_searxng_discovery as ultra

LANGUAGES = {
    'ja': ['VTuber', '個人勢VTuber', 'Vライバー', 'VSinger'],
    'en': ['indie VTuber', 'independent VTuber', 'virtual streamer', 'VSinger'],
    'zh-Hant': ['台灣 VTuber', '虛擬實況主', '香港 VTuber'],
    'zh-Hans': ['虚拟主播', '个人势 VTuber', '虚拟UP主'],
    'ko': ['버튜버', '개인 버튜버', '버츄얼 스트리머'],
    'es': ['VTuber español', 'VTuber latino', 'VTuber independiente'],
    'pt': ['VTuber Brasil', 'VTuber português', 'VTuber independente'],
    'id': ['VTuber Indonesia', 'VTuber independen'],
    'th': ['วีทูบเบอร์', 'VTuber ไทย'],
    'vi': ['VTuber Việt Nam', 'VTuber Việt'],
    'fr': ['VTuber français', 'VTuber francophone'],
    'de': ['deutscher VTuber', 'VTuber deutsch'],
    'ru': ['витубер', 'VTuber русский'],
}
PLATFORMS = [
    'youtube.com/@', 'youtube.com/channel', 'twitch.tv', 'tiktok.com/@',
    'web.iriam.app/s/user', 'reality.app/profile', 's.avvy.live/u',
    'showroom-live.com', '17.live', 'mirrativ.com/user', 'twitcasting.tv',
    'nicovideo.jp/user', 'spooncast.net', 'topia.tv/p', 'user.topia.tv',
    'palmu.me/users', 'app.palmu.jp/users', 'mixch.tv/u',
    'pococha.com/app/users', 'whowatch.tv/profile', 'kick.com',
    'web.colorsing.com/share/user', 'chzzk.naver.com', 'ch.sooplive.co.kr',
    'rplay.live', 'bigo.tv', 'stand.fm/channels', 'radiotalk.jp/program',
]
AI_TERMS = ['AIVTuber', 'AITuber', 'AI VTuber', 'AIライバー', 'AI Vライバー',
            'AI streamer', 'AI virtual streamer', '自律型AI VTuber',
            'AIキャラクター 配信', 'AI 虚拟主播', 'AI 버튜버']
TOPICS = ultra.unique(ultra.topics + [
    'Minecraft', 'Roblox', 'Stardew Valley', 'Terraria', 'Genshin Impact',
    'Honkai Star Rail', 'Final Fantasy XIV', 'Pokémon', 'Splatoon', 'Elden Ring',
    'Dark Souls', 'R.E.P.O.', 'Among Us', 'Lethal Company', 'VRChat', 'Chatting',
    'karaoke', 'drawing', 'art stream', 'cozy games', 'music', 'ASMR',
])


def build_base_queries():
    ai = [f'{prefix} "{term}"' for term in AI_TERMS
          for prefix in ['!yt'] + ['site:' + host for host in PLATFORMS]]
    media = [f'site:{host} "{term}" "{topic}"'
             for topic in ['配信', '初配信', '雑談', '歌', 'ゲーム', 'デビュー',
                           '個人勢', '自己紹介', 'stream', 'debut', 'live']
             for host in PLATFORMS
             for term in ['VTuber', 'Vライバー', 'VSinger']]
    # Use internationally searchable game/topic spellings across languages;
    # Japanese specialist terms stay in the original Japanese catalogue.
    international_topics = [topic for topic in TOPICS if topic.isascii()]
    international = [f'{prefix} "{term}" "{topic}"'
                     for topic in international_topics
                     for terms in LANGUAGES.values() for term in terms
                     for prefix in ['!yt', 'site:youtube.com/@', 'site:twitch.tv']]
    historical = [f'{prefix} "{term}" "{year}年{month}月"'
                  for year in reversed(range(2016, 2027)) for month in reversed(range(1, 13))
                  if (year, month) <= (2026, 9)
                  for term in ['VTuber 初配信', 'VTuber デビュー', 'Vライバー 初配信', 'AIVTuber']
                  for prefix in ['!yt', 'site:youtube.com/@']]
    # Interleave media, AI, languages, debut dates and the previous specialist
    # catalogue so short executions also reach every discovery family.
    language_basics = [f'{prefix} "{terms[0]}"' for prefix in
                       ['!yt', 'site:youtube.com/@', 'site:twitch.tv', 'site:youtube.com/channel']
                       for terms in LANGUAGES.values()]
    return ultra.unique(q for group in zip_longest(ai, media, language_basics,
                         international, historical, ultra.discovery.QUERIES) for q in group if q)


BASE_CAMPAIGN_QUERIES = build_base_queries()


def build_queries():
    # Append-only expansion lets the existing search cursor retain its exact
    # meaning. Do not reshuffle or restart already checked query families.
    topics = [topic for topic in TOPICS if topic.isascii()]
    regional = [f'{prefix} {region} "{topic}"'
                for topic in topics for region in ultra.INTERNATIONAL_TERMS
                for prefix in ['!yt', 'site:youtube.com/@', 'site:twitch.tv', 'site:tiktok.com/@']]
    multilingual_media = [f'site:{host} {term} "{topic}"'
                          for topic in topics for terms in LANGUAGES.values() for term in terms
                          for host in ['youtube.com/channel', 'tiktok.com/@', 'kick.com', 'chzzk.naver.com']]
    years = [f'{prefix} {term} "{year}"'
             for year in reversed(range(2016, 2027))
             for terms in LANGUAGES.values() for term in terms
             for prefix in ['!yt', 'site:youtube.com/@', 'site:twitch.tv']]
    ai_topics = [f'{prefix} {term} "{topic}"'
                 for topic in topics for term in AI_TERMS
                 for prefix in ['!yt', 'site:youtube.com/@', 'site:twitch.tv', 'site:tiktok.com/@']]
    additions = [q for group in zip_longest(regional, multilingual_media, years, ai_topics)
                 for q in group if q]
    return ultra.unique([*BASE_CAMPAIGN_QUERIES, *additions])


QUERIES = build_queries()

if __name__ == '__main__':
    ultra.discovery.QUERIES = QUERIES
    ultra.discovery.PREDECESSOR_QUERIES = BASE_CAMPAIGN_QUERIES
    print(f'Campaign query catalogue: {len(QUERIES)} families', flush=True)
    ultra.discovery.main()
