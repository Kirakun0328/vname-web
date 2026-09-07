import datetime
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from global_sources import parse_taiwan_records, parse_hololist, merge_global
from legacy_sources import parse_legacy

CID='UC'+'a'*22
TODAY=datetime.date(2026,9,7)


class GlobalSourcesTest(unittest.TestCase):
    def test_preparing_and_future_debut_override_video(self):
        data={'id':'one','name':'例','activity':'active','YouTube':{'id':CID},'popularVideo':{'type':'YouTube','id':'abcdefghijk'}}
        self.assertEqual(len(parse_taiwan_records([data],TODAY)[0]),1)
        self.assertEqual(len(parse_taiwan_records([dict(data,activity='preparing')],TODAY)[0]),0)
        self.assertEqual(len(parse_taiwan_records([dict(data,debutDate='2026-09-08')],TODAY)[0]),0)
        self.assertEqual(len(parse_taiwan_records([dict(data,name='例 準備中')],TODAY)[0]),0)

    def test_follower_count_does_not_prove_debut(self):
        r={'id':'two','name':'例','activity':'active','Twitch':{'id':'example','follower':{'count':25}}}
        self.assertFalse(parse_taiwan_records([r],TODAY)[0])
        rows,_=parse_taiwan_records([dict(r,debutDate='2020-01-01')],TODAY)
        self.assertEqual(rows[0]['twitch_login'],'example')

    def test_historical_snapshot_requires_already_past_debut(self):
        r={'name':'Example','youtube':CID,'url':'https://hololist.net/example/','status':'Active','debutDate':'September 13, 2024'}
        self.assertEqual(len(parse_hololist([r])[0]),1)
        self.assertEqual(len(parse_hololist([dict(r,debutDate='September 15, 2024')])[0]),0)

    def test_accounts_merge_without_overwriting_verified_readings(self):
        base=[{'source_id':'old','display_name':'旧名','reading':'きゅうめい','youtube_channel_id':CID,'activity_source':'https://example.com/current'}]
        row={'source_id':'taiwan:one','display_name':'新名','source_url':'https://example.com/old','youtube_channel_id':CID,'twitch_login':'example','activity_source':'https://example.com/old','source_snapshot_at':'2024-09-14'}
        extra,counts=merge_global(base,[],[row],{})
        self.assertEqual(counts['new_records'],0)
        self.assertEqual(extra[0]['aliases'],['新名'])
        self.assertNotIn('reading',extra[0])
        self.assertNotIn('activity_source',extra[0])
        other=dict(row,source_id='taiwan:two',youtube_channel_id=None)
        _,counts=merge_global(base,extra,[other],{})
        self.assertEqual(counts['new_records'],0)

    def test_same_name_different_accounts_is_not_merged(self):
        rows=[{'source_id':'taiwan:'+s,'display_name':'同じ名前','source_url':'https://example.com/'+s,'twitch_login':s} for s in ['one','two']]
        extra,counts=merge_global([],[],rows,{})
        self.assertEqual(counts['new_records'],2)
        _,counts=merge_global([],extra,rows,{})
        self.assertEqual(counts['new_records'],0)

    def test_retired_people_remain_eligible_with_past_debut(self):
        row={'name':'Example','youtube':CID,'url':'https://hololist.net/example/','status':'Retired','debutDate':'September 13, 2018'}
        records,_=parse_hololist([row])
        self.assertEqual(records[0]['activity_status_at_source'],'Retired')

    def test_bulk_source_url_is_not_an_identity(self):
        rows=[{'source_id':'youtube:'+cid,'display_name':'例'+str(i),'source_url':'https://example.com/all.json','youtube_channel_id':cid} for i,cid in enumerate([CID,'UC'+'b'*22])]
        extra,counts=merge_global([],[],rows,{})
        self.assertEqual(counts['new_records'],2)
        self.assertEqual(len(extra),2)

    def test_explicit_directory_reading_preserves_existing_verification(self):
        row={'source_id':'youtube:'+CID,'display_name':'例','youtube_channel_id':CID,'source_url':'https://example.com/profile',
             'reading':'れい','reading_source':'https://example.com/profile','reading_source_kind':'directory_explicit'}
        extra,_=merge_global([],[],[row],{})
        self.assertEqual(extra[0]['reading'],'れい')
        extra[0].update(reading='ためし',reading_source='https://example.com/official')
        updated,_=merge_global([],extra,[row],{})
        self.assertEqual(updated[0]['reading'],'ためし')

    def test_legacy_requires_self_description_and_posted_videos(self):
        row={'channelId':CID,'channelTitle':'例 VTuber','videoCount':'2','viewCount':'20'}
        meta={CID:{'desc':'VTuberの例です。','source_url':'https://example.com/snapshot'}}
        self.assertEqual(len(parse_legacy([row],meta)[0]),1)
        self.assertFalse(parse_legacy([dict(row,videoCount='0')],meta)[0])
        self.assertFalse(parse_legacy([dict(row,channelTitle='VTuber切り抜き')],meta)[0])
        meta[CID]['desc']='VTuberファンです。'
        self.assertFalse(parse_legacy([row],meta)[0])
        meta[CID]['desc']='新人VTuberです。初配信予定です。'
        self.assertFalse(parse_legacy([row],meta)[0])
