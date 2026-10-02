"""## Executive summary (read this first)

Enforce distinct information classes, units, dates and first releases.
"""
import pandas as pd

CLASS_A="TRUE_CONSENSUS"
CLASS_B="MARKET_IMPLIED"
FAMILIES=("RGDP","CPI","UNEMP","TBILL","TBOND")
WINDOWS=(1,5,21)

def validate_snapshot(snapshot):
    if snapshot["snapshot_kind"] != "actual_survey_median":
        raise ValueError("Not an actual survey snapshot")
    pd.Timestamp(snapshot["publication_date"])
    if not pd.notna(snapshot["value"]):
        raise ValueError("Missing actual expectation")

def validate_actual(actual):
    if actual["vintage"] != "first":
        raise ValueError("Revised actual rejected")
    if not actual.get("document_sha256"):
        raise ValueError("First-release provenance absent")

def separate_classes(records, info_class):
    if any(r["class"] != info_class for r in records):
        raise ValueError("Information classes cannot be pooled")
    return records
