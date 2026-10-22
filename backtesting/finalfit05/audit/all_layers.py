"""Executive summary: enumerate every archive layer, including small wrapper layers."""
import json,os,pathlib,re,tarfile
root=pathlib.Path(os.environ['RUNNER_TEMP'])/'ff05-layer-audit';root.mkdir(exist_ok=True)
results={}
# Audit all saved layers, including deleted files, report paths/counts only, never content.
archive=pathlib.Path(os.environ['RUNNER_TEMP'])/'ff03-image/candidate-image.tar.gz'
secret=re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
findings=[];scanned=0;layers=0;names=[]
with tarfile.open(archive,'r:gz') as tar:
    for member in tar:
        if member.name.endswith('/layer.tar') or member.name.startswith('blobs/sha256/'):
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

(root/'all-layers.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results))
