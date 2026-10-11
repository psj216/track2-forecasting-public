"""Executive summary: keep participant identity private and the image immutable."""
import json
from pathlib import Path
import pytest
from backtesting.secure_team_claim_completion14.core import *
from qfbench2_common.contracts import CONTRACT_SET

SCHEMA={"type":"object","additionalProperties":False,"required":["team_id","descriptor_digest","image","track","phase","competition_id","schema_version","models","license"],"properties":{k:{} for k in ["team_id","descriptor_digest","image","track","phase","competition_id","schema_version","models","license"]}}
def fixture():
 return {"team_id":"example","descriptor_digest":"unused","image":{},"track":"forecasting","phase":"final","competition_id":"agenthon2026-forecasting-final","schema_version":"1.0.0","models":[{}],"license":"Apache-2.0"}
def test_exact_frozen_identities():
 assert PARENT=="c4f29969dfa3ca3a8993e7f44f58cd0cc61aa6a8" and TOOLKIT=="bd01548e34d21fd660d88fd06157078fb25ece4e"
 assert IMAGE_REF.endswith(IMAGE_DIGEST) and SOURCE=="47194f28d5188b87cdca1d591d86b9eeda86f7cf"
def test_no_example_participant_identity():
 d=make_draft(fixture());assert not IDENTITY_FIELDS.intersection(d)
 assert validate_draft(d,SCHEMA)=="KNOWN_FIELDS_PASS_FINAL_IDENTITY_PENDING"
def test_no_extra_fields():
 d=make_draft(fixture());d["unexpected"]="bad"
 with pytest.raises(Exception):validate_draft(d,SCHEMA)
def test_identity_in_draft_refused():
 d=make_draft(fixture());d["team_id"]="invented"
 with pytest.raises(AssertionError):validate_draft(d,SCHEMA)
def test_tag_only_image_refused():
 d=make_draft(fixture());d["image"]["digest"]="latest"
 with pytest.raises(AssertionError):validate_draft(d,SCHEMA)
def test_no_model_rebuild_or_upload():
 text=(Path(__file__).parents[1]/"backtesting/secure_team_claim_completion14/core.py").read_text()
 assert "getpass" not in text and "subprocess" not in text and "docker build" not in text

@pytest.mark.skipif(CONTRACT_SET != "1.1.0", reason="Official2.6 packaging tests run in the dedicated Python3.13 environment")
def test_official_synthetic_pack_and_receipt(tmp_path):
 from qfbench2_common.team_claim import pack_submission
 # Synthetic contract fixture only: never a participant key.
 draft=make_draft(fixture());draft.update(interface_version="2.0",category="api",image_access="public")
 target=tmp_path/"synthetic.zip"
 alias=pack_submission(draft,999999,"synthetic-contract-test-key-only",target)
 result=verify_zip(target,999999,alias)
 assert result["crc"]=="PASS" and result["claim_byte_binding"]=="PASS"

@pytest.mark.skipif(CONTRACT_SET != "1.1.0", reason="Official2.6 packaging tests run in the dedicated Python3.13 environment")
def test_extra_zip_member_refused(tmp_path):
 import zipfile
 from qfbench2_common.team_claim import pack_submission
 draft=make_draft(fixture());draft.update(interface_version="2.0",category="api",image_access="public")
 target=tmp_path/"synthetic.zip";alias=pack_submission(draft,999999,"synthetic-contract-test-key-only",target)
 with zipfile.ZipFile(target,"a") as z:z.writestr("unexpected.txt","x")
 with pytest.raises(AssertionError):verify_zip(target,999999,alias)
