import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from estimate_readings import validate,read_object
class EstimateTests(unittest.TestCase):
 def test_read_curated_correction(self):
  row=read_object(Path(__file__).resolve().parents[1]/'readings.js')['花野彩晴']
  self.assertEqual(row['reading'],'はなのいろは');self.assertEqual(row['reading_source_kind'],'manual')
  self.assertEqual(read_object(Path(__file__).resolve().parents[1]/'readings.js')['夢空愛里鈴']['reading'],'ゆめかありす')
 def test_model_results_require_exact_batch_identity_and_kana(self):
  batch=[{'source_id':'one'},{'source_id':'two'}]
  self.assertEqual(validate({'readings':[{'id':0,'reading':'はな'},{'id':1,'reading':''}]},batch),{'one':'はな','two':''})
  for results in [[{'id':0,'reading':'はな'}],[{'id':0,'reading':'はな'},{'id':0,'reading':'はな'}],[{'id':0,'reading':'<script>'},{'id':1,'reading':'はな'}]]:
   with self.assertRaises(ValueError):validate({'readings':results},batch)
