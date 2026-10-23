"""Minimal actual Docker gates; persist receipts on every step and stop on failure."""
import hashlib,json,os,pathlib,subprocess,time,tomllib,tarfile,re
root=pathlib.Path(os.environ['RUNNER_TEMP'])/'m20';root.mkdir(exist_ok=True);root.chmod(0o777)
repo=pathlib.Path.cwd();base='sha256:23f226ced859978d7a3f16a23c6d1515a1a3bdb14338297f4818d114bcfa2c1c'
candidate='moonshot20-local:'+os.environ['GITHUB_SHA']
receipts={'source':os.environ['GITHUB_SHA'],'run_id':os.environ['GITHUB_RUN_ID'],'steps':[],'performance':'NOT_EVALUATED'}
def save(): (root/'receipt.json').write_text(json.dumps(receipts,indent=2))
def run(cmd,limit=120):
 t=time.monotonic();p=subprocess.run(cmd,text=True,capture_output=True,timeout=limit)
 r={'command':cmd,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-t};receipts['steps'].append(r);save();print(json.dumps(r),flush=True);assert p.returncode==0,r
 return p.stdout
archive=pathlib.Path(os.environ['RUNNER_TEMP'])/'ff03-image/candidate-image.tar.gz'
receipts['original_archive_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest();assert receipts['original_archive_sha256']=='df232487177cb56cb0ae945b2613fbbebbb24eff702f21712662e589d04f636c';save()
run(['docker','load','--input',str(archive)])
original=json.loads(run(['docker','image','inspect',base]))[0];before=original['RepoTags'];assert original['Id']==base
base_tag='finalfit03-local:c5b8bbbd6227888b7a3dc0bbd05dc414d2d7c3f6';assert base_tag in before
run(['docker','build','--platform=linux/amd64','--pull=false','--build-arg','FF03_BASE='+base_tag,'--build-arg','SOURCE_SHA='+os.environ['GITHUB_SHA'],'-t',candidate,str(repo/'backtesting/moonshot20')],180)
info=json.loads(run(['docker','image','inspect',candidate]))[0];receipts['candidate_image_id']=info['Id'];receipts['image_config']=info['Config']
assert info['Architecture']=='amd64' and info['Os']=='linux' and not info['Config'].get('Volumes')
assert info['Config']['User']=='1000' and info['Config']['Labels']['qfbench2.interface_version']=='2.0'
assert not info['Config']['Entrypoint'] and info['Config']['Cmd']==['forecast','--help']
def docker(unit,out,image,command,extra=None):
 cmd=['docker','run','--rm','--platform=linux/amd64','--network=none','--read-only','--tmpfs','/tmp:rw,size=512m','--cpus=2','--memory=4g','--pids-limit=256','--security-opt=no-new-privileges','-v',str(unit)+':/input:ro','-v',str(out)+':/output:rw']
 return cmd+(extra or [])+[image]+command
for kind,name in [('daily','t2-F3-curve-ust3m-ust6m-ust1y-ust2y-005-ps1'),('monthly','t2-F1-cpi-glidepath-2023')]:
 unit=repo/'official-current/units'/name;c=tomllib.loads((unit/'card.toml').read_text())
 args=['forecast','--panels','/input','--text','/input/text','--asof',c['provenance']['data_cutoff'],'--out','/output/forecast.parquet','--seed','17','--n-draws','1000']
 outputs={}
 for label,image in [('baseline',base),('candidate',candidate)]+([('repeat',candidate)] if kind=='daily' else []):
  out=root/(kind+'-'+label);out.mkdir();out.chmod(0o777);outputs[label]=out
  run(docker(unit,out,image,args))
 if kind=='daily':
  for f in outputs['candidate'].iterdir():assert f.read_bytes()==(outputs['repeat']/f.name).read_bytes()
 run(docker(unit,outputs['candidate'],candidate,['python3','/check/check.py',kind],['-v',str(outputs['baseline'])+':/baseline:ro','-v',str(repo/'backtesting/moonshot20')+':/check:ro']))
 for label in ['baseline','candidate']:
  gate=json.loads(run(docker(unit,outputs[label],candidate,['python3','/official/scoring/scoring.py','score','--card','/input/card.toml','--forecast','/output/forecast.parquet'],['-v',str(repo/'official-current')+':/official:ro','-v',str(repo/'common-current/common')+':/common:ro','-e','PYTHONPATH=/common:/official'])))
  assert gate['admissible'] and all(x=='pass' for x in gate['gates'].values())
 receipts[kind]='PASS';save()
# Preserve standalone image; neither the original archive nor tags are changed.
run(['docker','save','-o',str(root/'candidate-image.tar'),candidate],120)
run(['gzip','-n',str(root/'candidate-image.tar')],120)
receipts['candidate_archive_sha256']=hashlib.sha256((root/'candidate-image.tar.gz').read_bytes()).hexdigest()
secret=re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
findings=[];layers=files=0
with tarfile.open(root/'candidate-image.tar.gz','r:gz') as tar:
 for member in tar:
  if member.name.endswith('/layer.tar') or member.name.startswith('blobs/sha256/'):
   try:
    with tarfile.open(fileobj=tar.extractfile(member),mode='r|*') as inner:
     layers+=1
     for f in inner:
      if not f.isfile():continue
      files+=1;name=f.name.lower()
      if any(s in name for s in ['team-key','team_key','team-claim.json','realized.parquet','practice-answers/','submission.zip','answer_key']):findings.append({'path':f.name,'kind':'forbidden_path'})
      if f.size<=2000000 and name.endswith(('.py','.sh','.json','.toml','.env','.yaml','.yml')) and secret.search(inner.extractfile(f).read()):findings.append({'path':f.name,'kind':'secret_pattern'})
   except tarfile.ReadError:pass
receipts['layers']={'layers':layers,'files':files,'findings':findings,'scope':'all layer paths, text/config <=2MB pattern scan; not proof against arbitrary hidden secrets'}
assert layers>0 and not findings
assert json.loads(run(['docker','image','inspect',base]))[0]['RepoTags']==before
receipts['classification']='MOONSHOT20_TECHNICALLY_VALID_HIGH_RISK';receipts['original_preserved']=True;save()
print('MOONSHOT20_FINAL '+json.dumps({k:v for k,v in receipts.items() if k not in ['steps','image_config']}),flush=True)
