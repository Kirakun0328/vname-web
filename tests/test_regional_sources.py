import datetime
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from regional_sources import parse_thai, parse_indonesia
from scholar_sources import parse_profile, verified_video
from reviewed_sources import merge_reviewed

NOW=datetime.datetime(2026,9,7,tzinfo=datetime.timezone.utc)
CID='UC'+'a'*22


class RegionalSourcesTest(unittest.TestCase):
    def thai(self):
        return {'result':[{'channel_id':'UC'+str(i).zfill(22),'title':'Example '+str(i),'views':30,
                           'last_published_video_at':'2025-01-01T00:00:00Z'} for i in range(100)]}

    def test_thai_creation_date_or_subscribers_do_not_prove_activity(self):
        data=self.thai()
        data['result'][0].update(last_published_video_at=None,published_at='2016-01-01',subscribers=100000)
        data['result'][1]['last_published_video_at']='2027-01-01T00:00:00Z'
        data['result'][2]['views']=0
        data['result'][3]['title']='Example เตรียมเดบิวต์'
        rows,_=parse_thai(data,NOW)
        self.assertEqual(len(rows),96)
        self.assertNotIn('debut_date',rows[0])

    def test_duplicate_thai_identity_rejects_source(self):
        data=self.thai();data['result'][1]['channel_id']=data['result'][0]['channel_id']
        with self.assertRaises(ValueError):parse_thai(data,NOW)

    def test_indonesia_excludes_predebut_even_with_videos(self):
        row={'channel_id':CID,'channel_name':'Example','description':'I am a VTuber.','video_count':'10','views_count':'50'}
        self.assertEqual(len(parse_indonesia([row])[0]),1)
        for description in ['VTuber, will debut soon','calon vtuber ID yang belum tau kapan debut','Vtweet bukan "Vtuber"','VTuber belum debut']:
            self.assertFalse(parse_indonesia([dict(row,description=description)])[0])
        self.assertFalse(parse_indonesia([dict(row,description='',channel_tag='VTuber')])[0])
        self.assertFalse(parse_indonesia([dict(row,video_count='0')])[0])
        self.assertFalse(parse_indonesia([dict(row,channel_name='Example Clips')])[0])

    def test_scholar_only_uses_profile_sections_and_own_published_video(self):
        page='<h1 class="vtuber-name">Example</h1><div class="vtuber-social-links"><a href="https://www.youtube.com/@Example">YT</a></div><section class="vtuber-videos"><iframe src="https://www.youtube.com/embed/abcdefghijk"></iframe></section><footer><a href="https://www.youtube.com/@Other">Other</a></footer>'
        profile=parse_profile(page,'https://scholarvtuber.com/vtuber/example/')
        player={'videoDetails':{'videoId':'abcdefghijk','channelId':CID,'viewCount':'20'},'microformat':{'playerMicroformatRenderer':{'publishDate':'2025-01-01','ownerProfileUrl':'http://www.youtube.com/@Example'}}}
        def check():return verified_video(profile,'var ytInitialPlayerResponse = '+json.dumps(player)+';', 'abcdefghijk',NOW)
        self.assertEqual(check()['youtube_channel_id'],CID)
        player['microformat']['playerMicroformatRenderer']['ownerProfileUrl']='https://www.youtube.com/@Other'
        self.assertIsNone(check())
        player['microformat']['playerMicroformatRenderer']['ownerProfileUrl']='https://www.youtube.com/@Example'
        player['microformat']['playerMicroformatRenderer']['publishDate']='2027-01-01'
        self.assertIsNone(check())
        player['microformat']['playerMicroformatRenderer']['publishDate']='2025-01-01'
        player['videoDetails']['isUpcoming']=True
        self.assertIsNone(check())

    def test_reviewed_shared_broadcast_keeps_distinct_characters(self):
        rows=[{'source_id':'aivtuberdb:'+name,'display_name':name,'source_url':'https://www.twitch.tv/shared',
               'activity_source':'https://aivtuberdb.com/','reading':''} for name in ['Alice','Reign']]
        extra=merge_reviewed([],rows)
        self.assertEqual(len(extra),2)
        self.assertEqual(merge_reviewed(extra,rows),extra)
        extra[0]['reading']='ありす'
        self.assertEqual(merge_reviewed(extra,rows)[0]['reading'],'ありす')

    def test_scholar_parentheses_must_be_explicit_kana(self):
        player={'videoDetails':{'videoId':'abcdefghijk','channelId':CID,'viewCount':'2'},'microformat':{'playerMicroformatRenderer':{'publishDate':'2025-01-01','ownerProfileUrl':'https://www.youtube.com/@Example'}}}
        document='var ytInitialPlayerResponse = '+json.dumps(player)+';'
        profile={'display_name':'粉体 粒子 (ふんたい つぶこ)','source_url':'https://scholarvtuber.com/vtuber/example/','links':['https://www.youtube.com/@Example']}
        row=verified_video(profile,document,'abcdefghijk',NOW)
        self.assertEqual(row['display_name'],'粉体 粒子')
        self.assertEqual(row['reading'],'ふんたいつぶこ')
        profile['display_name']='Example (Project)'
        self.assertNotIn('reading',verified_video(profile,document,'abcdefghijk',NOW))


if __name__=='__main__':unittest.main()
