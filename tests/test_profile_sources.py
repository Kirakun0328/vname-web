import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from vstats_sources import profile_views
from liverfun_sources import parse_profile, merge_profiles

CID = 'UC'+'a'*22
ROW = {'source_url':'https://www.liverfun.jp/vtuber/example/', 'display_name':'例VTuber', 'followers':52}


def profile(name='例VTuber', description='個人勢VTuberです。毎日配信中！', url=ROW['source_url']):
    data = {'@type':'Person','name':name,'description':description,'sameAs':['https://x.com/example']}
    return '<link rel="canonical" href="'+url+'"><script type="application/ld+json">'+json.dumps(data)+'</script>'


class ProfileSourcesTest(unittest.TestCase):
    def test_views_require_matching_channel(self):
        html = '<a href="https://www.youtube.com/channel/'+CID+'">channel</a>総再生回数</span><span>1,234</span>'
        self.assertEqual(profile_views(html,CID),1234)
        with self.assertRaises(ValueError):
            profile_views(html,'UC'+'b'*22)

    def test_preparing_in_bio_overrides_active_wording(self):
        self.assertIsNone(parse_profile(profile(description='VTuber準備中。声だけで毎日配信中！'),ROW))

    def test_ambiguous_debut_date_is_not_assumed_past(self):
        self.assertIsNone(parse_profile(profile(name='例VTuber@9/17デビュー'),ROW))

    def test_fan_and_intent_are_insufficient(self):
        self.assertIsNone(parse_profile(profile(name='ファン',description='VTuberが好き。毎日配信中！'),ROW))
        self.assertIsNone(parse_profile(profile(description='個人勢VTuberです。毎日配信したいです！'),ROW))
        self.assertIsNone(parse_profile(profile(description='個人勢VTuberです。配信を中心に活動予定です！'),ROW))
        self.assertIsNone(parse_profile(profile(description='個人勢VTuberです。ゲーム配信中心の予定です！'),ROW))

    def test_identity_and_explicit_activity(self):
        r = parse_profile(profile(),ROW)
        self.assertEqual(r['twitter_url'],'https://x.com/example')
        with self.assertRaises(ValueError):
            parse_profile(profile(url='https://www.liverfun.jp/vtuber/other/'),ROW)

    def test_duplicate_account_is_not_new_person(self):
        old = [{'source_id':'old','display_name':'旧名','twitter_url':'https://x.com/example','reading':'れい'}]
        extra, counts = merge_profiles(old,[],[parse_profile(profile(),ROW)],{})
        self.assertEqual(counts['new_records'],0)
        self.assertEqual(extra[0]['source_id'],'old')
        self.assertNotIn('reading',extra[0])
