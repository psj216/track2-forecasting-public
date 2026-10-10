"""Executive summary: reconstruct only historical complete profiles without reading truth or losses.
Verify immutable recovery members, B0/R2 bytes and exact inherited T0/S0/ST0 features.
"""
import argparse,json,csv,zipfile
from pathlib import Path
import numpy as np
from .core import ROOT,EXPERTS,PARENT,digest,array_digest,dump
from backtesting.text_route_audit02.features import build,T_NAMES,S_NAMES
from qfbench2_track_forecasting.context01.context_router import EXPERTS as INPUTS,route
from qfbench2_track_forecasting.context01.engine import apply
from qfbench2_track_forecasting.context01.text_effect import location_only

def prepare(private):
 rec=private/'recovered';out=ROOT/'backtesting/last_shot08/results'
 context=json.loads((rec/'context/recovery_index.json').read_text())
 text=json.loads((rec/'text/RECOVERY_HASH_MANIFEST.json').read_text())['members']
 verified=0
 for item in context['files']:
  p=rec/'context'/item['path']
  if p.is_file():assert digest(p)==item['sha256'],str(p);verified+=1
 for name,h in text.items():
  p=rec/'text'/name
  if p.is_file():assert digest(p)==h,str(p);verified+=1
 cards=json.loads((rec/'text/private/cards.json').read_text())['cards']
 assert len(cards)==24 and sum(c['cells']for c in cards)==63 and sum(c['cells']==1 for c in cards)==13
 rows=json.loads((rec/'context/context01-private/rows.json').read_text())['rows']
 annotations=json.loads((ROOT/'backtesting/context01/results/context_annotations.json').read_text())['cards']
 texts=json.loads((rec/'context/context01-private/annotation_texts.json').read_text())['cards']
 baselines=json.loads((ROOT/'backtesting/context01/results/baseline_manifest.json').read_text())['baselines']
 original=json.loads((ROOT/'backtesting/text_route_audit02/results/frozen_expert_manifest.json').read_text())['cards']
 inputs=json.loads((ROOT/'backtesting/context01/results/expert_transfer_manifest.json').read_text())['cards']
 dest=private/'library';dest.mkdir(exist_ok=True);audits=[];b0s=[];r2s=[]
 for i,c in enumerate(cards):
  bp=rec/'context/context01-private/baselines'/(c['id']+'_baseline.npy')
  npth=bp.with_name(c['id']+'_numeric.npy')
  for kind,p in [('B_TEXT',bp),('B_NUMERIC',npth)]:
   expected=next(r for r in baselines if r['card_id']==c['id']and r['kind']==kind)
   assert digest(p)==expected['sha256'];assert expected['draws']==2000
  b=np.load(bp);n=np.load(npth);saved=rec/'text/private/frozen_forecasts'/f'card{i:02d}.npz'
  assert digest(saved)==original[i]['npz_sha256']
  with np.load(saved)as z:e0=z['E0'];e1=z['E1']
  assert np.array_equal(b,e0)and array_digest(e0)==original[i]['B0_array_sha256']and array_digest(e1)==original[i]['R2_array_sha256']
  ep=rec/'context/context01-private/experts'/f'card{i:02d}.npz';assert digest(ep)==inputs[i]['prediction_sha256']
  with np.load(ep)as z:pred={e:z['prediction'][j]for j,e in enumerate(INPUTS)};avail={e:z['available'][j]for j,e in enumerate(INPUTS)}
  assets=[r['asset']for r in rows if r['card_id']==c['id']]
  one,mean,_,_=route(annotations[c['id']]['economic_topics'],assets,pred,avail)
  r1=apply(b,one);r2=apply(b,mean);assert np.array_equal(r2,e1)
  models={'B0':b,'B_NUMERIC':n,'TEXT_LOCATION':location_only(b,n),'R1':r1,'R2':e1}
  for key,x in models.items():assert x.shape==b.shape and np.isfinite(x).all()and x.shape[0]==2000
  np.savez_compressed(dest/f'card{i:02d}.npz',**models)
  audits.append({'card_id_hash':__import__('hashlib').sha256(c['id'].encode()).hexdigest(),'shape':list(b.shape),'forecast_hashes':{k:array_digest(x)for k,x in models.items()},'stored_B0_R2_bitwise_equal':True,'existing_R1_reconstructed_no_fit':True})
  b0s.append(b);r2s.append(e1)
  print(json.dumps({'stage':'pre-outcome forecast reproduction','completed':i+1,'total':24,'path':str(dest/f'card{i:02d}.npz')}),flush=True)
 rebuilt=build(cards,texts,annotations,b0s,r2s);fp=rec/'text/private/features.npz'
 assert digest(fp)=='564a38e4b7d71dca0ae7c22270486edca47195e7b89c27afce9989e646c7df67'
 with np.load(fp)as saved:
  for k in ['T0','S0','ST0']:assert np.array_equal(saved[k],rebuilt[k]),k
 assert len(T_NAMES)==36
 np.savez_compressed(private/'frozen_features.npz',T0=rebuilt['T0'],S0=rebuilt['S0'],ST0=rebuilt['ST0'])
 dump(out/'feature_manifest.json',{'source_features_sha256':digest(fp),'columns':{'T0':T_NAMES,'S0':S_NAMES,'ST0':S_NAMES+T_NAMES},'array_hashes':{k:array_digest(rebuilt[k])for k in ['T0','S0','ST0']},'exact_inherited_arrays':True,'new_features':False})
 dump(out/'expert_reproduction_manifest.json',{'source_members_verified':verified,'cards':audits,'experts':list(EXPERTS),'truth_deserialized':False,'comparative_losses_opened':False,'refitting':False,'historical_score_verification':'Deferred until remote PRE; exact historical components then required'})
 dump(out/'expert_library_spec.json',{'primary_library':list(EXPERTS),'eligibility':'Historical independent forecast logic, complete exact 24 whole-card draw profiles, no card truth in generation, no expert modifications; reproducibility failures exclude technically only. No partial-card dropping.','selection_before_losses':True,'identities_frozen':True,'same_card_universe':{'cards':24,'cells':63,'single':13,'multi':11,'families':4},'tie_order':list(EXPERTS),'aliases':'R0 duplicates B0; duplicates on individual cards retained; no duplicate complete-library identities','scope':'B_NUMERIC and TEXT_LOCATION are existing CONTEXT01 scored forecast profiles, not newly generated experts.'})
 print('PREPARATION VERIFIED: five historical profiles; no outcomes loaded',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--private',type=Path,required=True);prepare(p.parse_args().private)
