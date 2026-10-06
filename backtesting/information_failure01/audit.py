"""Executive summary: reproduce exact saved primary forecasts; never call a model fit."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from qfbench2_common.scoring.crps import crps_ensemble
from .common import *

KEYS=['origin','asset','horizon']
def selected_indices(e,r):
 idx=pd.MultiIndex.from_frame(e[KEYS]);q=pd.MultiIndex.from_frame(r[KEYS]);assert idx.is_unique and q.is_unique
 ii=idx.get_indexer(q)
 if (ii<0).any():raise ValueError('Scored rows absent from exact evaluation ledger')
 return ii
def load_models(q,model):
 single=q/'fits'/(model+'.json')
 if single.exists():return json.loads(single.read_text())['folds']
 return [json.loads(f.read_text()) for f in sorted((q/'fits').glob(model+'-*.json'))]
def heldout_state(r,p,models,features):
 n=len(r);zmax=np.full(n,np.nan);zmean=np.full(n,np.nan);components=np.full((n,5),np.nan);audits=[]
 for m in models:
  mask=pd.to_datetime(r.origin).dt.year.eq(m['year']).to_numpy(copy=True)
  if 'asset' in m:mask &= r.asset.eq(m['asset']).to_numpy()&r.horizon.eq(m['horizon']).to_numpy()
  if not mask.any():continue
  mean=np.asarray(m['scaler_mean']);scale=np.asarray(m['scaler_scale']);co=np.asarray(m.get('coefficient',m.get('coefficients')));x=r.loc[mask,features].to_numpy();z=(x-mean)/scale;pp=z@co+float(m['intercept'])
  if not np.allclose(pp,p[mask],atol=1e-12,rtol=1e-12):raise ValueError('Preserved coefficient/state does not reproduce frozen prediction')
  zmax[mask]=np.max(abs(z),axis=1);zmean[mask]=np.mean(z*z,axis=1);components[mask]=z*co
  audits.append({**m,'coefficient':co.tolist(),'raw_feature_coefficient':(co/scale).tolist(),'raw_feature_intercept':float(m['intercept']-np.dot(co,mean/scale)),'heldout_cells':int(mask.sum())})
 return zmax,zmean,components,audits
def build_source(private,source):
 private=Path(private);line=json.loads((OUT/'lineage_manifest.json').read_text())['sources'][source];loc=line['location'];old=ROOT/'backtesting'/loc/'results';q=private/'source_experiments'/source/'private';model=line['primary_model'];features=line['features']
 required=['scored_rows.parquet','evaluation_ledger.parquet','predictions.npz','losses.npz','evaluation_draws.npz'];missing=[x for x in required if not (q/x).exists()]
 if missing:raise FileNotFoundError('MISSING_ARTIFACT '+source+': '+','.join(missing))
 r=pd.read_parquet(q/'scored_rows.parquet');e=pd.read_parquet(q/'evaluation_ledger.parquet');ii=selected_indices(e,r)
 for col in ['truth','median','sd','delta','scale']:
  if not np.array_equal(e.iloc[ii][col].to_numpy(),r[col].to_numpy()):raise ValueError('Frozen scored/evaluation ledger differs: '+col)
 pred=np.load(q/'predictions.npz',allow_pickle=False);p=pred[model][ii]
 if not np.isfinite(p).all():raise ValueError('Nonfinite frozen primary prediction')
 draws=np.load(q/'evaluation_draws.npz',allow_pickle=False)['draws'][:,ii]
 if (q/'scored_draws.npz').exists() and not np.array_equal(draws,np.load(q/'scored_draws.npz')['draws']):raise ValueError('Frozen scored draw columns differ')
 if not np.allclose(np.median(draws,axis=0),r['median'],atol=1e-14,rtol=0) or not np.allclose(np.std(draws,axis=0),r.sd,atol=1e-14,rtol=1e-13):raise ValueError('Original V5.1 geometry mismatch')
 if not np.allclose((r.truth-r['median'])/r.sd,r.delta,atol=1e-12,rtol=1e-12):raise ValueError('Original standardized target mismatch')
 losses=np.load(q/'losses.npz',allow_pickle=False);b=crps_ensemble(draws,r.truth.to_numpy(),fair=True)/r.scale.to_numpy();c=crps_ensemble(draws+p*r.sd.to_numpy(),r.truth.to_numpy(),fair=True)/r.scale.to_numpy()
 if not np.allclose(b,losses['baseline'],atol=1e-12,rtol=1e-12) or not np.allclose(c,losses[model],atol=1e-12,rtol=1e-12):raise ValueError('Saved primary cell loss reproduction mismatch')
 ratio=float(c.sum()/b.sum());summary=json.loads((old/'primary_score_summary.json').read_text());published=summary['models'][model]['crps_ratio']
 if abs(ratio-published)>1e-12:raise ValueError('Published primary ratio not reproduced')
 pub=pd.read_csv(old/'crossfit_predictions.csv',float_precision='round_trip')
 if 'asset' not in pub:pub['asset']=r.asset.iloc[0]
 ip=selected_indices(pub,r)
 if not np.allclose(pub.iloc[ip][model].to_numpy(),p,atol=1e-14,rtol=1e-14):raise ValueError('Saved public/private predictions mismatch')
 relcol='round_id' if source=='ECB' else 'release_id';rel=r[relcol].astype(str)
 if source=='ECB':pubdates=pd.read_csv(old/'ecb_publication_ledger.csv').set_index('round_id').publication_date.to_dict()
 elif source=='SLOOS':pubdates=pd.read_csv(old/'sloos_publication_ledger.csv').set_index('release_id').publication_date.to_dict()
 else:pubdates={s['release_id']:s['publication_date'] for s in json.loads((old/'source_states.json').read_text())['states']}
 models=load_models(q,model);zmax,zmean,components,modelaudit=heldout_state(r,p,models,features)
 l=pd.DataFrame({'source':source,'asset':r.asset,'origin_date':r.origin,'year':pd.to_datetime(r.origin).dt.year,'fold':pd.to_datetime(r.origin).dt.year,'horizon':r.horizon,'release_id':rel,'release_date':rel.map(pubdates),'source_age':r.SOURCE_AGE_BUSINESS_DAYS,'true_delta':r.delta,'predicted_delta':p,'V5.1_median':r['median'],'V5.1_SD':r.sd,'raw_center_error':r.truth-r['median'],'predicted_raw_shift':p*r.sd,'baseline_cell_CRPS':losses['baseline'],'candidate_cell_CRPS':losses[model],'cell_CRPS_delta':losses[model]-losses['baseline'],'sign_true':np.sign(r.delta),'sign_pred':np.sign(p),'sign_correct':np.sign(r.delta)==np.sign(p),'abs_true_delta':abs(r.delta),'abs_pred_delta':abs(p),'feature_state_id':source+':'+rel,'truth':r.truth,'normalization_scale':r.scale,'target_end':r.target_end,'heldout_max_abs_train_z':zmax,'heldout_mean_squared_train_z':zmean})
 if l.release_date.isna().any():raise ValueError('MISSING_ARTIFACT publication-date mapping')
 folder=private/'diagnostic_inputs'/source;folder.mkdir(parents=True,exist_ok=True);l.to_parquet(folder/'ledger.parquet',index=False);np.savez_compressed(folder/'draws.npz',draws=draws,oracle_loss=losses['oracle'],feature_values=r[features].to_numpy(),prediction_components=components);save(folder/'models.json',{'features':features,'models':modelaudit,'missing_model_state_cells':int(np.isnan(zmax).sum()),'MISSING_ARTIFACT':not bool(modelaudit),'no_model_fit_called':True})
 result=dict(source=source,primary_model=model,published_primary_ratio=published,reproduced_primary_ratio=ratio,difference=ratio-published,tolerance=1e-12,original_geometry_tolerance={'median_atol':1e-14,'SD_rtol':1e-13,'delta_rtol':1e-12},within_tolerance=True,origins=int(l.origin_date.nunique()),cells=len(l),releases=int(l.release_id.nunique()),assets=sorted(l.asset.unique()),horizons=sorted(map(int,l.horizon.unique())),folds=sorted(map(int,l.fold.unique())),DATASET_READY=line['DATASET_READY'],predictions_npz_sha256=digest(q/'predictions.npz'),selected_prediction_array_sha256=array_digest(p),scored_ledger_sha256=digest(q/'scored_rows.parquet'),frozen_baseline_draw_array_sha256=array_digest(draws),model_state_files=len(modelaudit),missing_model_state_cells=int(np.isnan(zmax).sum()),source_model_scope='Pooled all horizons, annual single EUR fit' if source=='ECB' else 'Separate asset/horizon/annual fits',primary_forecasts_frozen=True)
 save(OUT/(source+'-reproduction.json'),result);status('reproduction',source=source)
 print(f'REPRODUCE {source} ratio={ratio:.15f} difference={ratio-published:.3g} cells={len(l)} output={folder}',flush=True)
 return result
def assemble(private):
 private=Path(private);rows=[];repro=[]
 for source in ['ECB','SLOOS','SPD']:
  result=json.loads((OUT/(source+'-reproduction.json')).read_text());repro.append(result);rows.append(pd.read_parquet(private/'diagnostic_inputs'/source/'ledger.parquet'))
 ledger=pd.concat(rows,ignore_index=True);dest=private_out(private);dest.mkdir(parents=True,exist_ok=True);ledger.to_parquet(dest/'unified_failure_ledger.parquet',index=False)
 manifest={}
 for source in ['ECB','SLOOS','SPD']:
  q=private/'source_experiments'/source/'private'
  for name in ['predictions.npz','losses.npz','scored_rows.parquet','evaluation_ledger.parquet','evaluation_draws.npz']:
   f=q/name;manifest[str(f.relative_to(private))]=digest(f)
  for f in (q/'fits').glob('*.json'):manifest[str(f.relative_to(private))]=digest(f)
  for f in (private/'diagnostic_inputs'/source).iterdir():manifest[str(f.relative_to(private))]=digest(f)
 manifest[str((dest/'unified_failure_ledger.parquet').relative_to(private))]=digest(dest/'unified_failure_ledger.parquet')
 save(private/'input_hash_manifest.json',{'files':manifest,'source_prediction_hashes_preserved':True})
 save(OUT/'prior_result_reproduction.json',{'sources':repro,'no_refitting':True,'all_primary_results_reproduced':all(x['within_tolerance'] for x in repro)})
 save(OUT/'unified_failure_summary.json',{'rows':len(ledger),'schema':list(ledger.columns),'source_counts':[{k:x[k] for k in ['source','cells','origins','releases','assets','horizons','folds']} for x in repro],'ledger_location':'Private recovery: backtesting/information_failure01/results/unified_failure_ledger.parquet','ledger_sha256':digest(dest/'unified_failure_ledger.parquet'),'cell_CRPS_units':'Original fair CRPS divided by each frozen normalization scale; exact legacy score inputs. Raw center error/shift retain asset native units.','feature_state_id':'source:release_id; identifies the frozen release packet, never contains outcome data','market_outcomes_public':False,'source_ledgers_not_identical':'ECB EUR 2020-2024; SLOOS six UST assets 2017-2024; SPD two UST assets 2020-2024. Do not interpret score differences as a controlled source ranking.'})
 status('unified_ledger',new_models_fitted=0);print('UNIFIED ledger complete',len(ledger),dest,flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private',type=Path,required=True);a.add_argument('--source',choices=['ECB','SLOOS','SPD','ASSEMBLE'],required=True);v=a.parse_args()
 if v.source=='ASSEMBLE':assemble(v.private)
 else:build_source(v.private,v.source)
