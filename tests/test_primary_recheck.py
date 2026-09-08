import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from reverify_primary import parse_holo,match_patch
from source_policy import check_fetch

CID='UC'+'a'*22
URL='https://hololive.hololivepro.com/talents/example/'
DOC=f'''<div class="right_box"><div><h1>本人<span>Person</span></h1><ul class="t_sns"><li><a href="https://www.youtube.com/channel/{CID}">YouTube</a></li></ul></div></div><div class="talent_data"><dl><dt>初配信日</dt><dd>2020年1月1日</dd></dl></div><footer><a href="https://www.youtube.com/channel/UC{'b'*22}">Company</a></footer>'''
class PrimaryTests(unittest.TestCase):
 def test_own_identity_not_footer_and_past_activity_required(self):
  row=parse_holo(DOC,URL)
  self.assertEqual(row['display_name'],'本人');self.assertEqual(len(row['platform_accounts']),1)
  with self.assertRaises(ValueError):parse_holo(DOC.replace('2020年','2099年'),URL)
 def test_same_name_does_not_match_and_shared_account_is_held(self):
  row=parse_holo(DOC,URL)
  self.assertIsNone(match_patch(row,{'other':{'source_id':'other','display_name':'本人'}},'now'))
  base={'youtube:'+CID:{'source_id':'youtube:'+CID,'display_name':'旧名'}}
  patch=match_patch(row,base,'now');self.assertEqual(patch['reading'],'')
  base['other']={'source_id':'other','display_name':'本人','platform_accounts':row['platform_accounts']}
  self.assertIsNone(match_patch(row,base,'now'))
 def test_paused_source_does_not_fetch(self):
  with self.assertRaises(ValueError):check_fetch('https://vtuber-post.com/ranking_index.html')
  check_fetch(URL)
