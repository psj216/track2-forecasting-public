"""## Executive summary (read this first)
Only direct flow mappings and predeclared global macro liquidity enter primary features.
"""
FLOW_ASSET='MKT'
LIQUIDITY_ASSETS=('AUD','BRL','CAD','CHF','CNY','DKK','EUR','GBP','INR','JPY','NOK','NZD','SEK','BAB','HML','MKT','MOM','QMJ','SMB','UST_2Y','UST_5Y','UST_7Y','UST_10Y','UST_20Y','UST_30Y')
def admitted(confidence,source_class,global_macro=False):
    return confidence=='DIRECT' or (source_class=='L' and global_macro and confidence=='GLOBAL_MACRO')
