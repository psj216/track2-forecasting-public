"""Executive summary: source-only OCR assistance for original PDF font mapping failures."""
from pathlib import Path
import argparse,re,subprocess,os,json,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from PIL import Image
import numpy as np
from .acquire import save,status
def prepare(private,rid,page):
 folder=private/'ocr'/rid;folder.mkdir(parents=True,exist_ok=True);base=folder/f'page-{page}';tsv=base.with_suffix('.tsv');receipt=folder/'receipt.json'
 if tsv.exists() and receipt.exists():return json.loads(receipt.read_text())
 subprocess.run(['pdftoppm','-f',str(page),'-l',str(page),'-r','220','-singlefile','-png',str(private/'source'/rid/'results.pdf'),str(base)],check=True,timeout=40)
 arr=np.array(Image.open(base.with_suffix('.png')).convert('RGB'));blue=(arr[:,:,2].astype(int)-arr[:,:,0].astype(int)>25)&(arr[:,:,1].astype(int)-arr[:,:,0].astype(int)>10);bands=blue.mean(axis=1)>.40
 for y in np.flatnonzero(bands):
  xx=np.flatnonzero(blue[y]);lo,hi=int(xx.min()),int(xx.max())+1;gray=arr[y,lo:hi].mean(axis=1);white=np.where(gray>230,0,255).astype('uint8');arr[y,lo:hi]=white[:,None]
 processed=folder/f'page-{page}-headers-readable.png';Image.fromarray(arr).save(processed)
 env=dict(os.environ,OMP_THREAD_LIMIT='1');subprocess.run(['tesseract',str(processed),str(base),'--psm','6','txt','tsv'],check=True,timeout=50,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 d={'survey_id':rid,'page':page,'method':'Original PDF raster220dpi; invert high-coverage blue header bands for OCR readability; numeric data not edited','original_pdf':'source/'+rid+'/results.pdf','original_image':str(base.with_suffix('.png').relative_to(private)),'derived_image':str(processed.relative_to(private)),'OCR_tsv':str(tsv.relative_to(private)),'tesseract_version':subprocess.check_output(['tesseract','--version'],text=True).splitlines()[0]};save(receipt,d);return d
def main(private):
 tasks=[]
 for p in sorted((private/'source').glob('20*-*/results.txt')):
  s=p.read_text();m=re.search(r'most likely outcome[^\n]+mode',s,re.I)
  if not m:continue
  block=s[m.start():m.start()+1400]
  if 'midpoint' in block and not re.search(r'Median[^\n]+\d+\.\d+%',block):tasks.append((p.parent.name,s[:m.start()].count('\f')+1))
 start=time.monotonic();out=[]
 with ThreadPoolExecutor(max_workers=3) as pool:
  fs={pool.submit(prepare,private,rid,page):(rid,page) for rid,page in tasks}
  for i,f in enumerate(as_completed(fs),1):
   out.append(f.result());save(private/'OCR-receipts.json',out);status('questionnaire_field_harmonization',OCR_completed=i,OCR_total=len(tasks));print(f'OCR {i}/{len(tasks)} current={fs[f]} elapsed={time.monotonic()-start:.1f}s output=ocr/{fs[f][0]}',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--private',type=Path,required=True);a=p.parse_args();main(a.private)
