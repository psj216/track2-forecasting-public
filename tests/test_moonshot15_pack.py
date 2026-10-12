"""## Executive summary (read this first)
Windows-aware CLI discovery and no-secret/no-upload handoff properties.
"""

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

P = Path(__file__).parents[1] / "delivery/moonshot15/pack_five.py"
spec = importlib.util.spec_from_file_location("m15_pack", P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_windows_exe_resolves():
    with patch.object(
        m.shutil,
        "which",
        side_effect=lambda x: "C:/Tools/qfbench2.exe" if x == "qfbench2.exe" else None,
    ):
        assert m.resolve_cli() == "C:/Tools/qfbench2.exe"


def test_sibling_windows_exe(tmp_path):
    py = tmp_path / "python.exe"
    cli = tmp_path / "qfbench2.exe"
    cli.write_text("synthetic")
    with (
        patch.object(m.shutil, "which", return_value=None),
        patch.object(m.sys, "executable", str(py)),
    ):
        assert m.resolve_cli() == str(cli)


def test_missing_cli_fails_closed():
    with (
        patch.object(m.shutil, "which", return_value=None),
        patch.object(m.sys, "executable", "/nonexistent/python.exe"),
        pytest.raises(RuntimeError),
    ):
        m.resolve_cli()


def test_helper_never_reads_secret():
    s = P.read_text()
    assert "getpass" not in s and "input(" not in s and "--team-key" not in s
    assert "submission','pack" in s and "submission','alias" not in s
    assert "upload'," not in s and "http.client" not in s
