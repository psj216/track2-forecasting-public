"""## Executive summary (read this first)
Strict House JSON, five frozen transforms, no truth access and exact baseline fallback.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import os
import hashlib
import numpy as np
from .official_transport import _house_reply, HouseError, new_call_receipt
ROOT=Path(__file__).parent
CONFIG=json.loads((ROOT/'config.json').read_text())
PROMPTS=json.loads((ROOT/'prompts.json').read_text())
FACTORS=CONFIG['factors']
class InvalidReply(ValueError):
    """A closed-schema reply is unusable; no partial forecast adjustment is admitted."""

def number(v,low,high):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not low<=v<=high:
        raise InvalidReply('number_outside_closed_bounds')
    return float(v)
def keys(v,expected):
    if not isinstance(v,dict) or set(v)!=set(expected): raise InvalidReply('object_keys_mismatch')
def duplicate_guard(pairs):
    out={}
    for k,v in pairs:
        if k in out: raise InvalidReply('duplicate_JSON_key')
        out[k]=v
    return out
def reject_constant(v): raise InvalidReply('nonfinite_JSON')
def force_map(x):
    keys(x,FACTORS)
    for f in FACTORS:
        v=x[f];keys(v,['direction','strength','confidence','persistence'])
        for k,l,h in [('direction',-1,1),('strength',0,1),('confidence',0,1)]: number(v[k],l,h)
        p=v['persistence']
        if type(p) is not int or p not in CONFIG['persistence_bd']: raise InvalidReply('persistence_not_frozen')
def cells(x,assets,horizons):
    if not isinstance(x,list) or len(x)!=len(assets)*len(horizons): raise InvalidReply('cell_count')
    seen=set()
    for v in x:
        keys(v,['asset','horizon','direction','standardized_shift','confidence'])
        if type(v['asset']) is not str or v['asset'] not in assets or type(v['horizon']) is not int or v['horizon'] not in horizons: raise InvalidReply('unknown_cell')
        pair=(v['asset'],v['horizon'])
        if pair in seen: raise InvalidReply('duplicate_cell')
        seen.add(pair)
        if type(v['direction']) is not int or v['direction'] not in [-1,0,1]: raise InvalidReply('direction')
        number(v['standardized_shift'],0,10);number(v['confidence'],0,1)
def scenarios(x):
    if not isinstance(x,list) or not CONFIG['scenario_min']<=len(x)<=CONFIG['scenario_max']: raise InvalidReply('scenario_count')
    for v in x:
        keys(v,['probability','factors']);number(v['probability'],0,1);force_map(v['factors'])
    if sum(v['probability'] for v in x)<=0: raise InvalidReply('zero_probability')
def validate(obj,variant,assets,horizons):
    if variant in ['A','E1']:
        keys(obj,['factors']);force_map(obj['factors'])
    elif variant=='B': keys(obj,['cells']);cells(obj['cells'],assets,horizons)
    elif variant=='C': keys(obj,['scenarios']);scenarios(obj['scenarios'])
    elif variant=='D':
        keys(obj,['regimes']); rs=obj['regimes']
        if not isinstance(rs,list) or not 1<=len(rs)<=3: raise InvalidReply('regime_count')
        seen=set()
        for v in rs:
            keys(v,['name','weight','confidence','persistence'])
            if v['name'] not in CONFIG['regimes'] or v['name'] in seen: raise InvalidReply('regime_name')
            seen.add(v['name']);number(v['weight'],0,1);number(v['confidence'],0,1)
            if type(v['persistence']) is not int or v['persistence'] not in CONFIG['persistence_bd']: raise InvalidReply('regime_persistence')
        if sum(v['weight'] for v in rs)<=0: raise InvalidReply('zero_weight')
    elif variant=='E2': keys(obj,['cells','scenarios']);cells(obj['cells'],assets,horizons);scenarios(obj['scenarios'])
    else: raise InvalidReply('variant')
    return obj
def parse(content,variant,assets,horizons):
    if not isinstance(content,str) or len(content)>100000: raise InvalidReply('response_type_size')
    obj=json.loads(content,object_pairs_hook=duplicate_guard,parse_constant=reject_constant)
    return validate(obj,variant,assets,horizons)
def request(variant,context,receipt=None):
    receipt=new_call_receipt() if receipt is None else receipt
    endpoint=os.environ.get('MODEL_ENDPOINT','')
    model=os.environ.get('MODEL_NAME','')
    token=os.environ.get('MODEL_TOKEN','')
    try:
        if not endpoint: raise HouseError('endpoint_missing')
        if not model: raise HouseError('model_name_missing')
        if not token: raise HouseError('token_missing')
        body=json.dumps({'model':model,'temperature':CONFIG['temperature'],'max_tokens':CONFIG['max_tokens'],'chat_template_kwargs':{'enable_thinking':False},'messages':[{'role':'user','content':PROMPTS[variant]+'\nCONTEXT_JSON\n'+json.dumps(context,sort_keys=True,allow_nan=False)}]},allow_nan=False).encode()
        payload=_house_reply(endpoint,token,body,receipt)
        try:
            choice=payload['choices'][0]
            content=choice['message']['content']
            finish=choice.get('finish_reason')
        except (KeyError,IndexError,TypeError,AttributeError):
            raise HouseError('malformed_response') from None
        if finish not in ['stop',None]: raise HouseError('response_incomplete')
        try:
            parsed=parse(content,variant,context['card']['assets'],context['card']['horizons'])
        except json.JSONDecodeError:
            category='code_fenced_json' if isinstance(content,str) and content.lstrip().startswith('```') else 'malformed_model_content'
            raise HouseError(category) from None
        except InvalidReply as exc:
            category='duplicate_model_json_keys' if str(exc)=='duplicate_JSON_key' else 'schema_rejection'
            raise HouseError(category) from None
        except (TypeError,KeyError):
            raise HouseError('schema_rejection') from None
        receipt['response_validated']=True
        return parsed
    except HouseError as exc:
        receipt['failure_category']=exc.category
        raise

def loading(asset):
    table=CONFIG['loadings']
    if asset.startswith('UST_'): return np.array(table['RATE'])
    if asset in ['EUR','GBP','AUD','NZD']: return np.array(table['USD_PER_FOREIGN'])
    if asset in ['JPY','CHF','CAD','SEK','NOK','DKK','CNY','INR','BRL']: return np.array(table['FOREIGN_PER_USD'])
    for tag in ['CPI','PCE','NFP','UNRATE']:
        if tag in asset.upper(): return np.array(table[tag])
    return np.array(table.get(asset,[0]*len(FACTORS)),dtype=float)
def factor_shifts(fm,assets,horizons,cap):
    out=np.zeros((len(assets),len(horizons)))
    for i,a in enumerate(assets):
        load=loading(a);den=max(1.,sum(abs(load)))
        for j,h in enumerate(horizons):
            force=np.array([fm[f]['direction']*fm[f]['strength']*fm[f]['confidence']*math.exp(-h/fm[f]['persistence']) for f in FACTORS])
            out[i,j]=np.clip(cap*np.dot(load,force)/den,-cap,cap)
    return out
def direct_shifts(cs,assets,horizons,cap):
    out=np.zeros((len(assets),len(horizons)));confidence=np.zeros_like(out)
    for v in cs:
        i,j=assets.index(v['asset']),horizons.index(v['horizon'])
        out[i,j]=np.clip(v['direction']*v['standardized_shift'],-cap,cap)*v['confidence']
        confidence[i,j]=v['confidence']
    return out,confidence
def scenario_shifts(ss,assets,horizons,n,cap):
    probabilities=np.array([s['probability'] for s in ss],dtype=float);probabilities/=probabilities.sum()
    # Stratified deterministic assignment gives one coherent scenario label to each joint draw.
    u=(np.arange(n)+.5)/n
    labels=np.minimum(np.searchsorted(np.cumsum(probabilities),u,side='right'),len(ss)-1)
    labels=labels[np.random.default_rng(CONFIG['seed']).permutation(n)]
    shift=np.array([factor_shifts(s['factors'],assets,horizons,cap) for s in ss])
    return shift[labels],labels

def transform(base,variant,reply,assets,horizons):
    if not isinstance(base,np.ndarray) or not np.isfinite(base).all(): raise InvalidReply('baseline_invalid')
    cap=CONFIG['variants'][variant]['location_cap_sd'];sd=np.std(base,axis=0,ddof=0)
    n=len(base);labels=None
    if variant=='A': shift=factor_shifts(reply['factors'],assets,horizons,cap)[None,:,:]
    elif variant=='B': shift=direct_shifts(reply['cells'],assets,horizons,cap)[0][None,:,:]
    elif variant=='C': shift,labels=scenario_shifts(reply['scenarios'],assets,horizons,n,cap)
    elif variant=='D':
        shift=np.zeros_like(sd)
        total=sum(v['weight'] for v in reply['regimes'])
        for v in reply['regimes']:
            fm={f:{'direction':CONFIG['regimes'][v['name']][k],'strength':1,'confidence':v['confidence'],'persistence':v['persistence']} for k,f in enumerate(FACTORS)}
            shift+=v['weight']/total*factor_shifts(fm,assets,horizons,cap)
        shift=shift[None,:,:]
    elif variant=='E':
        direct,confidence=direct_shifts(reply['cells'],assets,horizons,cap)
        scen,labels=scenario_shifts(reply['scenarios'],assets,horizons,n,cap)
        agree=np.sign(direct)[None,:,:]==np.sign(scen)
        gate=np.where((confidence[None,:,:]>=CONFIG['hybrid_confidence_gate']) & agree,1.,.25)
        shift=(CONFIG['hybrid_direct_weight']*direct[None,:,:]+CONFIG['hybrid_scenario_weight']*scen)*gate
    else: raise InvalidReply('variant')
    shift=np.clip(shift,-cap,cap)
    adjusted=base+shift*sd[None,:,:]
    if not np.isfinite(adjusted).all(): raise InvalidReply('nonfinite_transform')
    return adjusted,{'max_absolute_shift_sd':float(np.max(abs(shift))),'mean_absolute_shift_sd':float(np.mean(abs(shift))),'location_cap_sd':cap,'joint_scenario_labels_SHA256':hashlib.sha256(labels.tobytes()).hexdigest() if labels is not None else None,'scenario_labels_reused_all_cells':labels is not None,'scale_fitted':False}
