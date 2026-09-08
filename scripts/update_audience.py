"""Audience directory ingestion paused; no YouTube Data API is used."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    report={'status':'disabled_by_request','uses_youtube_data_api':False,
            'reason':'Subscriber counts and popularity sorting have been removed.'}
    (ROOT/'scripts/audience-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
