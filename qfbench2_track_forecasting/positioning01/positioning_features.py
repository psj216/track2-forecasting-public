"""## Executive summary (read this first)
Keep native positioning categories separate; actual positioning is source-gated off.
"""
from .normalization import shares,past_z
def report_features(reports,index):
    r=reports[index];net,gross=shares(r['long'],r['short'],r['oi'])
    history=[shares(x['long'],x['short'],x['oi'])[0] for x in reports[:index+1]]
    return dict(net_share=net,gross_share=gross,change1=net-history[index-1] if index>=1 else None,change4=net-history[index-4] if index>=4 else None,change13=net-history[index-13] if index>=13 else None,z=past_z(history,index))
