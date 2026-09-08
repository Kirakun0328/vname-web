import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cleanup_legacy_external", ROOT / "scripts" / "cleanup_legacy_external.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SourcePolicyTests(unittest.TestCase):
    def test_pixiv_encyclopedia_is_preserved_reference(self):
        row = {
            "source_id": "youtube:example",
            "encyclopedia_sources": ["https://dic.pixiv.net/a/example"],
        }
        self.assertEqual(MODULE.reference_family(row), "user_encyclopedia")
        self.assertFalse(MODULE.risky_added_record(row))

    def test_niconico_pedia_is_preserved_reference(self):
        row = {
            "source_id": "youtube:example2",
            "encyclopedia_sources": ["https://dic.nicovideo.jp/a/example"],
        }
        self.assertEqual(MODULE.reference_family(row), "user_encyclopedia")
        self.assertFalse(MODULE.risky_added_record(row))

    def test_taiwan_archive_is_explicitly_reusable(self):
        row = {
            "source_id": "youtube:example3",
            "snapshot_source": (
                "https://raw.githubusercontent.com/TaiwanVtuberData/"
                "TaiwanVTuberTrackingDataArchive/master/example.json"
            ),
        }
        self.assertEqual(MODULE.reusable_family(row), "taiwan_archive")
        self.assertFalse(MODULE.risky_added_record(row))


if __name__ == "__main__":
    unittest.main()
