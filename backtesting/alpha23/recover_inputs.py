"""Executive summary: reconstruct exact runner metadata without relaxing any input-byte assertion."""
import pathlib,shutil,json,hashlib,sys
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);(out/'inputs').mkdir(parents=True,exist_ok=True);(out/'data').mkdir(exist_ok=True);shutil.copyfile(root/'data/curve.parquet',out/'data/curve.parquet')
manifest=json.loads((root/'inputs/input-manifest.json').read_text());rows=[]
for ent in manifest['inputs']:
 name=ent['id'];found=list((root/'artifacts').glob('**/'+name+'/receipt.json'));assert len(found)==1;receipt=json.loads(found[0].read_text());runner=found[0].parent.parent.parent
 docs=json.loads((runner/'data/dataset-manifest.json').read_text())['docs'];date=ent['origin'];eligible=[d for d in docs if d['active']<=date];selected=[]
 for kind in ['fomc_statement','fomc_minutes']:selected+=sorted([d for d in eligible if d['kind']==kind],key=lambda d:(d['active'],d['sha256']))[-2:]
 unit=out/'inputs'/name;shutil.copytree(root/'inputs'/name,unit,dirs_exist_ok=True)
 (unit/'policy.json').write_text(json.dumps([{k:v for k,v in d.items() if k not in ['text','path']} for d in selected],indent=2))
 entries=[{'doc_id':'policy-'+d['sha256'][:16],'timestamp':d['active'],'source':'Federal Reserve','doc_type':d['kind'],'file':f'policy-{i}.txt'} for i,d in enumerate(selected)]
 (unit/'text/corpus_index.json').write_text(json.dumps({'documents':entries,'asof':date},indent=2))
 hashes={str(f.relative_to(unit)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(unit.rglob('*')) if f.is_file()}
 assert hashes==receipt['input_hashes'],name
 # Numerical histories AND actual policy language were never changed.
 assert all(hashes[k]==ent['files'][k] for k in hashes if k not in ['policy.json','text/corpus_index.json'])
 original=json.loads((root/'inputs'/name/'policy.json').read_text());recovered=json.loads((unit/'policy.json').read_text());assert [{k:v for k,v in d.items() if k!='sha256'} for d in original]==[{k:v for k,v in d.items() if k!='sha256'} for d in recovered]
 rows.append({'id':name,'origin':date,'files':hashes,'last_observation':ent['last_observation'],'docs':ent['docs']})
manifest['inputs']=rows;(out/'inputs/input-manifest.json').write_text(json.dumps(manifest,indent=2));print('PASS exact runner bytes reconstructed for',len(rows),'units; numeric and policy signal values unchanged')
