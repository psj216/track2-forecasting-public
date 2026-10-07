"""Executive summary: predeclared attribution, aggregate-only diagnostics and report."""
import argparse
from .core import *

def distribution(a):return {'mean':float(np.nanmean(a)),'q05':float(np.nanquantile(a,.05)),'q50':float(np.nanquantile(a,.5)),'q95':float(np.nanquantile(a,.95))}
def joined(folder,key,pattern='*.npz'):
 files=sorted((private()/folder).glob(pattern));return np.concatenate([np.load(f)[key] for f in files])
def decide(models,annual,permutation,random,bootstrap,bias,concentration,pit,origin):
 p=models['PRICE_FULL'];r=p['CRPS_ratio'];gain_i=models['INTERCEPT_ONLY']['CRPS_ratio']-r;gain_s=models['STRUCTURE_ONLY']['CRPS_ratio']-r
 gates={'ratio_le_0990':r<=.990,'increment_intercept_ge_0003':gain_i>=.003,'increment_structure_ge_0003':gain_s>=.003,
 'beats_majority':r<models['TRAINING_MAJORITY']['CRPS_ratio'],'beats_random_median':r<random['A']['ratio']['q50'],
 'balanced_ge_055':p['balanced_accuracy']>=.55,'Spearman_ge_010':p['Spearman']>=.10,'four_years_nonworse':sum(x<=1 for x in annual)>=4,
 'permutation_support':permutation['Monte_Carlo_p_ratio']<=.05,
 'origin_year_support':bootstrap['origin']['PRICE_FULL_ratio'][1]<1 and bootstrap['year']['PRICE_FULL_ratio'][1]<1,
 'no_year_over_half_gross_gain':concentration['year']<=.5,'usable_PIT':pit in ['A','B']}
 similar=any(abs(models[n]['CRPS_ratio']-r)<=.003 or models[n]['CRPS_ratio']<r for n in ['CONSTANT_UP','CONSTANT_DOWN','TRAINING_MAJORITY','INTERCEPT_ONLY'])
 frequent=random['A']['fraction_equal_or_better']>=.10
 negligible=gain_i<.003 or gain_s<.003
 materially_real=r<1 and gain_i>=.003 and gain_s>=.003 and p['balanced_accuracy']>=.55 and p['Spearman']>=.1 and sum(x<1 for x in annual)>=3 and gates['permutation_support']
 if all(gates.values()):verdict='PRICE_SIGNAL_REAL_BUT_SMALL';nxt='PRICE-STATE-DIRECTION-04'
 elif bias['persistent_center_bias'] and (similar or frequent or negligible):verdict='BASELINE_BIAS_NOT_PRICE_ALPHA';nxt='V5.1-CENTER-BIAS-AUDIT-04'
 elif materially_real and pit not in ['A','B']:verdict='SIGNAL_PLAUSIBLE_PIT_LIMITED';nxt='PRICE-PIT-RECONSTRUCTION-04'
 elif not bias['persistent_center_bias'] and not gates['permutation_support'] and frequent and (origin['balanced_accuracy']<.55 or sum(x<1 for x in annual)<3):verdict='NO_PRICE_SIGNAL';nxt='ALPHA-STRATEGY-RESET-04'
 else:verdict='INCONCLUSIVE';nxt='V5.1-CENTER-BIAS-AUDIT-04' if similar or frequent else 'PRICE-PIT-RECONSTRUCTION-04' if pit not in ['A','B'] else 'ALPHA-STRATEGY-RESET-04'
 return verdict,nxt,gates,{'similar_null':similar,'random_frequently_beats':frequent,'negligible_increment':negligible,'materially_price_specific':materially_real}

