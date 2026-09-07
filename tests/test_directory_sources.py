import datetime
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from directory_sources import parse_razz,parse_live_feed,parse_atoms,atoms_next,atoms_urls
from platform_sources import merge_platforms,canonical_account

TODAY=datetime.date(2026,9,7)
UID='12345678-1234-1234-1234-123456789abc'


def nuxt(items):
    nodes=[]
    def put(value):
        index=len(nodes);nodes.append(None)
        if isinstance(value,dict):nodes[index]={k:put(v) for k,v in value.items()}
        elif isinstance(value,list):nodes[index]=[put(v) for v in value]
        else:nodes[index]=value
        return index
    put(items)
    return '<script id="__NUXT_DATA__" type="application/json">'+json.dumps(nodes)+'</script>'


def razz(**changes):
    return dict({'slug':'starcat','name':'星ねこ','name_kana':'ほしねこ','name_en':'Star Cat','debut_date':'2025-01-01T00:00:00Z',
                 'iriam_info':{'profile_deep_link_url':'iriam://p?applicationModel=profile&uid='+UID},'x_id':'123456789'},**changes)


def atoms(name,uid,handle,date='2024/01/01'):
    return f'''<html><head><title>{name} | Atoms(アトムス) Agency | VLiver事務所</title></head><body>
    <header><a href="https://x.com/AtomsAgency">Official X</a></header><main><div class="changing-class">
    <p>{name}</p><p>Star Cat</p><p>コメント</p><p>配信してます。</p><p>デビュー日：{date}</p>
    <a href="https://reality.app/profile/{uid}">REALITY</a><a href="https://x.com/{handle}">X</a></div></main>
    <footer><a href="https://x.com/AtomsAgency">Agency X</a><a href="https://reality.app/profile/agency">Agency stream</a></footer></body></html>'''


class DirectoryTests(unittest.TestCase):
    def test_razz_requires_past_debut_and_preserves_official_reading(self):
        document=nuxt([razz(),razz(slug='future',debut_date='2027-01-01'),razz(slug='today',debut_date='2026-09-07'),razz(slug='preparing',name='VTuber準備中')])
        rows=parse_razz(document,TODAY);self.assertEqual(len(rows),1);self.assertEqual(rows[0]['reading'],'ほしねこ')
        self.assertEqual(rows[0]['primary_platforms'],['iriam'])
        self.assertTrue(rows[0]['platform_accounts'][0]['url'].startswith('iriam://'))
        self.assertNotIn('web.iriam.app',rows[0]['platform_accounts'][0]['url'])

    def test_iriam_current_and_legacy_native_ids_and_numeric_x_are_stable(self):
        for uid in [UID,UID.replace('-','')]:
            self.assertEqual(canonical_account('iriam://p?applicationModel=profile&uid='+uid)['id'],uid)
        self.assertIsNone(canonical_account('iriam://p?applicationModel=live&uid='+UID))
        self.assertEqual(canonical_account('https://x.com/i/user/123')['id'],'uid:123')

    def test_live_feed_needs_positive_stream_time_or_actual_live_status(self):
        items=[{'Name':'配信済み','UserId':UID,'StreamedTime':600,'Rank':101,'AdminList':['not exported']},
               {'Name':'配信中','UserId':UID.replace('-',''),'StreamedTime':0,'LiveStatus':'STREAMING'},
               {'Name':'未確認','UserId':UID,'StreamedTime':0,'Rank':501},
               {'Name':'Vライバー準備中','UserId':UID,'StreamedTime':600}]
        rows=parse_live_feed('<script id="iriam-broadcasters-data">'+json.dumps(items)+'</script>','listart')
        self.assertEqual([r['display_name'] for r in rows],['配信済み','配信中'])
        self.assertNotIn('AdminList',json.dumps(rows))

    def test_atoms_scopes_personal_accounts_and_does_not_merge_through_agency_footer(self):
        rows=[parse_atoms(atoms('星ねこ','one','one'), 'https://kyampus.me/atoms/liver/one',TODAY),
              parse_atoms(atoms('月ねこ','two','two'), 'https://kyampus.me/atoms/liver/two',TODAY)]
        self.assertEqual({a['id'] for a in rows[0]['platform_accounts']},{'one'})
        merged,counts=merge_platforms([],[],rows)
        self.assertEqual(counts['new_records'],2);self.assertEqual(len(merged),2)
        self.assertNotIn('AtomsAgency',json.dumps(merged))

    def test_atoms_future_or_unknown_debut_is_not_added(self):
        self.assertIsNone(parse_atoms(atoms('星ねこ','one','one','2027/01/01'),'https://kyampus.me/atoms/liver/one',TODAY))
        self.assertIsNone(parse_atoms(atoms('星ねこ','one','one','未定'),'https://kyampus.me/atoms/liver/one',TODAY))

    def test_official_readings_are_added_but_existing_ai_identity_is_preserved(self):
        row=parse_razz(nuxt([razz()]),TODAY)[0]
        base=[{'source_id':'ai-one','display_name':'星のAI','category':'AIVTuber','reading':'ほしのあい','reading_source':'https://example.org/official','platform_accounts':row['platform_accounts']}]
        out,counts=merge_platforms(base,[],[row]);self.assertEqual(out[0]['source_id'],'ai-one');self.assertNotIn('category',out[0]);self.assertNotIn('reading',out[0])
        new,counts=merge_platforms([],[],[row]);self.assertEqual(new[0]['reading'],'ほしねこ')

    def test_pagination_uses_public_next_cursor_and_skips_directory_routes(self):
        fragment='<button data-load-more-trigger="" data-next-cms-content-id="nextID" data-next-offset="100"></button>'
        self.assertIn('__sd_nextOffset=100',atoms_next(fragment,3));self.assertIn('page=3',atoms_next(fragment,3))
        self.assertEqual(atoms_urls('<a href="/atoms/liver/Rank">Rank</a><a href="/atoms/liver/person">Person</a>'),['https://kyampus.me/atoms/liver/person'])


if __name__=='__main__':unittest.main()
