"""## Executive summary (read this first)
Add reproducible reporting diagnostics and recovery audit without changing frozen forecasts or gates.
"""
import argparse,json,subprocess,time
from pathlib import Path
import numpy as np
from qfbench2_track_forecasting.ceiling01.scorer_adapter import aggregate,composite_from_components
from .freeze_annotations import dump,digest,verify
from .diagnostics import skill

def run(root,private):
 verify(root);r=root/'backtesting/context01/results';records=[json.loads(f.read_text())for f in sorted((private/'scored').glob('loco_card*.json'))];assert len(records)==24
 y=np.concatenate([c['text_effect']['numeric_oracle_delta']for c in records]);z=np.concatenate([c['text_effect']['z_shift']for c in records]);active=abs(z)>1e-12;f=r/'text_effect_summary.json';text=json.loads(f.read_text());text['active_only_descriptive']=dict(active_cells=int(active.sum()),total_cells=63,active_cards=sum(any(abs(v)>1e-12 for v in c['text_effect']['z_shift'])for c in records),metrics=skill(y[active],z[active]),interpretation='Only five nonzero median text shifts; descriptive sparse subset, never used to select/tune. Zero shifts count as incorrect sign against nonzero residual in the all63cell metric.')
 text['alternative_numeric_component_reference']=dict(full_text_over_numeric=aggregate([composite_from_components(c['baseline'],c['models']['B_NUMERIC'],c['cells'])for c in records]),pure_location_over_numeric=aggregate([composite_from_components(c['models']['TEXT_LOCATION'],c['models']['B_NUMERIC'],c['cells'])for c in records]),interpretation='Supplementary rescaling using original imported composite adapter with numeric component denominators. Frozen decision uses the primary unchanged TEXT component reference, so gates are unchanged.')
 dump(f,{k:v for k,v in text.items()if k!='executive_summary'})
 f=r/'residual_oracle_summary.json';oracle=json.loads(f.read_text())
 for name,g in oracle['groups'].items():
  recs=records if name=='all'else([c for c in records if c['single']]if name=='single'else([c for c in records if not c['single']]if name=='multi'else[c for c in records if c['family']==name]));g['feasible_joint_subset_cards']=sum(c['location_joint_oracle']is not None for c in recs);g['location_plus_feasible_joint_all_group_cards']=aggregate([(c['location_joint_oracle']or c['oracle'])['ratio']for c in recs])
 dump(f,{k:v for k,v in oracle.items()if k!='executive_summary'})
 folds=[json.loads(f.read_text())for f in (private/'crossfit').glob('*.json')];count=0
 for a in folds:
  for model,v in a['models'].items():
   assert not(set(v['training_card_ids'])&set(v['held_out_card_ids']));count+=1
   if a['mode']=='family':assert v['train_cards']==18 and v['test_cards']==6
 assert count==620
 score_counts={m:len(list((private/'scored').glob(m+'_card*.json')))for m in ['loco','family','chrono']};assert score_counts==dict(loco=24,family=24,chrono=18)
 audit=dict(PRE_RESULT_CONTEXT01_SHA='a57c11701ae2b9383882673b14680e16c8d9cdea',original_tests='520passed/2skipped;250common passed;22new tests',runtime_recovery='Ephemeral workspace reverted to earlier snapshot. Restored exact PRE branch and161private files from durable checkpoint;168experts reused. Four early fold files were absent from checkpoint and rebuilt exactly, not retuned. Restored narwhals2.26.0purePython dependency;22research tests passed after recovery.',fit_folds=count,card_folds=24,family_folds=4,chrono_folds=3,scored_card_counts=score_counts,variants_per_card=39,model_component_rescores=66*39,matched_asof_expert_fits=168,all_same_card_leakage_assertions='PASS',post_freeze_reporting_correction='Converted candidate/control NumPy ratio vector to list for unchanged imported aggregate adapter. No fit, prediction, source, score formula, model choice, gates, annotations or routing changed.',protocol_sha256=digest(root/'backtesting/context01/frozen_protocol.json'),recovered_tests_log_sha256=digest(private/'recovered-context-tests.log'),future_model_runs_after_reporting_change=0)
 audit['public_singleton_subgroups']='Counts and suppression status only; complete metrics retained privately. Publication redaction never excludes any card from evaluation.'
 dump(r/'execution_audit.json',audit)
 report=root/'CONTEXT-01-CARD-SEMANTIC-LOCATION-report.md';s=report.read_text();s+='\nReporting and recovery audit: original repository tests520passed/2skipped, common250passed, new research22passed. After runtime rollback, the exact PRE and161saved private files were restored;168expert fits reused; the four early ephemeral folds were absent and rebuilt with identical frozen rules. Research tests22passed after dependency restoration. All620model/fold disjointness assertions and66card score records were verified, covering2574variant/card component rescores. The sole post-freeze code correction converted a NumPy vector to a list for the existing reporting aggregate adapter. No forecasts or acceptance rules changed.\n'
 s+=f"\nExisting text shifts are sparse: {int(active.sum())}/63nonzero median shifts on {text['active_only_descriptive']['active_cards']}/24cards. The five active shifts all match residual direction, but this is a tiny descriptive subset. The all-cell7.94%sign metric counts58zero forecasts as incorrect against nonzero truth. Correlation and calibration on this exposed sample cannot justify amplifying the text signal. No amplitude was retuned.\n"
 s+='\n|Scope|Perfect residual location|Perfect residual marginal|Feasible location+joint on multi subset|Subset cards|\n|---|---:|---:|---:|---:|\n'
 for name,g in oracle['groups'].items():
  s+=f"|{name}|{g['perfect_residual_location_composite_ratio']:.6f}|{g['perfect_residual_location_marginal_ratio']:.6f}|{g['feasible_location_joint_composite_ratio'] if g['feasible_location_joint_composite_ratio'] is not None else 'NA'}|{g['feasible_joint_subset_cards']}|\n"
 s+='\nF1 perfect median correction itself has composite1.706269despite marginal0.808881: pure location can harm path consistency even with hindsight. Learned models do not meet the predeclared location-signal/path-required flag because their F1marginal also fails to improve. Joint-oracle subset rows above contain only multi cards; the JSON additionally retains the full group aggregate with single-card location oracle substituted.\n'
 multi=json.loads((r/'multi_summary.json').read_text())['models'];s+='\n|Model|Multi marginal|Multi joint|Multi tail|Multi composite|Single wins/13|Multi wins/11|\n|---|---:|---:|---:|---:|---:|---:|\n';single=json.loads((r/'single_summary.json').read_text())['models']
 for k,v in multi.items():s+=f"|{k}|{v['marginal_ratio']:.6f}|{v['joint_ratio']:.6f}|{v['tail_ratio']:.6f}|{v['geometric_composite_ratio']:.6f}|{single[k]['card_wins']}|{v['card_wins']}|\n"
 s+='\nR2has composite0.980115and capture3.893%, below the frozen3%composite and>5%capture requirements. Multi composite1.024592fails safety; only2/4family holdouts improve; every matched control does not clear both paired uncertainty tests. Its whole-card95composite interval[0.910743,1.036203]and stratified interval[0.913284,1.035592]cross1. Thus routing is only descriptively WEAK and CONTEXT-01 remains NO. The weaker accepted gates are not met by any semantic or routed model.\n'
 s+='\nPublic firewall: singleton context/topic subgroups retain counts and suppression status only; complete diagnostics remain private. All24cards remain in every primary evaluation.\n'
 report.write_text(s)
 dump(r/'artifact_manifest.json',dict(pre_result_sha=audit['PRE_RESULT_CONTEXT01_SHA'],public_hashes={str(f.relative_to(root)):digest(f)for f in sorted(r.iterdir())if f.is_file()and f.name!='artifact_manifest.json'},report_sha256=digest(report),private_scored_count=66,private_scored_hashes={f.name:digest(f)for f in (private/'scored').glob('*.json')}))
 print('Final report and reporting audit saved; frozen gates unchanged',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--private',type=Path,required=True);a=p.parse_args();run(a.root,a.private)
