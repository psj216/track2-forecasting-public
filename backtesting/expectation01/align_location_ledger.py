"""## Executive summary (read this first)

Hash-check preserved targets and baseline losses before any reuse.
"""
import hashlib,json
import numpy as np
import pandas as pd
from pathlib import Path

INPUT_HASHES={"ledger.parquet":"5a421fa5c10745c69469c683797bf42f4abf54288e8082984bcf39fda76968a6","features.npy":"bfd4a3bbe34e4237575e0bbfd801ae8151fb611ac8b7b678f2762c816fdd9665","predictions.npz":"135ef536f2378211a1ec5187ee8eae784f73ee86481ebe193acd2acc0b0e1c62","losses.npz":"d71b2fa7f60cd3f288df5776e4602af255353a1cbb254a89d5e7994977ab4c39","transfer_models.pkl":"a2c882a669b9a00ea8427d409faea0f0b112f4882d97b82dab370a4d7164efdc"}

def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        while block:=f.read(1024*1024):h.update(block)
    return h.hexdigest()

def verify(private):
    actual={n:digest(private/n) for n in INPUT_HASHES}
    if actual!=INPUT_HASHES:raise ValueError("Frozen LOCATION artifact hash mismatch; STOP")
    return actual

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({"executive_summary":"Frozen research audit; raw per-cell data stay private.",**value},indent=2,allow_nan=False)+"\n")
