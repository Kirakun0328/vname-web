import datetime
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from ai_list_sources import parse_bundle, rows_from, merge_rows
from official_rosters import parse_ozon, parse_linear
from icon_sources import parse_channel_icon

TODAY=datetime.date(2026,9,7)
CID='UC'+'a'*22


def ai(**changes):
    return dict({'name':'星ねこ【AI VTuber】','description':'AI VTuberです','youtubeChannelID':CID,
                 'youtubeURL':'starcat','latestVideoDate':'2026-09-01T10:00:00Z',
                 'latestVideoUrl':'https://www.youtube.com/watch?v=abcdefghijk','isUpcoming':False},**changes)


class AdditionalSources(unittest.TestCase):
    def test_static_bundle_is_decoded_as_data_and_incomplete_payloads_fail(self):
        items=[ai(name='星ねこ'+str(i)) for i in range(100)]
        payload=json.dumps({'B':items},ensure_ascii=True).replace('\\','\\\\').replace("'","\\'")
        self.assertEqual(len(parse_bundle("throw Error('must not execute');JSON.parse('"+payload+"')")),100)
        with self.assertRaises(ValueError):parse_bundle("JSON.parse('{\"B\":[]}')")

    def test_ai_tags_alone_and_unreleased_streams_do_not_establish_activity(self):
        rows=rows_from([ai(),ai(name='動画投稿者',description='AIで動画を制作',tags=['AI VTuber']),
                        ai(name='未来AI VTuber',latestVideoDate='2027-01-01T00:00:00Z'),
                        ai(name='待機AI VTuber',isUpcoming=True,recentYoutubeVideos=[{'url':'https://www.youtube.com/watch?v=abcdefghijk','date':'2026-01-01T00:00:00Z'}])],TODAY)
        self.assertEqual(len(rows),1)
        self.assertNotIn('description',rows[0])

    def test_same_name_on_other_channel_stays_separate_and_shared_host_is_not_retagged(self):
        row=rows_from([ai()],TODAY)[0]
        old={'source_id':'old','display_name':'星ねこ','category':'VTuber','youtube_channel_id':'UC'+'b'*22}
        out,counts=merge_rows([old],[],[row]);self.assertEqual(counts['new_records'],1)
        host={'source_id':'host','display_name':'人間ホスト','youtube_channel_id':CID}
        out,counts=merge_rows([host],[],[row]);self.assertEqual(counts['ambiguous_skipped'],1);self.assertEqual(out,[])

    def test_linked_ai_name_enriches_existing_character_and_keeps_siblings(self):
        row=rows_from([ai()],TODAY)[0]
        old={'source_id':'star','display_name':'星ねこ','category':'AIVTuber','youtube_channel_id':CID,'reading':'ほしねこ','reading_source':'https://official.example/'}
        sibling={'source_id':'moon','display_name':'月ねこ','category':'AIVTuber','youtube_channel_id':CID}
        out,counts=merge_rows([old,sibling],[],[row]);self.assertEqual(counts['matched_existing'],1)
        self.assertEqual(out[0]['source_id'],'star');self.assertNotIn('reading',out[0]);self.assertEqual(len(out),1)

    def test_ozon_scopes_identity_to_modal_and_requires_past_debut(self):
        def profile(slug,name,date,uid):
            return f'<div class="remodal" data-remodal-id="modal-{slug}"><p class="v-name-b">{name}</p><p class="v-name-kana">ほしねこ</p><dl><dt>デビュー</dt><dd>{date}</dd></dl><a href="https://web.iriam.app/s/user/{uid}">IRIAM</a></div>'
        html=profile('one','星ねこ','2025年1月1日','one')+profile('future','未来','2027年1月1日','two')+'<footer><a href="https://x.com/agency">X</a></footer>'
        rows=parse_ozon(html,TODAY);self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['reading'],'ほしねこ');self.assertEqual(len(rows[0]['platform_accounts']),1)

    def test_linear_uses_personal_broadcast_link_when_badge_is_empty(self):
        html='''<div class="talent-profile__info"><h2 class="talent-profile__name">星ねこ</h2><dl><dt>デビュー日</dt><dd>2025年1月1日</dd></dl><div class="talent-profile__sns"><a class="talent-profile__sns-link--iriam" href="https://web.iriam.app/s/user/star">IRIAM</a></div></div><footer><a href="https://web.iriam.app/s/user/agency">IRIAM</a></footer>'''
        row=parse_linear(html,'https://linear-v.com/talent/123/',TODAY)
        self.assertEqual(row['primary_platforms'],['iriam']);self.assertEqual(len(row['platform_accounts']),1)
        self.assertIsNone(parse_linear(html.replace('2025年','2027年'),'https://linear-v.com/talent/123/',TODAY))

    def test_avatar_requires_exact_channel_and_known_image_host(self):
        html=f'<link rel="canonical" href="https://www.youtube.com/channel/{CID}"><meta property="og:image" content="https://yt3.ggpht.com/avatar">'
        self.assertEqual(parse_channel_icon(html,'https://www.youtube.com/channel/'+CID,CID)['icon_kind'],'channel')
        with self.assertRaises(ValueError):parse_channel_icon(html,'https://www.youtube.com/channel/'+CID,'UC'+'b'*22)
        self.assertIsNone(parse_channel_icon(html.replace('yt3.ggpht.com','evil.test'), 'https://youtube.com/@star',CID))


if __name__=='__main__':unittest.main()