def run():
 receipt=verify_pre();allrows,rows,parent=load();data=np.load(private()/'audit_predictions.npz');names=list(data['names']);loss=data['losses'];prob=data['probabilities'];base=data['base'];models={}
 for i,n in enumerate(names):models[n]=metrics(prob[i],loss[i],rows,base)
 for n in ['V5.1','PERFECT_LOCATION']:models[n]['sign_accuracy']=None;models[n]['balanced_accuracy']=None;models[n]['Brier']=None;models[n]['Pearson']=None;models[n]['Spearman']=None
 csv('model_comparison.csv',[dict(model=n,**m) for n,m in models.items()])
 for file,selected in [('null_model_summary.csv',['V5.1','TRAINING_MAJORITY','INTERCEPT_ONLY','ASSET_PRIOR','HORIZON_PRIOR','MATCHED_RANDOM','CONSTANT_UP','CONSTANT_DOWN']),('structure_control_summary.csv',['STRUCTURE_ONLY','PRICE_FULL']),('temporal_shift_summary.csv',['PRICE_FULL']+[f'PRICE_LAG_{d}BD' for d in LAGS]),('feature_group_diagnostic.csv',['PRICE_FULL','P_LEVEL','P_CHANGE','P_CURVE'])]:csv(file,[dict(model=n,diagnostic_only=n!='PRICE_FULL',**models[n]) for n in selected])
 balanced={}
 for label,field in [('CELL_WEIGHTED',None),('ORIGIN_BALANCED','origin'),('YEAR_BALANCED','year')]:
  w=None if field is None else balanced_weights(rows[field]);balanced[label]={n:metrics(prob[i],loss[i],rows,base,w) for i,n in enumerate(names)}
 save(OUT/'origin_balanced_summary.json',{'executive_summary':'Each origin/year gets equal total weight. Weighted rank uses weighted mid-CDF ranks. Prediction ties receive zero sign credit.','methods':balanced,'CELL_REPLICATION_ARTIFACT':models['PRICE_FULL']['CRPS_ratio']<1 and balanced['ORIGIN_BALANCED']['PRICE_FULL']['CRPS_ratio']>=1})
 aggregate_tables={}
 for field,file in [('year','annual_summary.csv'),('asset','asset_summary.csv'),('horizon','horizon_summary.csv')]:
  items=[]
  for group,ii in rows.groupby(field).indices.items():
   for i,n in enumerate(names):items.append(dict(group=str(group),model=n,**metrics(prob[i,ii],loss[i,ii],rows.iloc[ii],base[ii])))
  csv(file,items);aggregate_tables[field]=items
 # Training labels used only after PRE, and only frozen purged indices.
 base_rates=[];bias_folds=[]
 for year,tr,te,c in folds(allrows):
  foldstats={}
  for split,indices in [('train',tr),('test',te)]:
   frame=allrows.iloc[indices]
   def rates(df):return {'cells':len(df),'positive_fraction':float(df.y.gt(0).mean()),'negative_fraction':float(df.y.lt(0).mean()),'zero_fraction':float(df.y.eq(0).mean())}
   base_rates.append(dict(year=year,split=split,group_type='all',group='all',**rates(frame)))
   for field in ['asset','horizon','year']:
    for group,df in frame.groupby(field):base_rates.append(dict(year=year,split=split,group_type=field,group=str(group),**rates(df)))
   foldstats[split]={**rates(frame),'mean_raw_center_error':float(frame.raw_center_error.mean()),'median_raw_center_error':float(frame.raw_center_error.median()),'mean_standardized_error':float((frame.raw_center_error/frame.sd).mean())}
  train=foldstats['train'];test=foldstats['test'];direction_train=np.sign(train['positive_fraction']-.5);direction_test=np.sign(test['positive_fraction']-.5)
  bias_folds.append(dict(year=year,**foldstats,same_material_majority=bool(direction_train==direction_test and direction_train!=0 and abs(train['positive_fraction']-.5)>=.05 and abs(test['positive_fraction']-.5)>=.05),same_mean_error_sign=bool(np.sign(train['mean_raw_center_error'])==np.sign(test['mean_raw_center_error']) and train['mean_raw_center_error']!=0)))
 csv('target_base_rate_summary.csv',base_rates)
 bias={'executive_summary':'Descriptive training-only center bias inspected on unchanged heldout targets; no baseline recalibration.','folds':bias_folds,'test_positive_fraction':float(rows.y.gt(0).mean()),'persistent_center_bias':sum(b['same_material_majority'] and b['same_mean_error_sign'] for b in bias_folds)>=3 and models['TRAINING_MAJORITY']['CRPS_ratio']<1,'criterion':'At least3/5 folds train/test same majority, both at least5pp from50%, same nonzero mean raw-error sign; training-majority CRPS<1.'}
 save(OUT/'v51_center_bias_summary.json',bias)
 permutation=joined('feature_permutation','statistics');assert len(permutation)==2000
 primary=models['PRICE_FULL']
 perm={'executive_summary':'2000 train-origin vector permutations, all donors matured and known at fold cutoff; heldout features unchanged. No PRICE_FULL refit.','replicates':2000,'seed':SEED,'CRPS_ratio':distribution(permutation[:,0]),'balanced_accuracy':distribution(permutation[:,1]),'Spearman':distribution(permutation[:,2]),'Monte_Carlo_p_ratio':float((1+(permutation[:,0]<=primary['CRPS_ratio']).sum())/2001),'Monte_Carlo_p_balanced_accuracy':float((1+(permutation[:,1]>=primary['balanced_accuracy']).sum())/2001),'Monte_Carlo_p_Spearman':float((1+(permutation[:,2]>=primary['Spearman']).sum())/2001)}
 save(OUT/'feature_permutation_summary.json',perm)
 random={}
 for kind in 'ABCD':
  a=joined('random_sign','statistics',kind+'-*.npz');assert len(a)==5000
  random[kind]={'matching':{'A':'overall','B':'asset','C':'horizon','D':'fold'}[kind],'replicates':5000,'ratio':distribution(a[:,0]),'balanced_accuracy':distribution(a[:,1]),'fraction_equal_or_better':float((a[:,0]<=primary['CRPS_ratio']).mean()),'p_plus_one':float((1+(a[:,0]<=primary['CRPS_ratio']).sum())/5001)}
 save(OUT/'random_sign_summary.json',{'executive_summary':'5000 target-blind exact prevalence sign permutations each; the inherited MATCHED_RANDOM row remains separately frozen.','seed':SEED,'controls':random})
 ci={};cols=['PRICE_FULL_ratio','PRICE_FULL_minus_V51','PRICE_FULL_minus_intercept','PRICE_FULL_minus_structure','PRICE_FULL_minus_random_median','PRICE_FULL_minus_majority','balanced_accuracy','Spearman','oracle_capture']
 for block in ['origin','year','quarter']:
  a=joined('bootstrap','statistics',block+'-*.npz');assert len(a)==5000
  ci[block]={n:np.nanquantile(a[:,j],[.025,.975]).tolist() for j,n in enumerate(cols)}
 save(OUT/'bootstrap_summary.json',{'executive_summary':'5000 paired block draws each; random median recomputed from5000 prevalence-matched vectors in every resample. Only5 years constrain year inference.','seed':SEED,'methods':ci,'blocks':{'origin':int(rows.origin.nunique()),'year':int(rows.year.nunique()),'quarter':int(pd.to_datetime(rows.origin).dt.to_period('Q').nunique())},'negative_difference_favors_PRICE_FULL':True,'no_IID_cells':True})
 gain=base-loss[names.index('PRICE_FULL')];concentration={}
 for field in ['year','origin','horizon']:
  g=pd.Series(gain).groupby(rows[field]).sum().clip(lower=0);concentration[field]=float(g.max()/g.sum()) if g.sum()>0 else 1.
 # Saved fold models only; standardized coefficients, no outcome refitting.
 audits=[next(a for a in json.loads((parent_private()/'folds'/f'{year}.json').read_text()) if a['model']=='PRICE_LOGISTIC') for year in YEARS]
 coefficients=np.array([a['coefficients'][0] for a in audits]);means=np.array([a['scaler_mean'] for a in audits]);sd=np.array([a['scaler_scale'] for a in audits]);cos=coefficients@coefficients.T/np.outer(np.linalg.norm(coefficients,axis=1),np.linalg.norm(coefficients,axis=1))
 coeff={'executive_summary':'Saved standardized fold coefficients; no fit or coefficient-driven feature selection.','feature_names':list(PRICE_NAMES)+['asset_5Y','log_horizon'],'folds':audits,'cosine_similarity':cos,'sign_consistency_per_feature':np.maximum((coefficients>0).mean(axis=0),(coefficients<0).mean(axis=0)),'mean_sign_consistency':float(np.maximum((coefficients>0).mean(axis=0),(coefficients<0).mean(axis=0)).mean()),'top_one_abs_coefficient_concentration':np.max(abs(coefficients),axis=1)/np.sum(abs(coefficients),axis=1),'top_three_abs_coefficient_concentration':np.sort(abs(coefficients),axis=1)[:,-3:].sum(axis=1)/np.sum(abs(coefficients),axis=1),'successive_scaler_mean_change_in_previous_SD':np.diff(means,axis=0)/sd[:-1],'successive_scaler_SD_ratio':sd[1:]/sd[:-1]}
 save(OUT/'coefficient_stability.json',coeff)
 ro=models['PERFECT_LOCATION']['CRPS_ratio'];capture=(1-primary['CRPS_ratio'])/(1-ro)
 save(OUT/'oracle_summary.json',{'executive_summary':'Same frozen future-informed perfect-location headroom, no forecast claim or public cell answers.','R_PERFECT_LOCATION':ro,'same_ledger':True})
 save(OUT/'oracle_capture.json',{'executive_summary':'Unclipped mathematical capture; no predictability inference.','PRICE_ORACLE_CAPTURE':capture,'formula':'(1-R_PRICE)/(1-R_PERFECT_LOCATION)'})
 gains={'vs_intercept':models['INTERCEPT_ONLY']['CRPS_ratio']-primary['CRPS_ratio'],'vs_structure':models['STRUCTURE_ONLY']['CRPS_ratio']-primary['CRPS_ratio'],'vs_inherited_random':models['MATCHED_RANDOM']['CRPS_ratio']-primary['CRPS_ratio'],'vs_random_median':random['A']['ratio']['q50']-primary['CRPS_ratio']}
 save(OUT/'price_full_summary.json',{'executive_summary':'Exact inherited PRICE_LOGISTIC, never refitted. All new models are controls.','PRICE_FULL':primary,'incremental_gain':gains,'gross_gain_concentration':concentration,'original_prediction_SHA256':array_hash(parent['prob_PRICE_LOGISTIC']),'no_new_candidate':True})
 save(OUT/'constant_shift_summary.json',{'executive_summary':'Both fixed signs reported; no best constant is promoted.','controls':{n:models[n] for n in ['CONSTANT_UP','CONSTANT_DOWN','TRAINING_MAJORITY']},'amplitude_SD':AMPLITUDE})
 annual=[x['CRPS_ratio'] for x in aggregate_tables['year'] if x['model']=='PRICE_FULL']
 verdict,nxt,gates,evidence=decide(models,annual,perm,random,ci,bias,concentration,'C',balanced['ORIGIN_BALANCED']['PRICE_FULL'])
 attribution={'executive_summary':'Exposed forensic attribution only; quantitative null/bias conditions frozen before diagnostics.','central_conclusion':verdict,'gates':gates,'evidence':evidence,'incremental_gain':gains,'persistent_center_bias':bias['persistent_center_bias'],'concentration':concentration,'TIMING_SPECIFIC_PRICE_INFORMATION':'NOT_ESTABLISHED' if any(models[f'PRICE_LAG_{d}BD']['CRPS_ratio']<=primary['CRPS_ratio'] for d in LAGS) else 'EXPOSED_DESCRIPTIVE_ONLY','PRICE_SPECIFIC_INFORMATION':'NOT_ESTABLISHED' if evidence['random_frequently_beats'] or not gates['permutation_support'] else 'EXPOSED_DESCRIPTIVE_ONLY'}
 save(OUT/'information_attribution.json',attribution)
 decision={'executive_summary':'Audit complete; no model redesign, official submission, independent OOS or next study.','PRICE_STATE03_RESULT':verdict,'NEXT':nxt,'PRE_RESULT_PRICE_STATE03_SHA':receipt['PRE_RESULT_PRICE_STATE03_SHA'],'parent_RESULT_SHA':PARENT,'primary_ratio':primary['CRPS_ratio'],'PRICE_DATA_PIT':'C','BROAD_TRANSFER_READY':False,'independent_validation':'NOT_AVAILABLE','submission_readiness':False,'V51_reference':.9541,'gates':gates}
 save(OUT/'final_decision.json',decision);save(OUT/'next_axis_decision.json',{'executive_summary':'Exactly one next separately frozen study; not executed.','NEXT':nxt,'basis':verdict,'executed':False})
 make_report(decision,models,aggregate_tables,balanced,perm,random,ci,bias,attribution,coeff)
 status('REPORT_COMPLETE','final_decision.json');print(json.dumps(clean(decision),indent=2),flush=True)

