import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from popularity_sources import merge_counts, list_counts

class PopularityTests(unittest.TestCase):
    def test_only_exact_accounts_receive_counts_and_zero_remains_valid(self):
        cid='UC'+'a'*22
        base=[{'source_id':'youtube:'+cid,'display_name':'星ねこ'}, {'source_id':'other','display_name':'星ねこ'}]
        row={'platform':'youtube','account_id':'channel/'+cid,'count':0,'source':'https://example.com/','checked_at':'2026-09-08'}
        out,count=merge_counts(base,[],[row]);self.assertEqual(count,1)
        self.assertEqual(out[0]['source_id'],'youtube:'+cid);self.assertEqual(out[0]['audience_metrics'][0]['count'],0)
        again,_=merge_counts(base,out,[dict(row,count=100)])
        self.assertEqual(len(again[0]['audience_metrics']),1);self.assertEqual(again[0]['audience_metrics'][0]['count'],100)
        for invalid in [-1,None,'100',True]:self.assertEqual(merge_counts(base,[],[dict(row,count=invalid)])[0],[])

    def test_list_counts_do_not_copy_content_or_invent_missing_counts(self):
        item={'youtubeChannelID':'UC'+'a'*22,'youtubeSubscribers':42,'description':'Creative profile','imageUrl':'https://example.com/image'}
        rows=list_counts([item]);self.assertEqual(len(rows),1);self.assertEqual(rows[0]['count'],42)
        self.assertEqual(set(rows[0]),{'platform','account_id','count','source','checked_at','retrieved_at'})
        self.assertEqual(list_counts([dict(item,youtubeSubscribers=None)]),[])

if __name__=='__main__':unittest.main()
