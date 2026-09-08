import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from agency321_sources import roster_urls, parse_profile

class Agency321Tests(unittest.TestCase):
    def test_active_roster_only(self):
        with self.assertRaises(ValueError):roster_urls('<a href="https://vliver.321.inc/liver/foo/">Foo</a>')
        self.assertEqual(roster_urls('活躍中の321所属Vライバー<a href="https://vliver.321.inc/liver/foo/">Foo REALITY</a><a href="https://evil.example/liver/bar/">Bar</a>'),['https://vliver.321.inc/liver/foo/'])

    def profile(self, name='架空テスト', link='https://reality.app/profile/abcd1234'):
        return f'<header><a href="https://x.com/agency">Agency</a></header><div class="catch-name"><h1>{name}</h1></div><div class="liver-profile"><div class="description">毎日配信しています</div><div class="delivery-account"><a href="{link}">配信</a></div><div class="sns-account"><a href="https://www.tiktok.com/@test">TikTok</a></div></div>'

    def test_person_scope_and_primary_platform(self):
        row=parse_profile(self.profile(),'https://vliver.321.inc/liver/test/')
        self.assertEqual(row['primary_platforms'],['reality'])
        self.assertEqual({a['platform'] for a in row['platform_accounts']},{'reality','tiktok'})
        self.assertNotIn('x',{a['platform'] for a in row['platform_accounts']})

    def test_predebut_and_missing_broadcast_skipped(self):
        self.assertIsNone(parse_profile(self.profile('VTuber準備中'),'https://vliver.321.inc/liver/test/'))
        self.assertIsNone(parse_profile(self.profile(link='https://x.com/test'),'https://vliver.321.inc/liver/test/'))