def table(items,cols):return '| '+' | '.join(cols)+' |\n| '+' | '.join(['---']*len(cols))+' |\n'+'\n'.join('| '+' | '.join(f'{r[c]:.6f}' if isinstance(r.get(c),float) else str(r.get(c,'—')) for c in cols)+' |' for r in items)
def make_report(decision,models,tables,balanced,perm,random,ci,bias,attribution,coeff):
 selected=['V5.1','TRAINING_MAJORITY','INTERCEPT_ONLY','STRUCTURE_ONLY','PRICE_21BD','PRICE_FULL','MATCHED_RANDOM','CONSTANT_UP','CONSTANT_DOWN','PERFECT_LOCATION']
 sections=['## Executive summary (read this first)',f"Audit completed: **{decision['PRICE_STATE03_RESULT']}**. Exactly one next axis: **{decision['NEXT']}**, not executed. PRICE_FULL is the original parent PRICE_LOGISTIC, not a new candidate. All outcomes are already research-exposed. No independent OOS, alpha validation, submission, amplitude optimization or favorable subset is claimed.",
 '## Parent reproduction',f"Parent RESULT {PARENT}; parent PRE {PARENT_PRE}; new PRE {decision['PRE_RESULT_PRICE_STATE03_SHA']}. Every parent model loss array is bitwise reproduced with the imported common v2.4.3 scorer; ratio tolerance1e-14. Saved fold scaler/coefficients reproduce saved probabilities within1e-14. Saved probabilities and original draws remain unchanged. Initial launch/import and Unicode Git-path protection errors were diagnosed before evaluation and corrected; no completed research was restarted.",
 '## Main comparison',table([dict(model=n,**models[n]) for n in selected],['model','CRPS_ratio','sign_accuracy','balanced_accuracy','Spearman']),
 '## Incremental price information',json.dumps(clean(attribution['incremental_gain']),indent=2),f"Feature-permutation Monte Carlo p (lower CRPS): {perm['Monte_Carlo_p_ratio']:.6f}. The predeclared price-information gate requires ratio≤0.990, both null/structure increments≥0.003, direction evidence, stable years/blocks and usable PIT. All gates: {json.dumps(decision['gates'],sort_keys=True)}.",
 '## Training bias and nulls',json.dumps(clean(bias),indent=2),
 '## Feature permutation and random signs',f"2000 whole-price-vector train-origin permutations: {json.dumps(perm)}. Historical donors are all admitted and matured by the fold cutoff; they may move across earlier train origins, but never from test/future folds. This is a fold-conditional null, not a simulated tradable historical path. Test features and structural covariates are fixed.",table([dict(kind=k,**v['ratio'],fraction_equal_or_better=v['fraction_equal_or_better']) for k,v in random.items()],['kind','mean','q05','q50','q95','fraction_equal_or_better']),
 '## Annual stability',table([r for r in tables['year'] if r['model'] in ['PRICE_FULL','INTERCEPT_ONLY','STRUCTURE_ONLY','MATCHED_RANDOM']],['group','model','cells','CRPS_ratio','sign_accuracy','balanced_accuracy','Spearman']),
 '## Asset stability',table([r for r in tables['asset'] if r['model']=='PRICE_FULL'],['group','cells','CRPS_ratio','sign_accuracy','balanced_accuracy','Spearman']),
 '## Horizon stability',table([r for r in tables['horizon'] if r['model']=='PRICE_FULL'],['group','cells','CRPS_ratio','sign_accuracy','balanced_accuracy','Spearman']),
 '## Equal-origin/year evidence',table([dict(method=k,**v['PRICE_FULL']) for k,v in balanced.items()],['method','CRPS_ratio','sign_accuracy','balanced_accuracy','Spearman']),
 '## Paired block bootstrap',table([dict(block=k,**v) for k,v in ci.items()],['block','PRICE_FULL_ratio','PRICE_FULL_minus_intercept','PRICE_FULL_minus_structure','PRICE_FULL_minus_random_median','balanced_accuracy','Spearman']),
 '## Timing, feature groups and coefficients',f"Timing-specific information: {attribution['TIMING_SPECIFIC_PRICE_INFORMATION']}. Fixed5/21/63 weekday lags and LEVEL/CHANGE/CURVE controls are all reported in artifacts; no best lag/group becomes a candidate. Mean coefficient sign consistency {coeff['mean_sign_consistency']:.6f}; full standardized coefficients, fold cosine similarities, concentration and scaler drift are in coefficient_stability.json. Coefficient size alone does not validate information.",
 '## Price point-in-time integrity and broader transfer','PIT remains C. The archived bounded FRED/H15 probe is current-vintage. Official observation dates plus one weekday EOD and previous-weekday16:00NY cutoff prevent same-day premature activation, but cannot recover unknown later revisions. FRED represents latest vintage; ALFRED has dated vintage semantics. No original contemporaneous price vintage was acquired or revisions bounded. Therefore validated price alpha is unavailable. Exact raw source hash and all14 transformations are in price_feature_manifest.csv and price_pit_audit.json. Public Federal Reserve rates require attribution; offline reconstruction is feasible only after a separate PIT acquisition audit. Broader canonical LOCATION01 ledger exists, but PRICE_DATA_PIT is insufficient, so BROAD_TRANSFER_READY=false. Its canonical all-origin specification was frozen before diagnostics; no broader outcomes were evaluated or substitute favorable origins invented.',
 '## Concentration and limitations',f"Largest positive gross gain shares by year/origin/horizon: {json.dumps(attribution['concentration'])}. Parent ledger has52 origins and482 cells, monthly gaps, only five years, quarterly SEP eligibility conditioning and repeated cells per origin. No IID cell bootstrap. Ties receive zero directional credit; V5.1 and perfect-location oracle directional metrics are not predictive metrics. Same-ledger oracle is mathematical headroom. PIT and dependence prevent independent claims. All years, assets and horizons remain in the main result.",
 '## Verdict and next axis',f"**{decision['PRICE_STATE03_RESULT']}**. **{decision['NEXT']}** is the only selected future axis. Quantitative attribution: {json.dumps(clean(attribution),sort_keys=True)}. No next experiment is executed.",
 '## Baseline, tests and recovery','All parent tracked files, main, V5.1 source and submission files are hash-protected and unchanged. Official previously verified V5.1 Development reference0.9541 is not remeasured. No Docker package is overwritten; existing binary-package byte verification remains limited by the preserved evidence. Research, affected, full repository and common tests are recorded in execution_audit.json. PRE is remotely verified before new diagnostic labels; final RESULT/remote files/main/tree and private recovery CRC/member SHA/archive SHA are bound by an external completion receipt to avoid self-reference. RUNBOOK.md documents stages and exact continuation points.']
 (ROOT/'PRICE-STATE-INFORMATION-AUDIT-03-report.md').write_text('\n\n'.join(sections)+'\n')
if __name__=='__main__':run()
