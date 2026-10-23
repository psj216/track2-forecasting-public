"""Executive summary: recover non-overlapping official Treasury tables and published Fed statements."""
import concurrent.futures,hashlib,json,pathlib,urllib.request
root=pathlib.Path('receipts/alpha23/raw');root.mkdir(parents=True,exist_ok=True)
jobs={f'treasury-{y}':f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?field_tdr_date_value={y}&type=daily_treasury_yield_curve' for y in range(2024,2027)}
for s in ['20250129','20250319','20250507','20250618','20250730','20250917','20251029','20251210','20260128','20260318','20260429','20260617','20260729','20260916']:
 jobs['fed-'+s]='https://www.federalreserve.gov/newsevents/pressreleases/monetary'+s+'a.htm'
jobs['calendar']='https://www.federalreserve.gov/newsevents/pressreleases/monetary20240809a.htm'
def get(item):
 name,url=item;p=root/(name+'.html')
 try:
  if not p.exists():p.write_bytes(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read())
  return {'name':name,'url':url,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'status':'ACQUIRED'}
 except Exception as e:return {'name':name,'url':url,'error':str(e),'status':'FAILED'}
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for r in pool.map(get,jobs.items()):rows.append(r);print(r['name'],r['status'],flush=True);(root/'manifest.json').write_text(json.dumps(rows,indent=2))
