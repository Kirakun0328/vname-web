import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from platform_sources import canonical_account, merge_platforms, parse_agency_profile, parse_agency_index
from broad_sources import preparing


def row(name='テスト',url='https://www.tiktok.com/@example'):
    return {'source_id':'agency:test','display_name':name,'source_url':'https://agency.example/profile',
            'activity_source':'https://agency.example/profile','activity_evidence':'official_broadcast_destinations',
            'platform_accounts':[{'url':url}], 'primary_platforms':['tiktok'],
            'primary_platform_source':'https://agency.example/profile','primary_platform_evidence':'official_broadcast_destinations'}


class PlatformTests(unittest.TestCase):
    def test_platform_identity_and_tracking_parameters(self):
        a=canonical_account('https://web.iriam.app/s/user/ABCdef?uuid=123')
        self.assertEqual(a['id'],'ABCdef')
        self.assertEqual(a['url'],'https://web.iriam.app/s/user/ABCdef')
        self.assertEqual(canonical_account('https://twitter.com/Example?x=1'),canonical_account('https://x.com/example'))
        self.assertEqual(canonical_account('https://www.tiktok.com/@EXample/live')['id'],'@example')
        self.assertEqual(canonical_account('https://www.spooncast.net/jp/channel/315874262/tab/home')['platform'],'spoon')

    def test_untrusted_or_non_account_urls(self):
        for url in ['javascript:alert(1)','https://tiktok.com.evil.test/@example','https://u:p@www.tiktok.com/@example','https://twitch.tv/directory','https://www.youtube.com/watch?v=123']:
            self.assertIsNone(canonical_account(url),url)

    def test_no_youtube_required_and_repeat_is_idempotent(self):
        result,counts=merge_platforms([],[],[row()])
        self.assertEqual(counts['new_records'],1)
        self.assertNotIn('youtube_channel_id',result[0])
        again,_=merge_platforms([],result,[row()])
        self.assertEqual(result,again)

    def test_match_account_preserves_reading_ai_category_and_name(self):
        base=[{'source_id':'existing','display_name':'元の名前','reading':'もとのなまえ','category':'AIVTuber','source_url':'https://www.tiktok.com/@example'}]
        result,counts=merge_platforms(base,[],[row()])
        self.assertEqual(counts['matched_existing'],1)
        self.assertEqual(result[0]['source_id'],'existing')
        self.assertNotIn('category',result[0])
        self.assertNotIn('reading',result[0])
        self.assertEqual(result[0]['aliases'],['テスト'])

    def test_same_names_are_not_identity_evidence(self):
        base=[{'source_id':'other','display_name':'テスト','source_url':'https://www.tiktok.com/@someoneelse'}]
        result,counts=merge_platforms(base,[],[row()])
        self.assertEqual(counts['new_records'],1)

    def test_shared_ai_broadcast_is_not_collapsed(self):
        base=[{'source_id':n,'display_name':n,'broadcast_url':'https://www.twitch.tv/shared'} for n in ['Alice','Reign']]
        result,counts=merge_platforms(base,[],[row(url='https://www.twitch.tv/shared')])
        self.assertEqual(result,[])
        self.assertEqual(counts['ambiguous_skipped'],1)

    def test_primary_platform_uses_delivery_section_only(self):
        doc='<main><h1>テスト</h1><div class="delivery-account"><a href="https://www.tiktok.com/@example">TikTok LIVE</a></div><div class="sns-account"><a href="https://www.youtube.com/@example">YOUTUBE</a></div></main><footer><a href="https://twitch.tv/agency">Agency</a></footer>'
        r=parse_agency_profile(doc,'https://vliver.321.inc/liver/test/','321')
        self.assertEqual(r['primary_platforms'],['tiktok'])
        self.assertEqual({a['platform'] for a in r['platform_accounts']},{'tiktok','youtube'})
        self.assertIsNone(parse_agency_profile(doc.replace('テスト','IRIAM準備中'),'https://vliver.321.inc/liver/test/','321'))

    def test_clover_requires_activity(self):
        doc='<main><h1>テスト</h1><div class="liver-footer-actions"><a href="https://web.iriam.app/s/user/abc">配信を見る</a></div></main>'
        self.assertIsNone(parse_agency_profile(doc,'https://clover-live.com/liver-page/test/','clover'))
        r=parse_agency_profile(doc.replace('</h1>','</h1>毎日配信しています'),'https://clover-live.com/liver-page/test/','clover')
        self.assertEqual(r['primary_platforms'],['iriam'])

    def test_preparing_vlivers(self):
        for name in ['Vライバー準備中','IRIAM準備中','Avvy準備中']:
            self.assertTrue(preparing(name))

class KnownAccountTests(unittest.TestCase):
    def test_vdb_enriches_existing_only_without_inventing_primary(self):
        from platform_sources import enrich_known_accounts
        existing={'source_id':'known','display_name':'既存'}
        vdb={'vtbs':[{'type':'group'}]*5000+[
            {'uuid':'known','type':'vtuber','accounts':[{'platform':'bilibili','type':'official','id':'123'}]},
            {'uuid':'new','type':'vtuber','accounts':[{'platform':'bilibili','type':'official','id':'456'}]}]}
        rows,count=enrich_known_accounts([existing],[],vdb)
        self.assertEqual(count,1)
        self.assertEqual(rows[0]['source_id'],'known')
        self.assertNotIn('primary_platforms',rows[0])
        self.assertEqual(rows[0]['platform_accounts'][0]['platform'],'bilibili')

    def test_future_intent_is_not_activity(self):
        doc='<main><h1>例</h1>IRIAMで配信してみたいです。<div class="liver-footer-actions"><a href="https://web.iriam.app/s/user/abc">配信を見る</a></div></main>'
        self.assertIsNone(parse_agency_profile(doc,'https://clover-live.com/liver-page/test/','clover'))
