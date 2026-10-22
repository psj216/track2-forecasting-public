"""Executive summary: bounded exact-image monthly, isolation and runtime release audit."""
import concurrent.futures,hashlib,json,os,pathlib,re,subprocess,sys,tarfile,time,tomllib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'finalfit04'))
from replay import BASE,FF03,run,save,sha,auxiliary
root=pathlib.Path(os.environ['RUNNER_TEMP'])/'ff05-release';root.mkdir();root.chmod(0o777)
repo=pathlib.Path('.').resolve();official=repo/'official-current';common=repo/'common-current';audit03=repo/'backtesting/finalfit03';audit=pathlib.Path(__file__).resolve().parent
results={'executive_summary':'Exact FF03 restored archive; no build, push, secrets or packing.','run_id':os.environ['GITHUB_RUN_ID'],'source':os.environ['GITHUB_SHA'],'monthly':[],'sequential':[],'concurrent':[]}
def persist():save(root/'summary.json',results)
def docker(unit=None,out=None,tools=False):
    cmd=['docker','run','--rm','--platform=linux/amd64','--network=none','--read-only','--tmpfs','/tmp:rw,size=512m','--cpus=2','--memory=4g','--pids-limit=256','--security-opt=no-new-privileges']
    if unit:cmd+=['-v',str(unit)+':/input:ro']
    if out:cmd+=['-v',str(out)+':/output:rw']
    if tools:cmd+=['-v',str(audit03)+':/audit03:ro','-v',str(audit)+':/audit05:ro','-v',str(root)+':/worktest:rw','-v',str(official)+':/official:ro']
    return cmd
for image,label in [(FF03,'ff03'),(BASE,'original')]:
    rec=run(['docker','image','inspect',image]);save(root/(label+'-inspect.json'),rec);assert rec['exit']==0
    info=json.loads(rec['stdout'])[0]
    assert info['Os']=='linux' and info['Architecture']=='amd64' and not info['Config'].get('Volumes')
    assert info['Config']['Labels']['qfbench2.interface_version']=='2.0' and info['Config']['User'] not in ['', '0','root']
    if label=='ff03':assert info['Id']==FF03
results['image_identity']=json.loads((root/'ff03-inspect.json').read_text())
results['forecast_help']=run(docker()+[FF03,'forecast','--help']);assert results['forecast_help']['exit']==0
for args in [['python3','/audit03/container_tools.py','prepare','/worktest','/official','monthly'],['python3','/audit03/boundary_inputs.py','/worktest'],['python3','/audit05/prepare.py']]:
    rec=run(docker(tools=True)+[FF03]+args);save(root/('prepare-'+str(len(list(root.glob('prepare-*'))))+'.json'),rec);assert rec['exit']==0,rec
manifest=json.loads((root/'synthetic-input-manifest.json').read_text());lookup={x['name']:x for x in manifest}
def forecast(unit,label,measure=False):
    out=root/'outputs'/label;out.mkdir(parents=True);out.chmod(0o777)
    c=tomllib.loads((unit/'card.toml').read_text());args=['forecast','--panels','/input','--text','/input/text','--asof',c['provenance']['data_cutoff'],'--out','/output/forecast.parquet','--seed','17','--n-draws','1000']
    cmd=docker(unit,out)
    if measure:
        resourcefile='/tmp/child-resource.json'
        code="import subprocess,resource,json,pathlib,sys; p=subprocess.run("+repr(args)+"); print('FF05_RSS='+json.dumps({'forecast_child_peak_rss_kib':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss}));sys.exit(p.returncode)"
        rec=run(cmd+[FF03,'python3','-c',code],90)
    else:rec=run(cmd+[FF03]+args,90)
    rec.update(label=label,unit=unit.name,input_kind='SYNTHETIC_CONTRACT_TEST' if 'inputs' in unit.parts else 'PUBLISHED_PRACTICE',inputs={str(p.relative_to(unit)):sha(p) for p in unit.rglob('*') if p.is_file()},hashes={f.name:sha(f) for f in out.iterdir() if f.is_file()},output_bytes=sum(f.stat().st_size for f in out.iterdir() if f.is_file()))
    save(root/(label+'.json'),rec);print(label,rec['exit'],round(rec['wall_seconds'],3),flush=True)
    return rec,out
