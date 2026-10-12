"""## Executive summary (read this first)
Pack five frozen Development drafts locally through the official hidden-prompt CLI.
This helper never reads a Team Key and contains no upload command.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

def resolve_cli():
    for name in ['qfbench2','qfbench2.exe']:
        found=shutil.which(name)
        if found:return found
    for name in ['qfbench2.exe','qfbench2']:
        p=Path(sys.executable).parent/name
        if p.is_file():return str(p)
    raise RuntimeError('Official qfbench2 CLI not found. Activate the existing v2.6.0 environment.')
def verify(path,draft,team_number):
    from qfbench2_common.contracts.descriptor import SubmissionDescriptor
    with zipfile.ZipFile(path) as z:
        if sorted(z.namelist())!=['submission.json','team-claim.json'] or z.testzip() is not None:raise RuntimeError('Invalid ZIP members or CRC')
        raw=z.read('submission.json');sealed=json.loads(raw);claim=json.loads(z.read('team-claim.json'))
    descriptor=SubmissionDescriptor.from_mapping(sealed)
    if descriptor.track!='forecasting' or descriptor.phase!='dev':raise RuntimeError('Not a Development forecasting package')
    if sealed['image']!=draft['image'] or sealed['models']!=draft['models']:raise RuntimeError('Frozen image or model disclosure mismatch')
    if claim['site_team_id']!=team_number or claim['descriptor_sha256']!=hashlib.sha256(raw).hexdigest():raise RuntimeError('Team claim binding mismatch')
    if not isinstance(claim.get('proof'),str) or len(claim['proof'])!=64:raise RuntimeError('Invalid claim proof structure')
    return {'file':path.name,'SHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'size_bytes':path.stat().st_size,'CRC_PASS':True,'descriptor_pass':True,'claim_descriptor_binding_pass':True,'claim_cryptographic_authentication':'official pack produced proof; organizer verifies key-bound proof','phase':'dev','image':descriptor.image_reference()}
def main():
    p=argparse.ArgumentParser();p.add_argument('--team-number',type=int,required=True);p.add_argument('--out',type=Path,default=Path.cwd()/'M15-development-packages');args=p.parse_args()
    if sys.version_info<(3,13):raise RuntimeError('Python3.13 or later required')
    if metadata.version('qfbench2-common')!='2.6.0':raise RuntimeError('Use the existing official qfbench2-common2.6.0 environment; do not change image dependencies')
    if args.team_number<=0:raise RuntimeError('Supply your verified website team number')
    cli=resolve_cli();root=Path(__file__).resolve().parent
    from qfbench2_common.contracts.descriptor import SubmissionDescriptor,seal_descriptor_digest
    drafts={}
    for v in 'ABCDE':
        path=root/'drafts'/f'M15-{v}-development.draft.json';draft=json.loads(path.read_text())
        if 'team_id' in draft or 'descriptor_digest' in draft:raise RuntimeError('Draft unexpectedly contains a team claim')
        # Public fixture placeholder is validation-only, never used in a package.
        probe=seal_descriptor_digest({**draft,'team_id':'team-example-0001'})
        SubmissionDescriptor.from_mapping(probe)
        drafts[v]=(path,draft)
    args.out.mkdir(parents=True,exist_ok=True);receipts=[]
    for v in 'ABCDE':
        path,draft=drafts[v];out=args.out/f'M15-{v}-development.zip'
        if out.exists():
            receipts.append(verify(out,draft,args.team_number));print('Existing verified '+out.name);continue
        print('\n'+out.name+': the OFFICIAL CLI will ask for your Team Key (hidden). This helper cannot read it.',flush=True)
        subprocess.run([cli,'submission','pack','--descriptor',str(path),'--team-number',str(args.team_number),'--out',str(out)],check=True)
        receipts.append(verify(out,draft,args.team_number))
        (args.out/'M15-package-verification.json').write_text(json.dumps(receipts,indent=2)+'\n')
    (args.out/'M15-package-verification.json').write_text(json.dumps(receipts,indent=2)+'\n')
    print('\nFive Development ZIPs verified. No upload was performed. Keep V51-final-submission.zip separate.')
if __name__=='__main__':main()
