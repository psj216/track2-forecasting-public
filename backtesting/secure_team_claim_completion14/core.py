"""Executive summary: use official contracts; never read participant secrets."""
import hashlib
import json
import re
import zipfile
from pathlib import Path

PARENT = "c4f29969dfa3ca3a8993e7f44f58cd0cc61aa6a8"
DELIVERY_PARENT = "6d59afdfd75c72947b1341ee6028f62672e15700"
TOOLKIT = "bd01548e34d21fd660d88fd06157078fb25ece4e"
SOURCE = "47194f28d5188b87cdca1d591d86b9eeda86f7cf"
IMAGE_DIGEST = "sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874"
IMAGE_ID = "sha256:1d6835db45dec0dd419b135441540b9e27e1b1218f37c051f1e13a0c2072eb74"
IMAGE = {"registry":"docker.io", "repository":"jotj216/track2-f4-approved", "digest":IMAGE_DIGEST}
IMAGE_REF = "docker.io/jotj216/track2-f4-approved@" + IMAGE_DIGEST
IDENTITY_FIELDS = {"team_id", "descriptor_digest"}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def make_draft(fixture):
    result = {k:v for k,v in fixture.items() if k not in IDENTITY_FIELDS}
    result.update(schema_version="1.1.0", image=IMAGE.copy(), models=[], license="MIT")
    return result


def validate_draft(draft, schema):
    from jsonschema import Draft202012Validator
    assert not IDENTITY_FIELDS.intersection(draft), "Do not invent team identity"
    partial = {**schema, "required":[k for k in schema["required"] if k not in IDENTITY_FIELDS]}
    Draft202012Validator(partial).validate(draft)
    assert draft["image"] == IMAGE
    assert draft["competition_id"] == "agenthon2026-forecasting-final"
    assert draft["track"] == "forecasting" and draft["phase"] == "final"
    assert draft["schema_version"] == "1.1.0" and draft["models"] == []
    assert draft["license"] == "MIT"
    return "KNOWN_FIELDS_PASS_FINAL_IDENTITY_PENDING"


def verify_zip(path, team_number, expected_alias):
    """Validate bytes and official descriptor; HMAC generation stays in official CLI."""
    from qfbench2_common.contracts.descriptor import SubmissionDescriptor
    path=Path(path)
    with zipfile.ZipFile(path) as z:
        assert z.namelist()==["submission.json", "team-claim.json"]
        assert z.testzip() is None
        assert all(i.file_size<100000 and not i.is_dir() for i in z.infolist())
        raw=z.read("submission.json"); claim_raw=z.read("team-claim.json")
    descriptor=json.loads(raw); claim=json.loads(claim_raw)
    SubmissionDescriptor.from_mapping(descriptor)
    assert descriptor["team_id"]==expected_alias
    assert re.fullmatch(r"team-[0-9a-f]{32}",expected_alias)
    assert descriptor["image"]==IMAGE and descriptor["models"]==[]
    assert descriptor["license"]=="MIT" and descriptor["phase"]=="final"
    assert descriptor["track"]=="forecasting" and descriptor["schema_version"]=="1.1.0"
    assert set(claim)=={"schema_version","site_team_id","descriptor_sha256","proof"}
    assert claim["schema_version"]=="2.0" and claim["site_team_id"]==team_number
    assert claim["descriptor_sha256"]==sha256(raw)
    assert re.fullmatch(r"[0-9a-f]{64}",claim["proof"])
    # Only allow the published descriptor and claim fields; no arbitrary sidecars or paths.
    assert all(x not in raw.decode().lower() for x in ("/workspace/", "team_key", "password", "token", ".env"))
    return {"filename":path.name,"sha256":sha256(path.read_bytes()),"size":path.stat().st_size,
            "crc":"PASS","members":["submission.json","team-claim.json"],
            "descriptor_parser":"PASS","image_exact":True,"claim_byte_binding":"PASS",
            "claim_cryptographic_verification":"NOT_INDEPENDENTLY_VERIFIED_WITHOUT_KEY",
            "secret_structure_scan":"PASS","uploads":0,"submissions":0}
