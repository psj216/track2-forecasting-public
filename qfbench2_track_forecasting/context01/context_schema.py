"""## Executive summary (read this first)
Fix context vocabulary and numeric feature order before any card outcome is opened.
"""
TOPICS={
 'growth':r'\bgrowth\b|\bgdp\b|recession|economic activity|expansion|slowdown',
 'inflation':r'inflation|\bcpi\b|\bpce\b|price pressure|disinflation',
 'labor':r'labou?r|employment|unemployment|payroll|wage',
 'monetary_policy':r'monetary|central bank|\bfed\b|\bfomc\b|\brba\b|\bboj\b|\becb\b|policy|taper|tighten|easing|on.hold',
 'rates':r'rate|yield|curve|bond|treasury|flattener|steepener',
 'FX':r'exchange rate|currency|currencies|\bfx\b|dollar|yen|euro|sterling',
 'equity':r'equit|stock|market return|\bmkt\b|\bhml\b|\bsmb\b',
 'liquidity':r'liquidity|funding|credit crunch|credit stress|balance.sheet|quantitative easing|\bqe\b|reserve balance',
 'capital_flow':r'capital flow|portfolio flow|inflow|outflow|net purchase',
 'positioning':r'positioning|open interest|dealer position|net long|net short|crowding',
 'valuation':r'valuation|fair value|relative.value|mispric|cheap|expensive',
 'carry':r'\bcarry\b|interest differential',
 'risk_sentiment':r'risk|stress|panic|uncertainty|uncertain|fragil|flight.to|safe.haven',
 'commodity':r'commodity|commodities|oil|gold|copper',
 'geopolitical':r'geopolit|brexit|\bwar\b|\bconflict\b|sanction',
 'earnings_corporate':r'earnings|corporate|company|apple|profit|revenue',
 'generic_none':r'(?!)'}
CONDITIONS={'explicit_scenario':r'\bif\b|assuming|given that|conditional|scenario',
 'event_conditioned':r'event|shock|crisis|covid|brexit|pandemic|panic|meeting|announcement|testimony',
 'comparison_relative_value':r'relative|compar|spread|cross.market|differential',
 'convergence_divergence':r'convergen|divergen|normaliz|decoupl',
 'ranking_order':r'rank|order|outperform|underperform',
 'joint_path_consistency':r'joint|path|trajectory|curve|cross.market|consisten'}
LANGUAGE={'directional':r'rise|rising|fall|falling|upward|downward|increase|decrease|hawk|dov|tighten|eas',
 'increase':r'rise|rising|increase|upward|higher|tighten|hawk',
 'decrease':r'fall|falling|decrease|downward|lower|easing|dov',
 'surprise':r'surpris|unexpected|shock',
 'expected_consensus':r'expect|consensus|forecast|anticipat',
 'conditional_language':r'\bif\b|assuming|given|conditional',
 'uncertainty':r'uncertain|risk|may|might|could|possib|ambigu|thin.signal',
 'explicit_date':r'\b(?:19|20)\d{2}(?:-\d{2}(?:-\d{2})?)?\b',
 'numerical_threshold':r'\b\d+(?:\.\d+)?\s*(?:%|percent|basis points|bps)|(?:above|below|exceed|at least|threshold)\s*\d'}
ENTITIES=('federal reserve','fomc','fed','rba','bank of japan','boj','ecb','bank of england','bis','imf','powell','yellen','bernanke','greenspan','draghi','lagarde','kuroda','lowe','stevens','china','apple')
EVENTS=('covid','pandemic','brexit','taper','credit crunch','jackson hole','cpi','fomc meeting','financial crisis','china panic')
STRUCTURE=['family_'+f for f in ('F1','F2','F3','F4')]+['single','multi','assets_count','horizons_count','min_horizon','max_horizon','target_level','target_return','target_other','absolute','relative','future_point','trajectory']
CONDITIONALITY=['unconditional',*CONDITIONS]
LANGUAGE_NAMES=[*LANGUAGE,'named_event_count','named_entity_count']
TEMPORAL=['immediate','short','medium','long','multi_horizon']
BASE_COLUMNS=[(n,1)for n in STRUCTURE]+[(n,2)for n in CONDITIONALITY]+[(n,3)for n in TOPICS]+[(n,4)for n in [*LANGUAGE_NAMES,*TEMPORAL]]
GROUPS=('FX','Rates','Factor/Equity')
HORIZON_BINS=('1-5','6-21','22-63','64-126','127+')
def horizon_bin(h):return HORIZON_BINS[0 if h<=5 else 1 if h<=21 else 2 if h<=63 else 3 if h<=126 else 4]
def asset_group(asset,kind):return 'Factor/Equity'if kind in ('return','log_return')else('Rates'if asset.startswith('UST_')else'FX')
def schema():
 out=[dict(name=n,stage=s)for n,s in BASE_COLUMNS]
 for v in GROUPS:
  out.extend(dict(name=n+'__group='+v,stage=5,interaction='group',value=v,base=n)for n,_ in BASE_COLUMNS)
 for v in HORIZON_BINS:
  out.extend(dict(name=n+'__horizon='+v,stage=5,interaction='horizon',value=v,base=n)for n,_ in BASE_COLUMNS)
 return out
