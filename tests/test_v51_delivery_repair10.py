"""Executive summary: preserve exact delivery identity and reject unobserved runtime readiness."""

from pathlib import Path
import json
import tomllib
import qfbench2_common
from backtesting.v51_delivery_repair10 import audit

ROOT = Path(__file__).resolve().parents[1]


def test_exact_candidate_identity():
    from backtesting.v51_safe_delivery09 import image_recovery
    assert audit.IMAGE == image_recovery.IMAGE
    assert audit.SOURCE == image_recovery.SOURCE


def test_exact_common_import_source():
    package = Path(qfbench2_common.__file__).resolve()
    common = Path('/workspace/scratch/935b41f252e9/safe09-common242/common')
    assert package.is_relative_to(common)
    assert tomllib.loads((common/'pyproject.toml').read_text())['project']['version'] == '2.4.2'


def test_missing_observations_cannot_be_ready():
    assert not audit.readiness({})
    for omitted in audit.REQUIRED_GATES:
        observations = {gate: True for gate in audit.REQUIRED_GATES if gate != omitted}
        assert not audit.readiness(observations)


def test_default_branch_registration_block():
    assert not audit.manual_registration(['.github/workflows/ci.yml'])['registration_ready']
    assert audit.manual_registration([audit.WORKFLOW])['registration_ready']


def test_preserved_manual_only_workflow():
    import yaml
    workflow = yaml.load((ROOT/audit.WORKFLOW).read_text(), Loader=yaml.BaseLoader)
    assert set(workflow['on']) == {'workflow_dispatch'}
    assert workflow['permissions'] == {'contents': 'read'}
    assert workflow['jobs']['exact-image']['runs-on'] == 'ubuntu-latest'
    assert audit.verified_blob(ROOT/audit.WORKFLOW, '297121f769d05fa20ce9dcbacba1c8e0b6ab2968')


def test_frozen_target_no_claimed_runtime_result():
    spec = json.loads((ROOT/'backtesting/v51_delivery_repair10/results/delivery_target.json').read_text())
    assert spec['image_reference'] == audit.IMAGE
    assert spec['source_SHA'] == audit.SOURCE
    assert spec['forecast_mode'] == 'text-first-v5.1'
    assert spec['common_version'] == '2.4.2'
    assert spec['required_repetitions'] == 3
    assert spec['scores_allowed'] is False
    assert spec['submission_allowed'] is False
