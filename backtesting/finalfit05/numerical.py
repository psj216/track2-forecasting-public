"""Executive summary: exact-image portability RED with bounded standalone Docker runs."""
import json,os,pathlib,sys,time,tomllib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'finalfit04'))
from replay import BASE,FF03,run,save,sha,auxiliary
root=pathlib.Path(os.environ['RUNNER_TEMP'])/'ff05-numerical'; root.mkdir(exist_ok=True)
unit=pathlib.Path('official-current/units/t2-F4-curve-ust3m-008-ps1').resolve()
audit=pathlib.Path(__file__).resolve().parent
c=tomllib.loads((unit/'card.toml').read_text()); asof=c['provenance']['data_cutoff']
save(root/'host.json',dict(cpu=run(['lscpu']),run_id=os.environ['GITHUB_RUN_ID'],job=os.environ.get('FF05_RUNNER'),source=os.environ['GITHUB_SHA'],inputs={str(f.relative_to(unit)):sha(f) for f in unit.rglob('*') if f.is_file()}))
labels=[]
for label,image,disabled in [('original-normal',BASE,False),('original-disabled',BASE,True),('ff03-normal',FF03,False),('ff03-repeat',FF03,False),('ff03-disabled',FF03,True)]:
    out=root/label;out.mkdir();out.chmod(0o777)
    cmd=['docker','run','--rm','--platform=linux/amd64','--network=none','--read-only','--tmpfs','/tmp:rw,size=512m','--cpus=2','--memory=4g','--pids-limit=256','--security-opt=no-new-privileges','-v',str(unit)+':/input:ro','-v',str(out)+':/output:rw']
    if disabled:cmd+=['-e','NPY_DISABLE_CPU_FEATURES=AVX512F,AVX2,FMA3']
    forecast=['--panels','/input','--text','/input/text','--asof',asof,'--out','/output/forecast.parquet','--seed','17','--n-draws','1000']
    rec=run(cmd+[image,'forecast']+forecast,90);rec['hashes']={f.name:sha(f) for f in out.iterdir() if f.is_file()};save(root/(label+'.json'),rec);print(label,rec['exit'],flush=True);assert rec['exit']==0
    gate=run(auxiliary(BASE,unit,out,pathlib.Path('official-current').resolve(),pathlib.Path('common-current').resolve(),['python3','/official/scoring/scoring.py','score','--card','/input/card.toml','--forecast','/output/forecast.parquet']))
    save(root/(label+'-gate.json'),gate);assert gate['exit']==0
    # Answers are visible only to this separate post-forecast scoring process.
    score=run(auxiliary(BASE,unit,out,pathlib.Path('official-current').resolve(),pathlib.Path('common-current').resolve(),['python3','/official/scoring/scoring.py','score','--card','/input/card.toml','--forecast','/output/forecast.parquet','--realized','/official/practice-answers/'+unit.name+'.parquet']))
    save(root/(label+'-score.json'),score);assert score['exit']==0
    if label!='ff03-repeat':
        tr=root/(label+'-trace');tr.mkdir();tr.chmod(0o777)
        traced=root/(label+'-traced-output');traced.mkdir();traced.chmod(0o777)
        dcmd=cmd.copy();dcmd[dcmd.index(str(out)+':/output:rw')]=str(traced)+':/output:rw'
        diag=run(dcmd+['-v',str(audit)+':/audit:ro','-v',str(tr)+':/trace:rw',image,'python3','/audit/trace_numeric.py']+forecast,120)
        save(root/(label+'-diagnostic.json'),diag);assert diag['exit']==0
        assert sha(traced/'forecast.parquet')==sha(out/'forecast.parquet'), 'Tracing changed forecast'
    labels.append(label)
rec=run(['docker','run','--rm','--network=none','--read-only','-v',str(root)+':/results:rw','-v',str(audit)+':/audit:ro',FF03,'python3','/audit/analyze_numeric.py'],90)
save(root/'analysis-command.json',rec);print(rec['stdout'],flush=True);assert rec['exit']==0
