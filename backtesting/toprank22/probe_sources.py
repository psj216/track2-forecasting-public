"""Bounded primary-source access probes; current availability is not PIT evidence."""
import concurrent.futures,hashlib,json,pathlib,urllib.request,time
urls=[('fed2026','https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'),('fed2025statement','https://www.federalreserve.gov/newsevents/pressreleases/monetary20250129a.htm'),('ecb_current_history','https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip'),('treasury2026','https://home.treasury.gov/resource-center-data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=2026')]
root=pathlib.Path('/tmp/toprank22-primary-probes');root.mkdir(exist_ok=True)
def probe(pair):
 name,url=pair;t=time.monotonic()
 try:
  request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 research-data-audit'})
  with urllib.request.urlopen(request,timeout=30) as response:
   data=response.read(10000000);status=response.status;ctype=response.headers.get('Content-Type');final=response.url
  (root/name).write_bytes(data)
  return {'name':name,'url':url,'final_url':final,'status':status,'content_type':ctype,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'local_path':str(root/name),'seconds':time.monotonic()-t,'PIT':'NOT_ESTABLISHED_BY_CURRENT_FETCH'}
 except Exception as e:return {'name':name,'url':url,'error':type(e).__name__+': '+str(e),'seconds':time.monotonic()-t,'PIT':'NOT_VERIFIED'}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(probe,urls))
p=pathlib.Path(__file__).parent/'results/source-probes.json';p.write_text(json.dumps(results,indent=2)+'\n');print(p.read_text())
