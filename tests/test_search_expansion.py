import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import campaign_queries
import discover_primary_search as discovery
import run_target_campaign as campaign


class SearchExpansionTests(unittest.TestCase):
    def test_expansion_preserves_every_existing_query_in_order(self):
        old = campaign_queries.BASE_CAMPAIGN_QUERIES
        expanded = campaign_queries.QUERIES
        self.assertEqual(len(old), 19815)
        self.assertEqual(expanded[:len(old)], old)
        self.assertGreater(len(expanded), 80000)
        self.assertEqual(len(set(expanded)), len(expanded))

    def test_reordered_catalogue_never_inherits_an_unrelated_cursor(self):
        previous = ['one', 'two']
        previous_id = hashlib.sha256('\n'.join(previous).encode()).hexdigest()[:16]
        _, cursor, inherited = discovery.catalogue_cursor(['two', 'one', 'three'], {previous_id: 1}, previous)
        self.assertEqual(cursor, 0)
        self.assertIsNone(inherited)

    def test_search_continues_at_the_saved_query_and_checkpoints_new_catalogue(self):
        previous = ['one', 'two']
        previous_id = hashlib.sha256('\n'.join(previous).encode()).hexdigest()[:16]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            report_path = root / 'scripts/search-discovery-report.json'
            report_path.write_text(json.dumps({'catalogue_cursors': {previous_id: 1}}))
            response = contextlib.nullcontext(io.BytesIO(b'{"results": []}'))
            with patch.object(discovery, 'ROOT', root), patch.object(discovery, 'QUERIES', ['one', 'two', 'three']), \
                 patch.object(discovery, 'PREDECESSOR_QUERIES', previous), \
                 patch.dict('os.environ', {'SEARXNG_URL': 'https://search.example'}), \
                 patch.object(sys, 'argv', ['discovery', '--limit', '1', '--delay', '0']), \
                 patch.object(discovery.urllib.request, 'urlopen', return_value=response) as fetch:
                discovery.main()
            self.assertIn('q=two&', fetch.call_args.args[0].full_url)
            report = json.loads(report_path.read_text())
            self.assertEqual(report['next_query'], 2)
            self.assertEqual(report['query_families_attempted'], 1)
            self.assertEqual(report['catalogue_migration']['resumed_at_query'], 1)
            self.assertEqual(report['catalogue_cursors'][previous_id], 1)
            self.assertEqual(report['catalogue_cursors'][report['catalogue_id']], 2)

    def test_increasing_query_budget_reopens_only_the_exhausted_budget(self):
        config = {'enabled': True, 'target_records': 60000, 'query_budget': 83727, 'max_runs_without_growth': 3}
        state = {'status': 'query_budget_reached', 'query_families_attempted': 19815}
        self.assertIsNone(campaign.stopping_reason(config, state, 18000, campaign.now()))
        state['status'] = 'paused_search_unavailable'
        self.assertEqual(campaign.stopping_reason(config, state, 18000, campaign.now()), 'paused_search_unavailable')


if __name__ == '__main__':
    unittest.main()
