"""Inventory actual data without fitting a forecaster or computing outcome scores.
Usage: PYTHONPATH=audit-deps python3 audit_data.py official/units receipts/alpha19-newdata/ecb
"""
import collections,hashlib,json,pathlib,re,sys,tomllib,zipfile,io
import pandas as pd
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(__file__).parent/'results';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):(out/name).write_text(json.dumps(obj,indent=2,default=str)+'\n')
panels={};docs={};entries=[];issues=[];cards=[];raw_rows=0;cells={};panel_semantics=collections.defaultdict(set)
for cp in sorted(root.glob('*/card.toml')):
 card=tomllib.loads(cp.read_text());asof=card.get('provenance',{}).get('data_cutoff');cards.append({'card':cp.parent.name,'asof':asof,'sha256':sha(cp),'public_release_date':card.get('provenance',{}).get('public_release_date'),'redistributable':card.get('provenance',{}).get('redistributable'),'license':card.get('provenance',{}).get('license')})
 for name,meta in card.get('panels',{}).items():
  if isinstance(meta,dict):panel_semantics[name].add(str(meta.get('frequency')))
 idx=cp.parent/'text/corpus_index.json'
 if idx.exists():
  for e in json.loads(idx.read_text()).get('documents',[]):
   p=idx.parent/e.get('file','NOFILE');ts=str(e.get('timestamp',''));rec={'card':cp.parent.name,'asof':asof,'file':str(p.relative_to(root)),'timestamp':ts,'doc_type':e.get('doc_type'),'source':e.get('source')}
   if not p.is_file():issues.append(dict(rec,issue='missing_document'));continue
   h=sha(p);text=p.read_text(errors='replace');url=re.findall(r'https?://[^\s|<>]+',text[:1500]);rec.update(sha256=h,source_urls=url)
   if ts[:10]>str(asof):issues.append(dict(rec,issue='after_card_asof'))
   if not re.match(r'^\d{4}-\d{2}-\d{2}',ts):issues.append(dict(rec,issue='invalid_publication_date'))
   entries.append(rec)
   if h not in docs:docs[h]={'sha256':h,'bytes':p.stat().st_size,'timestamps':[],'doc_types':[],'sources':[],'source_urls':url,'paths':[]}
   for key,value in [('timestamps',ts),('doc_types',e.get('doc_type')),('sources',e.get('source')),('paths',str(p.relative_to(root)))]:
    if value not in docs[h][key]:docs[h][key].append(value)
 for p in sorted(cp.parent.glob('*.parquet')):
  h=sha(p)
  if h in panels:panels[h]['paths'].append(str(p.relative_to(root)));continue
  df=pd.read_parquet(p);raw_rows+=len(df);acol=next((x for x in ['asset','asset_id'] if x in df),None)
  rec={'sha256':h,'paths':[str(p.relative_to(root))],'rows':len(df),'columns':list(df.columns),'missing_by_column':df.isna().sum().to_dict()}
  if acol and 'date' in df and 'value' in df:
   dates=df.date.astype(str).str[:10];rec.update(date_min=dates.min(),date_max=dates.max(),assets=sorted(df[acol].astype(str).unique().tolist()),duplicated_asset_date=int(df.assign(_date=dates).duplicated([acol,'_date']).sum()))
   rec['vintage_columns']=[x for x in df if re.search(r'vintage|realtime|available|release|published',x,re.I)]
   # Panel identity preserved: NEVER merge ECB and H.10 quotes just by currency ticker.
   for asset,date,value in zip(df[acol].astype(str),dates,df.value):
    if pd.isna(value):continue
    key=(p.stem,asset,date);v=float(value)
    if key not in cells:cells[key]={'first':v,'conflict':False}
    elif cells[key]['first']!=v:cells[key]['conflict']=True
  panels[h]=rec
conflicts=[{'panel':k[0],'asset':k[1],'date':k[2]} for k,v in cells.items() if v['conflict']]
textyears=collections.Counter();types=collections.Counter();dates=collections.Counter()
for d in docs.values():
 if len(d['timestamps'])==1:textyears[d['timestamps'][0][:4]]+=1;dates[d['timestamps'][0][:10]]+=1
 else:issues.append({'sha256':d['sha256'],'issue':'conflicting_document_timestamps','timestamps':d['timestamps']})
 for t in d['doc_types']:types[t]+=1
coverage={}
for panel,asset,date in cells:
 key=panel+'/'+asset
 if key not in coverage:coverage[key]={'date_min':date,'date_max':date,'observations':0}
 coverage[key]['date_min']=min(coverage[key]['date_min'],date);coverage[key]['date_max']=max(coverage[key]['date_max'],date);coverage[key]['observations']+=1
source=pathlib.Path(sys.argv[2]);ecb={'file':source.name,'sha256':sha(source),'bytes':source.stat().st_size,'historical_vintage':'NOT_AUTHENTICATED_CURRENT_SNAPSHOT'}
if zipfile.is_zipfile(source):
 with zipfile.ZipFile(source) as z:
  ecb['members']=z.namelist();csv=next(x for x in z.namelist() if x.endswith('.csv'));df=pd.read_csv(io.BytesIO(z.read(csv)));ecb.update(rows=len(df),columns=list(df.columns),first_column_min=str(df.iloc[:,0].min()),first_column_max=str(df.iloc[:,0].max()),missing_by_column=df.isna().sum().to_dict())
else:ecb['format']='NOT_ZIP'
summary={'official_units':len(cards),'unique_panel_bytes':len(panels),'rows_across_unique_panel_files_not_independent':raw_rows,'deduplicated_panel_asset_date_cells':len(cells),'conflicting_panel_asset_date_cells':len(conflicts),'documents_references':len(entries),'unique_text_byte_hashes':len(docs),'distinct_document_dates':len(dates),'unique_text_by_year':dict(sorted(textyears.items())),'unique_text_by_type':dict(types),'source_url_present':sum(bool(d['source_urls']) for d in docs.values()),'date_only_timestamps':sum(all(len(x)==10 for x in d['timestamps']) for d in docs.values()),'issues':issues,'market_coverage':coverage,'inherited_ecb_snapshot':ecb,'vintage_columns_present_panels':sum(bool(d.get('vintage_columns')) for d in panels.values()),'training_executed':False,'new_outcome_scores_computed':False}
save('data-inventory.json',summary);save('panel-manifest.json',list(panels.values()));save('document-manifest.json',list(docs.values()));save('document-references.json',entries);save('card-manifest.json',cards);save('panel-conflicts.json',conflicts)
print(json.dumps({k:v for k,v in summary.items() if k not in ['market_coverage','issues','inherited_ecb_snapshot']},indent=2));print('issue_count',len(issues));print('ecb',json.dumps(ecb));print('Audit complete; no model training/scoring.')
