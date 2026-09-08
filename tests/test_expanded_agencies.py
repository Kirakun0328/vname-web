import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from expanded_agencies import discover,parse_profile
class ExpandedTests(unittest.TestCase):
 def test_roster_pagination_stays_on_official_origin(self):
  profiles,pages=discover('<a href="/vliver/alice/">Alice</a><a href="/vliver/?page=2">2</a><a href="https://evil.test/vliver/b/">B</a>','novel')
  self.assertEqual(profiles,['https://novel-live.net/vliver/alice/']);self.assertEqual(pages,['https://novel-live.net/vliver/?page=2'])
 def test_award_profile_ignores_related_member_links(self):
  doc='<h1>花子</h1><div class="gt3_single_team_descr">バナイベ 3位<a href="https://twitter.com/hanako">X</a><a href="https://t.co/example">IRIAMアカウント</a></div><a href="https://twitter.com/other">他の所属者</a>'
  r=parse_profile(doc,'https://novel-live.net/vliver/hanako/','novel')
  self.assertEqual(r['primary_platforms'],['iriam']);self.assertEqual(len(r['platform_accounts']),1)
 def test_fan_letter_or_future_activity_does_not_establish_debut(self):
  doc='<h1>花子</h1><div class="gt3_single_team_descr">準備中<a href="https://twitter.com/hanako">X</a><a href="https://t.co/example">IRIAMアカウント</a></div><div>ファンレター 入賞 3位</div>'
  self.assertIsNone(parse_profile(doc,'https://novel-live.net/vliver/hanako/','novel'))
