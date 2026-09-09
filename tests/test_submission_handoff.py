"""Check saved campaign handoff and the public 17LIVE URL forms supplied by creators."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run_ultra_sweep as sweep
from platform_sources import canonical_account


class SubmissionHandoffTests(unittest.TestCase):
    def test_resume_retains_saved_progress(self):
        saved = sweep.initial_report(1800, 3)
        saved.update(run_id='previous', query_families_attempted=960,
                     query_requests=1320, new_public_records=110,
                     batches=[{'number': 8}], status='running')
        with patch.object(sweep, 'read_report', return_value=copy.deepcopy(saved)):
            resumed = sweep.initial_report(1800, 3, resume=True)
        for key in ('started_at', 'query_families_attempted', 'query_requests',
                    'new_public_records', 'batches'):
            self.assertEqual(resumed[key], saved[key])
        self.assertEqual(resumed['resumed_runs'][0]['at_query'], 960)

    def test_resume_rejects_another_campaign(self):
        with patch.object(sweep, 'read_report', return_value=sweep.initial_report(1800, 3)):
            with self.assertRaises(ValueError):
                sweep.initial_report(600, 3, resume=True)

    def test_completed_campaign_does_not_restart(self):
        saved = sweep.initial_report(1800, 3)
        saved['query_families_attempted'] = 1800
        with patch.object(sweep, 'read_report', return_value=saved):
            self.assertEqual(sweep.initial_report(1800, 3, resume=True)['status'], 'completed')

    def test_17live_shared_profile_links(self):
        for suffix, ident in [('u/c3ea2a79-08b2-4010-980a-7604e31138a6', 'c3ea2a79-08b2-4010-980a-7604e31138a6'),
                              ('r/27820352', '27820352')]:
            url = 'https://17.live/ja/profile/' + suffix
            account = canonical_account(url + '?pid=InappShare')
            self.assertEqual(account, {'platform': '17live', 'id': ident, 'url': url})
        self.assertIsNone(canonical_account('https://17.live/ja/profile/u/id/videos'))


if __name__ == '__main__':
    unittest.main()
