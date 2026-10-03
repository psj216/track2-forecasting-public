"""Executive summary: complete source-only Gate A before any labels are loaded."""
import sys,pathlib,json,re,subprocess,hashlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]))
from backtesting.location03.source_dataset import *
ROOT=Path(__file__).resolve().parents[3];R=ROOT/'location03-repo';OUT=R/'backtesting/location03/results';RAW=ROOT/'location03-private/source'
u=json.loads((RAW/'universe.json').read_text());fields=[];pub=[];docs=[];states=[];errors=[];excluded=[]
for row in u:
 if row['scope']!='candidate':continue
 rid=row['release_id'];d=RAW/rid
 try:
  manifest=json.loads((d/'manifest.json').read_text());soup=BeautifulSoup((d/'main.html').read_bytes(),'html.parser');text=normalize(soup.get_text(' ',strip=True));date=publication(text)
  special='supplementary' in text.lower() and row['survey_month']=='September'
  pub.append(dict(release_id=rid,survey_year=row['survey_year'],survey_month=row['survey_month'],publication_date=date,available_at=activation(date).isoformat(),evidence='Dated original-round official HTML footer; release-specific date',official_url=row['original_url'],timing_status='verified'))
  for name,key in [('main.html','original_url'),('table1.html','table_url'),('table1.pdf','table_pdf_url'),('full.pdf','full_pdf_url')]:
   p=d/name
   if p.exists():docs.append(dict(release_id=rid,path=str(p.relative_to(RAW)),original_url=row['original_url'] if key=='original_url' else manifest[key],sha256=digest(p),bytes=p.stat().st_size,type=p.suffix,rights='Official Federal Reserve public aggregate response table; individual responses not collected'))
  if special:
   excluded.append({'release_id':rid,'reason':'Supplementary Main Street Lending survey; four fixed C&I fields absent'});continue
  extracted=extract((d/'table1.html').read_bytes())
  pdfpath=d/'table1.pdf'
  if rid=='2017-October':pdftext=normalize(subprocess.check_output(['pdftotext','-raw',str(pdfpath),'-'],text=True))
  elif rid in ['2022-April','2022-July','2023-July','2024-January']:
   ocr=ROOT/'location03-private/ocr'/rid;pdftext=normalize(' '.join(p.read_text() for p in sorted(ocr.glob('page-*.txt'))))
  elif rid=='2024-July':pdftext=normalize(' '.join(p.read_text() for p in sorted((ROOT/'location03-private/ocr2024').glob('page-*.txt'))))
  elif rid=='2024-April':
   pdfpath=d/'full.pdf';pdftext=normalize(' '.join(p.read_text() for p in sorted((ROOT/'location03-private/ocr/2024-April-full').glob('page-*.txt'))))
  else:pdftext=normalize(subprocess.check_output(['pdftotext','-layout',str(pdfpath),'-'],text=True))
  for j,e in enumerate(extracted):
   cats=STANDARDS if e['variable']=='standards' else DEMAND;k=j%2
   pdfcounts=[]
   for cat in cats:
    matches=re.findall(re.escape(cat)+r'\s+(\d+)[),]?\s+[\d.]+',pdftext)
    if len(matches)<2:raise ValueError('PDF extraction insufficient '+cat)
    pdfcounts.append(int(matches[k]))
   if pdfcounts!=e['counts']:raise ValueError('Original HTML/PDF count disagreement '+str((pdfcounts,e['counts'])))
   e.update(release_id=rid,publication_date=date,official_url=manifest['table_url'],source_sha256=digest(d/'table1.html'),pdf_count_agreement=True,denominator_rule='Sum five applicable response categories; excludes non-originators and nonresponses; never full survey N')
   fields.append(e)
  levels={kind:sum(e['net'] for e in extracted if e['variable']==kind)/2 for kind in ['standards','demand']}
  states.append(dict(release_id=rid,publication_date=date,CREDIT_STANDARDS=levels['standards'],CREDIT_DEMAND=levels['demand']))
 except Exception as e:errors.append({'release_id':rid,'error':str(e)})
print('universe',len(u),'candidate',sum(x['scope']=='candidate' for x in u),'states',len(states),'excluded',excluded,'errors',errors,flush=True)
write_csv(OUT/'sloos_publication_ledger.csv',pub)
flat=[]
for e in fields:
 f=e.copy();f['counts']=json.dumps(f['counts']);f['percentages']=json.dumps(f['percentages']);flat.append(f)
if flat:
 write_csv(OUT/'sloos_field_extraction.csv',flat);write_csv(OUT/'sloos_denominator_ledger.csv',[{k:e[k] for k in ['release_id','variable','borrower_size','counts','denominator','non_originating_explicit_count','denominator_rule','pdf_count_agreement']} for e in flat])
