const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('app.js','utf8');
const context=vm.createContext({});
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
