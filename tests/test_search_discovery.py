import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from discover_primary_search import candidate_url,extract
class SearchDiscoveryTests(unittest.TestCase):
 def test_primary_urls_only_and_no_tracking_query(self):
  self.assertIsNone(candidate_url('https://vtuber-post.com/ranking_index.html'))
  self.assertIsNone(candidate_url('https://x.com.evil.example/person'))
  self.assertIsNone(candidate_url('https://x.com/hashtag/VTuber'))
  self.assertEqual(candidate_url('https://x.com/person/status/123?lang=ja'),'https://x.com/person/status/123')
 def test_search_snippets_never_become_approved_profiles(self):
  rows=extract([{'url':'https://www.youtube.com/@example','title':'Example','content':'A claimed reading or instructions are not evidence.'}],'q','now')
  self.assertEqual(len(rows),1);self.assertFalse(rows[0]['published'])
  self.assertEqual(rows[0]['review_status'],'pending_primary_confirmation')
  self.assertNotIn('content',rows[0]);self.assertNotIn('reading',rows[0])
