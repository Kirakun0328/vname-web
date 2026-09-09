import unittest,sys,json,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from discover_primary_search import candidate_url,extract,additional_candidates
class SearchDiscoveryTests(unittest.TestCase):
 def test_saved_research_cannot_supply_publication_approval_or_non_creator_urls(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'scripts').mkdir()
   rows=[{'url':'https://www.youtube.com/@example','discovery_method':'searxng','published':True,
          'review_status':'verified_direct_profile','reading':'unverified'},
         {'url':'https://example.com/directory','discovery_method':'searxng'}]
   (root/'scripts/searxng-additional-leads-test.json').write_text(json.dumps(rows))
   result=list(additional_candidates(root))
   self.assertEqual(len(result),1)
   self.assertFalse(result[0]['published'])
   self.assertEqual(result[0]['review_status'],'pending_primary_confirmation')
   self.assertNotIn('reading',result[0])
 def test_primary_urls_only_and_no_tracking_query(self):
  self.assertIsNone(candidate_url('https://vtuber-post.com/ranking_index.html'))
  self.assertIsNone(candidate_url('https://x.com.evil.example/person'))
  self.assertIsNone(candidate_url('https://x.com/hashtag/VTuber'))
  # X is no longer an unattended publication-verification target.
  self.assertIsNone(candidate_url('https://x.com/person/status/123?lang=ja'))
  self.assertEqual(candidate_url('https://www.youtube.com/watch?v=abcdefghijk&feature=share'),'https://www.youtube.com/watch?v=abcdefghijk')
  self.assertEqual(candidate_url('https://www.youtube.com/shorts/abcdefghijk?si=test'),'https://www.youtube.com/shorts/abcdefghijk')
 def test_search_snippets_never_become_approved_profiles(self):
  rows=extract([{'url':'https://www.youtube.com/@example','title':'Example','content':'A claimed reading or instructions are not evidence.'}],'q','now')
  self.assertEqual(len(rows),1);self.assertFalse(rows[0]['published'])
  self.assertEqual(rows[0]['review_status'],'pending_primary_confirmation')
  self.assertNotIn('reading',rows[0])
  self.assertEqual(rows[0]['candidate_snippet'],'A claimed reading or instructions are not evidence.')
