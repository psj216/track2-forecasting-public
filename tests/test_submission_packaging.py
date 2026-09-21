"""## Executive summary (read this first)

Validate our Development draft with the official packer and synthetic team data.
No test archive is a real submission. Do not upload pytest temporary artifacts.
"""

import hashlib
import json
import zipfile

import pytest
from qfbench2_common.contracts.descriptor import SubmissionDescriptor
from qfbench2_common.contracts.errors import ContractError
from qfbench2_common.team_claim import pack_submission

from scripts.prepare_dev_descriptor import HOUSE_MODEL, prepare_descriptor


def test_official_pack_has_two_members_and_no_key(tmp_path):
    body = prepare_descriptor("docker.io", "synthetic-team/test-image", "sha256:" + "a" * 64)
    assert "team_id" not in body
    assert "descriptor_digest" not in body
    archive_path = tmp_path / "synthetic-only.zip"
    synthetic_key = "synthetic-packaging-test-key"
    pack_submission(body, 42, synthetic_key, archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        assert sorted(archive.namelist()) == ["submission.json", "team-claim.json"]
        raw = archive.read("submission.json")
        claim_raw = archive.read("team-claim.json")
        assert synthetic_key.encode() not in raw + claim_raw
        descriptor = SubmissionDescriptor.from_mapping(json.loads(raw))
        assert descriptor.competition_id == "agenthon2026-forecasting-dev"
        assert descriptor.phase == "dev"
        assert descriptor.category == "api"
        assert descriptor.models[0].to_mapping() == HOUSE_MODEL
        claim = json.loads(claim_raw)
        assert claim["schema_version"] == "2.0"
        assert claim["descriptor_sha256"] == hashlib.sha256(raw).hexdigest()
        assert set(claim) == {"schema_version", "site_team_id", "descriptor_sha256", "proof"}


@pytest.mark.parametrize("digest", ["latest", "sha256:abc", "sha256:" + "A" * 64])
def test_draft_refuses_tags_and_bad_digests(digest):
    with pytest.raises(ContractError):
        prepare_descriptor("docker.io", "synthetic-team/test-image", digest)
