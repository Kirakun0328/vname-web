import datetime
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import profile_backoff as backoff
import verify_searxng_candidates as verifier


class ProfileBackoffTests(unittest.TestCase):
    def test_retry_after_survives_a_fresh_process_state_and_covers_host_aliases(self):
        timestamp = datetime.datetime(2026, 9, 9, 7, tzinfo=datetime.timezone.utc)
        with tempfile.TemporaryDirectory() as directory, patch.object(backoff, 'HOSTS', {}), \
             patch.object(backoff, 'PATH', Path(directory) / 'backoff.json'), \
             patch.object(backoff, 'now', return_value=timestamp):
            backoff.pause('https://www.youtube.com/@creator', 429, '7200')
            backoff.HOSTS = {}
            backoff.load()
            self.assertTrue(backoff.blocked('https://m.youtube.com/@creator'))
            self.assertTrue(backoff.blocked('https://youtu.be/abcdefghijk'))
            self.assertFalse(backoff.blocked('https://twitch.tv/creator'))
            with patch.object(backoff, 'now', return_value=timestamp + datetime.timedelta(hours=2, seconds=1)):
                self.assertFalse(backoff.blocked('https://youtube.com/@creator'))

    def test_host_wait_does_not_turn_the_candidate_into_a_rejection(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(backoff, 'HOSTS', {}), \
             patch.object(backoff, 'PATH', Path(directory) / 'backoff.json'):
            root = Path(directory)
            queue = root / 'queue.json'
            report = root / 'report.json'
            queue.write_text(json.dumps([{'url': 'https://youtube.com/@creator',
                                         'review_status': 'pending_primary_confirmation'}]))
            backoff.pause('https://youtube.com', 429)
            with patch.object(verifier, 'QUEUE', queue), patch.object(verifier, 'REPORT', report), \
                 patch.object(sys, 'argv', ['verify']), patch.object(verifier, 'fetch_page') as fetch:
                verifier.main()
            fetch.assert_not_called()
            self.assertEqual(json.loads(queue.read_text())[0]['review_status'], 'pending_primary_confirmation')
            self.assertEqual(json.loads(report.read_text())['deferred_host_backoff'], 1)
            self.assertEqual(json.loads(report.read_text())['attempted_this_run'], 0)

    def test_only_the_known_limited_batch_is_recovered(self):
        with patch.object(backoff, 'HOSTS', {'youtube.com': {'legacy_verification_batch': 'known'}}):
            row = {'url': 'https://www.youtube.com/@creator', 'verified_at': 'known',
                   'review_status': 'unavailable', 'verification_status': 'unavailable:ValueError'}
            self.assertTrue(backoff.recover_legacy_candidate(row))
            self.assertEqual(row['review_status'], 'pending_primary_confirmation')
            other = {**row, 'verified_at': 'other', 'verification_status': 'unavailable:ValueError'}
            self.assertFalse(backoff.recover_legacy_candidate(other))


if __name__ == '__main__':
    unittest.main()
