"""Executive summary: immutable SPD sign -> fixed small pure translations, without refitting."""
import datetime, hashlib, json
from pathlib import Path
import numpy as np
from backtesting.information_failure01.common import clean, group_weights, direction_metrics

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'backtesting/direction_to_location01/results'
PARENT = 'fe62b9058ea6dc540f7548c6be96ccc4e8d04b92'
LOCATION04_RESULT = 'ca9b467d48b2fc145faa5bfe549975206c8a811f'
PRIMARY = 'DTL_PRIMARY_010'
PRIMARY_AMPLITUDE = .10
SECONDARY = {'DTL_005': .05, 'DTL_020': .20}
OOD_THRESHOLD = 3.
ASSETS = ('UST_2Y', 'UST_5Y')
HORIZONS = (5, 21, 63, 126, 189)
YEARS = (2020, 2021, 2022, 2023, 2024)
SEED = 2026100602
CONTROL_REPLICATES = 2000
BOOTSTRAP_REPLICATES = 5000
CONTROLS = ('RELEASE_SIGN_SHUFFLE', 'DATE_PERMUTED_DIRECTION', 'RANDOM_SIGN')

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def array_hash(a):
    return hashlib.sha256(np.ascontiguousarray(a, dtype=np.float64).tobytes()).hexdigest()

def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if 'executive_summary' not in data:
        data = {'executive_summary': 'Exposed frozen-direction location translation; no independent OOS or automatic submission.', **data}
    path.write_text(json.dumps(clean(data), indent=2, allow_nan=False) + '\n')

def status(stage, artifact='', **kw):
    path = ROOT / 'backtesting/direction_to_location01/STATUS.json'
    data = json.loads(path.read_text())
    data.update(current_stage=stage, last_successful_artifact=artifact, last_update=datetime.datetime.now(datetime.timezone.utc).isoformat(), **kw)
    data['stages'][stage] = 'complete'
    if stage not in data['completed_stages']:
        data['completed_stages'].append(stage)
    data['pending_stages'] = [x for x in data['pending_stages'] if x != stage]
    save(path, data)

def direction(prediction):
    prediction = np.asarray(prediction, float)
    if not np.isfinite(prediction).all():
        raise ValueError('Nonfinite frozen prediction')
    return np.sign(prediction)

def shift_vector(prediction, sd, amplitude=PRIMARY_AMPLITUDE, max_train_z=None):
    """This constructor has no outcome or future-source input."""
    sd = np.asarray(sd, float)
    sign = direction(prediction)
    if sign.shape != sd.shape or not np.isfinite(sd).all() or not (sd > 0).all():
        raise ValueError('Frozen baseline SD invalid')
    shift = sign * float(amplitude) * sd
    if max_train_z is not None:
        z = np.asarray(max_train_z, float)
        if z.shape != sd.shape or not np.isfinite(z).all():
            raise ValueError('Missing preserved TRAIN scaler diagnostic')
        shift = np.where(z > OOD_THRESHOLD, 0., shift)
    return shift

def translate(draws, shifts):
    return np.asarray(draws, float) + np.asarray(shifts, float)

def verify_inputs(private):
    p = Path(private)
    m = json.loads((p / 'input_hash_manifest.json').read_text())
    for name, sha in m['files'].items():
        if digest(p / name) != sha:
            raise ValueError('Immutable input changed: ' + name)
    return m

def verify_pre(private):
    p = Path(private)
    r = json.loads((p / 'PRE-receipt.json').read_text())
    if not r['remote_verified']:
        raise ValueError('Remote PRE verification required before any candidate CRPS')
    for name, sha in r['frozen_implementation_hashes'].items():
        if digest(ROOT / name) != sha:
            raise ValueError('Frozen implementation changed: ' + name)
    verify_inputs(p)
    return r['PRE_RESULT_DTL01_SHA']

def score_summary(rows, base, loss, oracle, shift, balance='cell'):
    w = np.ones(len(rows)) if balance == 'cell' else group_weights(rows.release_id)
    denominator = np.dot(w, base)
    ratio = float(np.dot(w, loss) / denominator)
    oracle_ratio = float(np.dot(w, oracle) / denominator)
    return dict(cells=len(rows), origins=int(rows.origin_date.nunique()), releases=int(rows.release_id.nunique()), balance=balance,
                crps_ratio=ratio, oracle_ratio=oracle_ratio, oracle_capture=(1-ratio)/(1-oracle_ratio),
                score_delta_ratio=ratio-1, mean_normalized_CRPS_delta=float(np.dot(w, loss-base)/w.sum()),
                normalized_total_score_delta=float(np.dot(w, loss-base)),
                mean_abs_raw_location_shift=float(np.dot(w, abs(shift))/w.sum()),
                mean_raw_location_shift=float(np.dot(w, shift)/w.sum()),
                mean_abs_standardized_shift=float(np.dot(w, abs(shift)/rows['V5.1_SD'].to_numpy())/w.sum()),
                shifted_fraction=float(np.dot(w, shift!=0)/w.sum()),
                frozen_source_direction=direction_metrics(rows.true_delta, rows.predicted_delta, w))