save(OUT/'sloos_document_manifest.json',{'documents':docs,'source_errors':errors,'sha256_covers_original_downloaded_bytes':True})
save(OUT/'sloos_field_semantics.json',{'population':'All applicable domestic-bank respondents in original Table 1; foreign banks excluded','borrower_groups':['annual sales >= $50 million','annual sales < $50 million'],'standards_categories':STANDARDS,'demand_categories':DEMAND,'net_definition':'100*(first+second-fourth-fifth)/sum(five categories)','borrower_aggregation':'unweighted average of exactly two available groups','non_originators':'excluded from applicable question total','feature_count':5})
save(OUT/'sloos_structural_breaks.json',{'official_documentation':'https://www.federalreserve.gov/data/sloos/about.htm','panel_expansion':'20 banks added in May 2012; July 2012 implementation per official 201224 revised PDF primer','admitted_first_survey':'January 2013','admitted_start_publication':'2013-02-04','exclude_all_pre_2013':True,'large_bank_asset_definition_changes':'2019 $50bn; October2023 $100bn; subgroup labels not features; original ALL domestic group used','other_question_changes':'CRE2013; housing2015; excluded questions do not enter fixed C&I fields','special_release_exclusions':excluded,'no_outcomes_used_to_choose_period':True})
save(OUT/'sloos_errata_ledger.json',{'official_announcements_url':'https://www.federalreserve.gov/feeds/sloos.html','announcements_sha256':digest(RAW/'announcements.html'),'events':[{'date':'2019-11-05','affected':'Chart Data HTML only','C_I_original_table_counts_affected':False},{'date':'2019-09-23','affected':'pre1997 C&I history and mortgage/reason DDP series; original tables correct','C_I_original_table_counts_affected':False},{'date':'2019-03-29','affected':'Table1 question31 wording and mortgage DDP; numeric tables unchanged','C_I_original_table_counts_affected':False},{'date':'2017-08-07','affected':'DDP missing July; original HTML correct','C_I_original_table_counts_affected':False},{'date':'2015-02-04','affected':'Table1 question17 unchanged category; household credit question','C_I_original_table_counts_affected':False},{'date':'2014-11-03','affected':'Missing chart figures','C_I_original_table_counts_affected':False}],'original_core_C_I_affected_corrections_found':0,'unknown_changes_not_proven_absent':True,'April2024_bad_table_pdf_link':{'linked_url':'https://www.federalreserve.gov/data/documents/sloos-202401-table1.pdf','action':'Reject January PDF for April row; verify April HTML counts against original official full April2024 report','verified_full_report_url':'https://www.federalreserve.gov/data/documents/sloos-202404.pdf'},'OCR_visual_corrections':'Original PDF first-column count reads verified visually before any forecasting labels; receipt in private recovery','HTML_template_HTTP_modified_not_activation_evidence':True,'original_round_HTML_PDF_counts_crosschecked':not errors})
s=states_from_rows(states);save(OUT/'source_states.json',{'states':s})
manifest=json.loads((R/'backtesting/location01/results/ledger_manifest.json').read_text());dates=sorted(str(x).removesuffix('.npz').removeprefix('origins/') for x in manifest['baseline_cache_sha256']);first={}
for date in dates:
 if '2013-01-01'<=date<='2024-12-18':first.setdefault(date[:7],date)
calendar=[]
for date in first.values():
 f=asof_features(s,date);c=dict(origin=date,cutoff=cutoff(date).isoformat(),active=bool(f),release_id=f['release_id'] if f else '',publication_date=f['publication_date'] if f else '')
 for feature in FEATURES:c[feature]=f[feature] if f else None
 calendar.append(c)
write_csv(OUT/'source_calendar.csv',calendar)
mutation=True
for c in calendar:
 future=[dict(x) for x in s]
 for x in future:
  if pd.Timestamp(x['available_at'])>cutoff(c['origin']):x['CREDIT_STANDARDS']=100000.
 if asof_features(s,c['origin'])!=asof_features(future,c['origin']):mutation=False
ready=not errors and len(states)==sum(x['scope']=='candidate' for x in u)-len(excluded) and mutation and len({c['release_id'] for c in calendar if c['active']})>=12
save(OUT/'sloos_pit_dataset_manifest.json',{'complete_archive_entries_enumerated':len(u),'eligible_round_entries':sum(x['scope']=='candidate' for x in u),'core_usable_releases':len(states),'active_full5_release_events':max(0,len(states)-1),'unusable_first_delta_event':s[0]['release_id'] if s else None,'source_period':'2013-02-04 through 2024-11-12','excluded_specials':excluded,'features':FEATURES,'age_limit_business_days':100,'timing':'date-only at 23:59:59 America/New_York; previous business day 16:00 origin cutoff','original_files_verified':len(docs)})
save(OUT/'sloos_dataset_readiness.json',{'DATASET_READY':ready,'complete_universe_enumerated':True,'official_provenance':not errors,'original_HTML_PDF_count_agreement':not errors,'future_mutation_passed':mutation,'errors':errors,'source_only_gate':True,'outcomes_loaded':False,'coverage':{'origins':len(calendar),'active_origins':sum(c['active'] for c in calendar),'unique_source_releases':len(states),'feature_usable_releases':max(0,len(states)-1)},'limitations':['Publication evidence uses release-specific dated official original-round HTML; no exact intraday time.','Original-round archived HTML and PDF plus official errata audit; absence of undocumented silent historical edits cannot be proven.']})
