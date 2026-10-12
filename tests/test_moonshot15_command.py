"""## Executive summary (read this first)
Regression for checker-added dangling Docker env flags; numerical assertions unchanged.
"""

import pytest

from backtesting.moonshot15.runtime.command_contract import validate_docker_argv


@pytest.mark.parametrize(
    "args",
    [
        ["docker", "run", "-e", "-v", "/unit:/input:ro", "image"],
        ["docker", "run", "--env"],
        ["docker", "run", "--user", "--network", "none", "image"],
        ["docker", "run", "-v", "--read-only", "image"],
    ],
)
def test_missing_option_value_never_launches(args):
    with pytest.raises(ValueError):
        validate_docker_argv(args)


def test_complete_current_contract_args():
    validate_docker_argv(
        [
            "docker",
            "run",
            "--rm",
            "--user",
            "65534:65534",
            "-e",
            "HOME=/nonexistent",
            "-v",
            "/unit:/input:ro",
            "--read-only",
            "image",
            "forecast",
        ]
    )


def test_non_run_commands_unchanged():
    validate_docker_argv(["docker", "pull", "image@sha256:abc"])