published=['t2-F1-cpi-glidepath-2023','t2-F4-cpi-vintage-2022','t2-F4-covid-nfp-2020','t2-F1-sahm-watch-2024']
synthetic=['monthly-a','monthly-b','monthly-missing','monthly-conflict','lagged-anchor','multi-monthly','heterogeneous','heterogeneous-anchor','nonconsecutive','duplicate-mapping','mixed-cadence','unsupported-cadence']
for name in published+synthetic:
    unit=official/'units'/name if name in published else root/'inputs'/name
    rec,out=forecast(unit,'monthly-'+name,measure=True)
    fail=name=='unsupported-cadence' or lookup.get(name,{}).get('expected_failure',False)
    rec['expected_rejection']=fail
    if fail:
        rec['rejection_safe']=rec['exit']!=0 and not (out/'forecast.parquet').exists();assert rec['rejection_safe'],rec
    else:
        assert rec['exit']==0,rec
        gate=run(auxiliary(BASE,unit,out,official,common,['python3','/official/scoring/scoring.py','score','--card','/input/card.toml','--forecast','/output/forecast.parquet']))
        save(root/('monthly-'+name+'-gate.json'),gate);assert gate['exit']==0,gate
        rec['official_gate']=gate
        if name not in published:
            kernel=run(docker(unit,out,tools=True)+[FF03,'python3','/audit03/kernel_check.py','/input','/output']);save(root/('monthly-'+name+'-kernel.json'),kernel);assert kernel['exit']==0,kernel
            rec['kernel']=kernel
    save(root/('monthly-'+name+'.json'),rec);results['monthly'].append(rec);persist()
ids=json.loads((repo/'backtesting/finalfit04/spec.json').read_text())['cards'][:16]
# Use existing daily public cards. This is runtime/isolation scope, not a repeat A/B regression.
t=time.monotonic()
for i,card in enumerate(ids):
    rec,out=forecast(official/'units'/card,'seq-'+str(i));assert rec['exit']==0;results['sequential'].append(rec);persist()
results['sequential_total_wall_seconds']=time.monotonic()-t
first,_=forecast(official/'units'/ids[0],'sequence-repeat');results['after_batch_identity']=first['hashes']==results['sequential'][0]['hashes'];assert results['after_batch_identity'];persist()
# Actual largest declared public asset grid plus a different card in parallel, isolated output mounts.
cards=[]
for p in (official/'units').glob('*/card.toml'):
    c=tomllib.loads(p.read_text());cards.append((len(c['targets']['asset_ids'])*len(c['targets']['horizons']),p.parent.name))
worst=max(cards)[1];results['largest_public_grid_card']=worst
ct=time.monotonic()
def concurrent_run(pair):
    i,card=pair;rec,_=forecast(official/'units'/card,'parallel-'+str(i),measure=True);assert rec['exit']==0;return rec
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results['concurrent']=list(pool.map(concurrent_run,enumerate([ids[0],worst,ids[0],worst])))
results['concurrent_total_wall_seconds']=time.monotonic()-ct
results['concurrent_repeat_equal']=results['concurrent'][0]['hashes']==results['concurrent'][2]['hashes'] and results['concurrent'][1]['hashes']==results['concurrent'][3]['hashes'];assert results['concurrent_repeat_equal'];persist()
# Source and dependency identity inspection does not modify either frozen image.
code="import pathlib,hashlib,json,sys,importlib.metadata as m; import qfbench2_track_forecasting as q;p=pathlib.Path(q.__file__).parent;print(json.dumps({'python':sys.version,'source':{str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*.py')},'wrapper':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in pathlib.Path('/opt/finalfit03').glob('*.py')},'dependencies':{d.metadata['Name']:d.version for d in m.distributions()}}))"
identity=run(docker()+[FF03,'python3','-c',code]);assert identity['exit']==0;save(root/'source-dependencies.json',identity)
# Audit all saved layers, including deleted files, report paths/counts only, never content.
archive=pathlib.Path(os.environ['RUNNER_TEMP'])/'ff03-image/candidate-image.tar.gz'
secret=re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
findings=[];scanned=0;layers=0;names=[]
with tarfile.open(archive,'r:gz') as tar:
    for member in tar:
        if member.name.endswith('/layer.tar') or (member.name.startswith('blobs/sha256/') and member.size>1000000):
            stream=tar.extractfile(member)
            try:
                inner=tarfile.open(fileobj=stream,mode='r|*');layers+=1
                for f in inner:
                    name=f.name.lower()
                    if f.isfile():
                        scanned+=1
                        if any(s in name for s in ['team-key','team_key','team-claim.json','realized.parquet','practice-answers/','submission.zip','answer_key']):findings.append({'layer':member.name,'path':f.name,'kind':'forbidden_path'})
                        if f.size<=2000000 and (name.endswith(('.py','.sh','.json','.toml','.env','.yaml','.yml')) or '/.ssh/' in name or '/.docker/config' in name):
                            data=inner.extractfile(f).read()
                            if secret.search(data):findings.append({'layer':member.name,'path':f.name,'kind':'secret_pattern'})
            except tarfile.ReadError:pass
results['layers_audit']={'layers_opened':layers,'files_enumerated':scanned,'findings':findings,'scope':'All layer filenames; bounded text/config files <=2MB credential-pattern scan, not proof against arbitrary hidden secrets.'};assert layers>0 and not findings
results['completed']=True;persist();print('FINAL_FIT_05_RELEASE_COMPLETE',flush=True)
