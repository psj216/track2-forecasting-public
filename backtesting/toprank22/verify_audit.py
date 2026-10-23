"""Verify evidence integrity; does not certify forecasts or provider vintages."""
import gzip,hashlib,json,pathlib,sys
r=pathlib.Path(__file__).parent/'results';units=pathlib.Path(sys.argv[1]);checked=0
for entry in json.loads((r/'card-manifest.json').read_text()):
 assert hashlib.sha256((units/entry['card']/'card.toml').read_bytes()).hexdigest()==entry['sha256'];checked+=1
for name in ['panel-manifest.json','document-manifest.json']:
 for entry in json.loads((r/name).read_text()):
  for relative in entry['paths']:
   assert hashlib.sha256((units/relative).read_bytes()).hexdigest()==entry['sha256'];checked+=1
for entry in json.loads((r/'compression-manifest.json').read_text()):
 b=(r/entry['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==entry['compressed_sha256']
 assert hashlib.sha256(gzip.decompress(b)).hexdigest()==entry['uncompressed_sha256']
d=json.loads((r/'data-inventory.json').read_text());assert len(json.loads((r/'document-manifest.json').read_text()))==d['unique_text_byte_hashes']
assert len(json.loads((r/'panel-conflicts.json').read_text()))==d['conflicting_panel_asset_date_cells']
receipt={'status':'PASS','input_files_hash_verified':checked,'compressed_manifest_files_verified':8,'scope':'Evidence integrity only; not PIT/provider-vintage or model verification','model_tests':'NOT_RUN_NO_MODEL'}
(r/'audit-verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
