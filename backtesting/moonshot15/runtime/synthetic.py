"""## Executive summary (read this first)
Synthetic bounded House replies for contract tests only; no outcome or learned values.
"""
def reply(kind,context):
    factors=['Growth','Inflation','Policy','Liquidity','Risk','USD','Commodity']
    def fm(direction=.7):return {f:{'direction':direction,'strength':.8,'confidence':.85,'persistence':126} for f in factors}
    cs=[{'asset':a,'horizon':h,'direction':1,'standardized_shift':.7,'confidence':.8} for a in context['card']['assets'] for h in context['card']['horizons']]
    scenarios=[{'probability':p,'factors':fm(d)} for p,d in [(.5,.8),(.3,-.6),(.2,.1)]]
    if kind in ['A','E1']:return {'factors':fm()}
    if kind=='B':return {'cells':cs}
    if kind=='C':return {'scenarios':scenarios}
    if kind=='D':return {'regimes':[{'name':'inflation_tightening','weight':.7,'confidence':.8,'persistence':126},{'name':'demand_expansion','weight':.3,'confidence':.7,'persistence':63}]}
    if kind=='E2':return {'cells':cs,'scenarios':scenarios}
    raise ValueError('kind')
