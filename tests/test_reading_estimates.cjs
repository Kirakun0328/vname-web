const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('app.js','utf8');
const context=vm.createContext({window:{}});
vm.runInContext(source.slice(source.indexOf('function resolveReading('),source.indexOf('function load(data)')),context);
const resolve=r=>context.resolveReading(r);
test('official unusual readings win over estimates',()=>{
 const r=resolve({display_name:'癒色えも',reading:'いしきえも',reading_source:'https://example.com',reading_source_kind:'manual'});
 assert.equal(r.reading,'いしきえも');assert.equal(r.reading_inferred,false);
});
test('kana names and complete Japanese reading candidates are marked as estimates',()=>{
 assert.equal(resolve({display_name:'ミライ アカリ',reading:'誤り'}).reading,'みらいあかり');
 const r=resolve({display_name:'山田はな',reading:'やまだはな'});assert.equal(r.reading,'やまだはな');assert.equal(r.reading_inferred,true);
});
test('partial conversions and unsupported English names stay without a guess',()=>{
 assert.equal(resolve({display_name:'音紡いま',reading:'音ぼういま'}).reading,'');
 assert.equal(resolve({display_name:'Natsumi Moe',reading:'なつみほうめぐみ'}).reading,'');
 assert.equal(resolve({display_name:'未知名'}).reading,'');
});

test('confirmed Hanano Iroha overrides an incorrect Gemma estimate',()=>{
 context.window.VTUBER_ESTIMATED_READINGS={one:{display_name:'花野彩晴',reading:'はなのさいせい',model:'gemma-4-E2B-it',kind:'inferred'}};
 const r=resolve({source_id:'one',display_name:'花野彩晴',reading:'はなのいろは',reading_source:'https://www.youtube.com/channel/UChQKyaipbRo2C-M-_oOJ4_w',reading_source_kind:'manual'});
 assert.equal(r.reading,'はなのいろは');assert.equal(r.reading_inferred,false);
});
test('Gemma can supplement English names but never reuse a renamed identity estimate',()=>{
 context.window.VTUBER_ESTIMATED_READINGS={one:{display_name:'Alice',reading:'ありす',model:'gemma-4-E2B-it',kind:'inferred'}};
 assert.equal(resolve({source_id:'one',display_name:'Alice'}).reading,'ありす');
 assert.equal(resolve({source_id:'one',display_name:'Bob'}).reading,'');
});
test('Gemma cannot change a kana suffix already spelled in the name',()=>{
 context.window.VTUBER_ESTIMATED_READINGS={one:{display_name:'灰島リウ',reading:'はいしまりゅう',model:'gemma-4-E2B-it',kind:'inferred'}};
 assert.equal(resolve({source_id:'one',display_name:'灰島リウ'}).reading,'');
});
