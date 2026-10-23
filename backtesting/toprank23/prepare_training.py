"""Executive summary: isolate pre2024 ECB training prices; write outside repository."""
import sys
from prepare_ecb import load,GROUPS
f=load(sys.argv[1]).loc[:'2023-12-31'];assets=sum(GROUPS.values(),[])
f[assets].div(f.USD,axis=0).to_parquet(sys.argv[2])
