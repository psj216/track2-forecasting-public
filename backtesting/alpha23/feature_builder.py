"""Executive summary: observable curve states; par-yield forwards are proxies, not policy expectations."""
import numpy as np
import pandas as pd
from policy_signal import features as policy_features
ASSETS=['UST_3M','UST_6M','UST_1Y','UST_2Y','UST_5Y','UST_7Y','UST_10Y','UST_20Y','UST_30Y']
TENORS=np.array([.25,.5,1,2,5,7,10,20,30])
def build(p,docs):
 p=p.reindex(columns=ASSETS);diff=p.diff();sd=diff.rolling(60,min_periods=50).std().clip(lower=.001);parts=[]
 def add(v,name):
  v=v.copy();v.columns=[name+'_'+c for c in v.columns];parts.append(v)
 add(p,'level')
 for n in [1,5,20]:add(p.diff(n)/sd/np.sqrt(n),'move'+str(n))
 for n in [10,30,60]:add(diff.rolling(n,min_periods=n).std(),'vol'+str(n))
 add(diff.rolling(10).std()/sd,'regime');add((p-p.rolling(20).mean())/sd,'reversion')
 extras=pd.DataFrame(index=p.index)
 for name,a,b in [('s3m2y','UST_3M','UST_2Y'),('s2y10y','UST_2Y','UST_10Y'),('s5y30y','UST_5Y','UST_30Y')]:
  extras[name]=p[b]-p[a];extras[name+'_change5']=extras[name].diff(5)
 extras['curvature']=2*p.UST_5Y-p.UST_2Y-p.UST_10Y
 # Algebraic slope of maturity*par yield; not a bootstrapped zero-coupon forward.
 for i in range(8):extras['par_forward_proxy'+str(i)]=(TENORS[i+1]*p.iloc[:,i+1]-TENORS[i]*p.iloc[:,i])/(TENORS[i+1]-TENORS[i])
 extras['parallel_shock']=diff.mean(axis=1);extras['nonparallel_shock']=diff.std(axis=1);extras['dispersion']=p.std(axis=1)
 extras['corr_short_long']=diff.UST_2Y.rolling(60).corr(diff.UST_10Y)
 market=pd.concat(parts+[extras],axis=1).replace([np.inf,-np.inf],np.nan)
 pol=policy_features(p.index,docs)
 # Learned interactions, not hardcoded direction responses.
 pol['policy_recent_x_vol']=pol.policy_recent4*sd.mean(axis=1)
 pol['policy_stance_x_slope']=(pol.policy_tightening-pol.policy_easing)*extras.s2y10y
 result=pd.concat([market,pol],axis=1)
 gap=pd.Series(p.index.to_series().diff().dt.days.to_numpy()>10,index=p.index).rolling(61,min_periods=1).max().astype(bool)
 result.loc[gap]=np.nan
 return result,sd
