"""Executive summary: fixed-sign nulls from immutable forecasts, no source or direction fitting."""
import numpy as np
import pandas as pd
from .core import SEED, CONTROLS, direction

class ControlPlan:
    def __init__(self, rows, states, cutoffs):
        self.rows = rows.reset_index(drop=True)
        self.signs = direction(rows.predicted_delta)
        self.releases = sorted(rows.release_id.unique())
        self.packets = {}
        signatures = {}
        for release, g in self.rows.groupby('release_id', sort=True):
            signature = tuple(sorted(set(zip(g.asset, g.horizon))))
            signatures.setdefault(signature, []).append(release)
            for (asset, horizon), t in g.groupby(['asset','horizon'], sort=True):
                self.packets[(release, asset, int(horizon))] = t.sort_values(['origin_date']).index.to_numpy()
        self.strata = list(signatures.values())
        self.states = sorted([s for s in states if s.get('panel')=='SPD'], key=lambda s:s['available_at'])
        self.available = np.array([pd.Timestamp(s['available_at']).value for s in self.states], dtype=np.int64)
        self.cutoffs = np.array([pd.Timestamp(c).value for c in cutoffs], dtype=np.int64)
        self.origin_ns = pd.to_datetime(self.rows.origin_date).to_numpy(dtype='datetime64[ns]').astype(np.int64)
        self.origin_cutoff_dates = np.array([str(pd.Timestamp(c).date()) for c in cutoffs], dtype='datetime64[D]')
        self.days_public = np.array([s['publication_date'] for s in self.states], dtype='datetime64[D]')
        self.valid_states = np.array([s['full5_usable_at_release'] for s in self.states])
        self.asset = self.rows.asset.to_numpy(); self.horizon = self.rows.horizon.to_numpy(); self.age = self.rows.source_age.to_numpy()
        self.recipient_indices = {release:np.flatnonzero(self.rows.release_id.eq(release)) for release in self.releases}
        # Recipient metadata-only matching indices are precomputed once; no truth/loss enters.
        self.donor_indices = {}
        for group in self.strata:
            for recipient in group:
                ii=self.recipient_indices[recipient]
                for donor in group:
                    mapped=[]
                    for j in ii:
                        options=self.packets[(donor,self.asset[j],int(self.horizon[j]))]
                        nearest=np.argmin(abs(self.age[options]-self.age[j]))
                        mapped.append(options[nearest])
                    self.donor_indices[(recipient,donor)] = np.asarray(mapped,int)
    def shuffled_release(self, rng):
        out = np.empty_like(self.signs)
        for group in self.strata:
            shuffled = rng.permutation(group)
            for recipient, donor in zip(group, shuffled):
                ii = self.recipient_indices[recipient]
                out[ii] = self.signs[self.donor_indices[(recipient,donor)]]
        return out
    def delayed_dates(self, rng):
        # Delay magnitudes are fixed; permute them, never backdate the source.
        delays=rng.permutation(np.resize(np.arange(21),len(self.states)))
        delayed=np.array([(pd.Timestamp(s['available_at'])+pd.offsets.BDay(int(delay))).value for s,delay in zip(self.states,delays)],dtype=np.int64)
        out=np.zeros(len(self.rows)); count=0
        for j in range(len(self.rows)):
            eligible=np.flatnonzero(delayed<=self.cutoffs[j])
            if not len(eligible):continue
            k=eligible[np.argmax(delayed[eligible])]
            state=self.states[k]
            age=int(np.busday_count(self.days_public[k],self.origin_cutoff_dates[j]))
            if not self.valid_states[k] or age>70:continue
            options=self.packets.get((state['release_id'],self.asset[j],int(self.horizon[j])),np.array([],int))
            options=options[self.origin_ns[options]<=self.origin_ns[j]]
            if len(options):out[j]=self.signs[options[-1]];count+=1
        return out, count
    def random_sign(self, rng):
        return rng.permutation(self.signs)
    def sample(self, kind, replicate):
        seed=SEED+100000*(CONTROLS.index(kind)+1)+replicate
        rng=np.random.default_rng(seed)
        if kind=='RELEASE_SIGN_SHUFFLE':return self.shuffled_release(rng),len(self.rows)
        if kind=='DATE_PERMUTED_DIRECTION':return self.delayed_dates(rng)
        if kind=='RANDOM_SIGN':return self.random_sign(rng),len(self.rows)
        raise ValueError('Unknown control')
    def prior_year(self):
        out=np.zeros(len(self.rows)); matched=[]
        for j,row in self.rows.iterrows():
            query=pd.Timestamp(row.origin_date)-pd.DateOffset(years=1)
            options=np.flatnonzero((self.asset==row.asset)&(self.horizon==row.horizon)&(self.origin_ns<=query.value))
            if len(options):
                k=options[np.argmax(self.origin_ns[options])]
                lag=int(np.busday_count(np.datetime64(str(pd.Timestamp(self.rows.iloc[k].origin_date).date())),np.datetime64(str(query.date()))))
                if lag<=40:out[j]=self.signs[k];matched.append(j)
        return out,np.asarray(matched,int)

def losses_for_sign(loss_table, signs):
    signs=np.asarray(signs)
    if not np.isin(signs,[-1,0,1]).all():raise ValueError('Null is not a sign vector')
    return np.asarray(loss_table)[signs.astype(int)+1,np.arange(len(signs))]

def sample_blocks(groups, rng):
    keys, ids=np.unique(np.asarray(groups).astype(str),return_inverse=True)
    counts=np.bincount(rng.integers(len(keys),size=len(keys)),minlength=len(keys))
    return counts[ids].astype(float),counts,ids
