"""Executive summary: fail closed on image identity or environment failures without changing forecasting logic."""
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from backtesting.v51_safe_delivery09 import image_recovery as recovery


def mock_docker(monkeypatch, **changes):
    image = {"RepoDigests": [recovery.IMAGE], "Architecture": "amd64", "Os": "linux",
             "Id": "sha256:" + "1" * 64, "Created": "2026-09-25T00:00:00Z", "RootFS": {"Layers": []},
             "Config": {"Env": ["FORECAST_MODE=text-first-v5.1", "TOKEN=private-value"], "User": "runner"}}
    image.update(changes)
    monkeypatch.setattr(recovery.shutil, "which", lambda _: "/usr/bin/docker")
    monkeypatch.setattr(recovery.subprocess, "run", lambda argv, **kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""))
    monkeypatch.setattr(recovery.subprocess, "check_output", lambda argv, **kwargs: json.dumps([image]))


def test_exact_frozen_identity():
    assert recovery.DIGEST == "sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874"
    assert recovery.SOURCE == "47194f28d5188b87cdca1d591d86b9eeda86f7cf"


def test_missing_engine_is_not_image_not_found(monkeypatch, tmp_path):
    monkeypatch.setattr(recovery.shutil, "which", lambda _: None)
    assert recovery.recover(tmp_path) == 1
    d = json.loads((tmp_path / "recovered_image_manifest.json").read_text())
    assert d["status"] == "DOCKER_EXECUTABLE_UNAVAILABLE" and not d["EXACT_PREPARATION_IMAGE_RECOVERED"]


def test_exact_pull_and_no_secret_export(monkeypatch, tmp_path):
    mock_docker(monkeypatch)
    assert recovery.recover(tmp_path) == 0
    text = (tmp_path / "recovered_image_manifest.json").read_text()
    assert "private-value" not in text
    d = json.loads(text)
    assert d["historical_official_identity"] is False
    assert d["forecast_runs"] == d["scores_computed"] == d["submissions"] == 0


@pytest.mark.parametrize("changes", [{"RepoDigests": ["repo@sha256:" + "2" * 64]}, {"Architecture": "arm64"}])
def test_identity_mismatch_fails_closed(monkeypatch, tmp_path, changes):
    mock_docker(monkeypatch, **changes)
    assert recovery.recover(tmp_path) == 1
    assert not json.loads((tmp_path / "recovered_image_manifest.json").read_text())["EXACT_PREPARATION_IMAGE_RECOVERED"]


def test_no_forecast_source_changed():
    root = Path(__file__).resolve().parents[1]
    lineage = json.loads((root / "backtesting/v51_safe_delivery09/results/lineage_manifest.json").read_text())
    assert lineage["scientific_parent_RESULT_SHA"] == "6903eb83c7c84c5c6dc581c1c76820a24bbc89e6"
    assert lineage["parent_reopened"] is False
