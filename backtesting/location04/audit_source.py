"""Executive summary: publication/representation gate, before future-error labels."""
import argparse,csv,json
from pathlib import Path
import pandas as pd
from .acquire import OUT,save,write_csv,status
from .source_dataset import source_dates,publication_after_minutes,activation,policy_rows,state_from_release,digest,STATISTIC

def run(private):
 rows=list(csv.DictReader((OUT/'spd_release_universe.csv').open()));events=json.loads((private/'fomc_calendar.json').read_text());pub=[];errors=[];documents=[];errata=[];fields=[];states=[]
 for row in rows:
  rid=row['survey_id'];text=(private/'source'/rid/'results.txt').read_text();(dist,due),detail=(('2023-04-19','2023-04-24'),{'hidden_template_date_conflict':False,'visual_source':'original May2023 page1'}) if rid=='2023-May' else source_dates(text,int(row['year']));row['SURVEY_DISTRIBUTED_AT']=dist;row['SURVEY_DUE_AT']=due
  matches=[e for e in events if 0<=(pd.Timestamp(e['FOMC_EVENT_DATE'])-pd.Timestamp(due)).days<=30]
  if not matches:raise ValueError('No source deadline/FOMC match '+rid)
  ev=min(matches,key=lambda e:e['FOMC_EVENT_DATE']);date=publication_after_minutes(ev['minutes_publication']);row['FOMC_EVENT_DATE']=ev['FOMC_EVENT_DATE'];row['RESULT_PUBLIC_AVAILABLE_AT']=activation(date).isoformat();row['publication_evidence']='NYFed post-minutes publication rule + official actual FOMC minutes publication date';row['timing_eligible']=not (int(row['year'])==2011 and 'December' not in rid) and date<='2024-12-18'
  if rid=='2011-December':assert date=='2012-01-04';row['publication_evidence']='Explicit NYFed January 4, 2012 media advisory'
  if rid=='2024-September':assert date=='2024-10-10';row['publication_evidence']='Explicit NYFed October 10, 2024 operating policy notice'
  receipt=json.loads((private/'source'/rid/'results.pdf.receipt.json').read_text());row['source_hash']=receipt['sha256'];row['retrieval_timestamp']=receipt['retrieved_at']
  try:f,st=policy_rows(private,row);row['extraction_status']=st;fields+=f
  except Exception as e:row['extraction_status']='UNRESOLVED_EXTRACTION';errors.append({'survey_id':rid,'error':str(e)});f=[]
  for kind in ['question','results']:
   d=json.loads((private/'source'/rid/(kind+'.pdf.receipt.json')).read_text());assert digest(private/'source'/d['path'])==d['sha256'];documents.append(dict(d,survey_id=rid,kind=kind,panel='SPD'))
  errata.append({'survey_id':rid,'archive_appendix_marker':row['appendix_update_marker'],'updated_responses_appendix':'updated responses' in text.lower(),'hidden_template_date_conflict':detail['hidden_template_date_conflict'],'primary_policy_path_amendment_evidence':'none identified; PIT grade B, no immutable historical byte claim','treatment':'appendices excluded; no amended path substituted'})
  pub.append({'survey_id':rid,'panel':'SPD','distributed_at':dist,'due_at':due,'FOMC_event_date':ev['FOMC_EVENT_DATE'],'minutes_publication':ev['minutes_publication'],'result_public_date':date,'result_available_at':row['RESULT_PUBLIC_AVAILABLE_AT'],'evidence':row['publication_evidence'],'calendar_evidence':ev['calendar_evidence_path'],'timing_eligible':row['timing_eligible'],'intraday_rule':'end of publication date America/New_York','PIT_grade':'B'})
 rows.sort(key=lambda r:r['RESULT_PUBLIC_AVAILABLE_AT']);previous=[]
 for row in rows:
  f=[x for x in fields if x['survey_id']==row['survey_id']];state=state_from_release(row,f,previous);state['timing_eligible']=row['timing_eligible'];state['full5_usable_at_release'] &= bool(row['timing_eligible']);states.append(state);previous=f
 usable=[s for s in states if s['full5_usable_at_release']];years=sorted({int(s['publication_date'][:4]) for s in usable});eras=sorted({('2016-2019' if y<=2019 else '2020-2021' if y<=2021 else '2022-2024') for y in years})
 ready=not errors and len(usable)>=30 and len(years)>=8 and len(eras)>=3
 save(private/'source_states.json',states);save(private/'source_extraction_errors.json',errors);write_csv(OUT/'spd_release_universe.csv',rows);write_csv(OUT/'spd_publication_ledger.csv',pub);write_csv(OUT/'spd_errata_ledger.csv',errata)
 if fields:write_csv(OUT/'spd_policy_field_ledger.csv',fields)
 save(OUT/'spd_document_manifest.json',{'executive_summary':'Official original SPD PDFs, not SMP; raw copyrighted files private.','documents':documents})
 save(OUT/'spd_panel_integrity.json',{'executive_summary':'Only first archive panel SPD admitted; SMP excluded.','SPD_rounds':len(rows),'SMP_admitted':0,'fallback':False})
 save(OUT/'spd_questionnaire_breaks.json',{'executive_summary':'Direct published midpoint modal median selected before outcomes.','canonical_statistic':STATISTIC,'canonical_start':'2016-March','earlier_split_top_bottom':'excluded, medians not averaged','probability_bins':'excluded, no arbitrary expectation','appendix':'excluded','errors':errors})
 gate={'executive_summary':'No future-error labels loaded. Gate >=30 FULL5 releases, >=8 years, >=3 eras, complete deterministic extraction.','DATASET_READY':ready,'enumerated_releases':len(rows),'original_PDFs':len(documents),'usable_FULL5_releases':len(usable),'usable_calendar_years':years,'policy_eras':eras,'same_target_revisions':sum(s['POLICY_REVISION_SAME_TARGET'] is not None and s['timing_eligible'] for s in states),'effective_independent_release_count':len(usable),'PIT_grade':'B','unresolved_extractions':errors,'new_outcomes_accessed':False}
 save(OUT/'spd_dataset_readiness.json',gate);status('source_gate',DATASET_READY=ready,usable_releases=len(usable));print(json.dumps(gate,indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--private',type=Path,required=True);run(ap.parse_args().private)
