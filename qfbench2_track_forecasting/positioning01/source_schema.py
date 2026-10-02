"""## Executive summary (read this first)
Reject unknown vintages and bind every observation to an original release hash.
"""
from dataclasses import dataclass
import hashlib
@dataclass(frozen=True)
class Release:
    source_id:str
    release_date:str
    observation_date:str
    value:float
    raw_sha256:str
    instrument:str
    category:str='aggregate'
def original_guard(data,sha256):
    if hashlib.sha256(data).hexdigest()!=sha256:raise ValueError('Original archive changed or revised replacement')
    return True
