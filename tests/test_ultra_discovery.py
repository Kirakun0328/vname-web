import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import discover_primary_search as discovery
import verify_searxng_candidates as verifier
import estimate_readings


class UltraDiscoveryTests(unittest.TestCase):
    def test_failed_search_keeps_cursor_and_reports_actual_attempts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            response = contextlib.nullcontext(io.BytesIO(json.dumps({'results':[
                {'url':'https://youtube.com/@creator', 'title':'Creator VTuber'}]}).encode()))
            with patch.object(discovery, 'ROOT', root), patch.object(discovery, 'QUERIES', ['one','two','three']), \
                 patch.dict('os.environ', {'SEARXNG_URL':'https://search.example'}), \
                 patch.object(sys, 'argv', ['discovery','--limit','3','--delay','0']), \
                 patch.object(discovery.urllib.request, 'urlopen', side_effect=[response,OSError('offline')]):
                discovery.main()
            report = json.loads((root/'scripts/search-discovery-report.json').read_text())
            self.assertEqual(report['query_families_attempted'], 2)
            self.assertEqual(report['next_query'], 1)
            self.assertEqual(report['status'], 'source_unavailable')
            self.assertEqual(report['new_candidates'], 1)
            self.assertFalse(json.loads((root/'scripts/searxng-candidates.json').read_text())[0]['published'])

    def test_recommendations_are_not_creator_identity(self):
        document = '<meta property="og:title" content="Ordinary channel"><meta name="description" content="A gamer">' \
                   '<script>{"recommendation":"AIVTuber","videoRenderer":{}}</script>'
        with patch.object(verifier, 'fetch_page', return_value=document):
            _, row, status = verifier.verify_one({'url':'https://youtube.com/@gamer'})
        self.assertIsNone(row)
        self.assertEqual(status, 'no_direct_vtuber_evidence')

    def test_profile_needs_started_activity_and_does_not_infer_reading(self):
        profile = '<meta property="og:title" content="Test AI - YouTube">' \
                  '<meta name="description" content="AIVTuberです">' \
                  '<script>{"externalId":"UC' + 'a'*22 + '"}</script>'
        candidate = {'url':'https://youtube.com/@testai'}
        with patch.object(verifier, 'fetch_page', return_value=profile):
            self.assertEqual(verifier.verify_one(candidate)[2], 'activity_unconfirmed')
        with patch.object(verifier, 'fetch_page', return_value=profile+'<script>{"videoRenderer":{}}</script>'):
            _, row, status = verifier.verify_one(candidate)
        self.assertEqual(status, 'verified')
        self.assertEqual(row['category'], 'AIVTuber')
        self.assertNotIn('reading', row)

    def test_avatar_platform_profile_alone_does_not_prove_activity(self):
        self.assertIsNone(verifier.activity_evidence('', 'よろしくお願いします', 'reality'))
        self.assertEqual(verifier.activity_evidence('', '毎日配信しています', 'reality'),
                         'creator_profile_describes_started_activity')

    def test_empty_batch_preserves_accumulated_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            queue = Path(directory)/'queue.json'
            report = Path(directory)/'report.json'
            queue.write_text('[]')
            report.write_text(json.dumps({'cumulative_since_checkpoint_fix':{'new_public_records':71}}))
            with patch.object(verifier, 'QUEUE', queue), patch.object(verifier, 'REPORT', report), \
                 patch.object(sys, 'argv', ['verify']):
                verifier.main()
            self.assertEqual(json.loads(report.read_text())['cumulative_since_checkpoint_fix']['new_public_records'],71)

    def test_orphan_metadata_does_not_crash_reading_queue(self):
        with patch.object(estimate_readings, 'read_js', return_value=[{'source_id':'orphan','category':'VTuber'}]), \
             patch.object(estimate_readings, 'read_object', return_value={}), \
             patch.object(estimate_readings, 'download') as download, \
             patch.object(sys, 'argv', ['estimate','--limit','0']):
            estimate_readings.main()
        download.assert_not_called()

    def test_first_batch_covers_ai_and_non_youtube_platforms(self):
        import ultra_searxng_discovery
        first = '\n'.join(ultra_searxng_discovery.discovery.QUERIES[:120])
        for term in ('AIVTuber','AITuber','twitch.tv','tiktok.com','web.iriam.app','reality.app','s.avvy.live'):
            self.assertIn(term, first)


if __name__ == '__main__':
    unittest.main()
