"""Bulk V-liver ingestion is intentionally disabled.

General VTuber/V-liver rosters and directories may be used only as research
leads. Publishing requires an individually reviewed public profile or an
explicit community submission. AIVTuber-specific research is handled
separately by the AIVTuber pipeline.
"""

import json


def main():
    print(json.dumps({
        "status": "disabled",
        "reason": "bulk_general_vliver_ingestion_paused",
        "publishing_policy": "individual_review_or_submission_only"
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
