"""## Executive summary (read this first)

Run a pre-submission activation check for F2 and F4. Mock mode exercises the
real HTTP client with a local transport stand-in; live mode uses configured
House credentials without ever printing them. Both compare against frozen V3.
Keep all forecast outputs and diagnostics outside the public repository.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import threading
import tomllib
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pandas as pd

from qfbench2_track_forecasting.cli import main as forecast

UNITS = ("t2-F2-cut-sizing-2024", "t2-F4-short-vol-2018")
ROOT = pathlib.Path(__file__).resolve().parents[1]


class StandIn(BaseHTTPRequestHandler):
    """A local wire-level response: never a proxy for Nemotron quality."""

    def log_message(self, *_args: Any) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802 — HTTP server verb
        if (
            self.path != "/v1/chat/completions"
            or self.headers.get("Authorization") != "Bearer activation-test-only"
        ):
            self.send_error(400)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size < 100_000:
                raise ValueError("request body size")
            body = json.loads(self.rfile.read(size))
            prompt = json.loads(body["messages"][1]["content"])
            doc_id = prompt["documents"][0]["doc_id"]
            family = prompt["context"]["family"]
            assets = prompt["context"]["assets"]
            if not assets or family not in {"T2-F2", "T2-F4"}:
                raise ValueError("unexpected card")
            response = {
                "regime": "policy_shift" if family == "T2-F2" else "liquidity_stress",
                "direction": 1 if family == "T2-F2" else -1,
                "confidence": 0.95,
                "evidence": [doc_id],
            }
            if len(assets) > 1:
                response["direction_asset"] = assets[0]
            wire = json.dumps(
                {
                    "choices": [
                        {"finish_reason": "stop", "message": {"content": json.dumps(response)}}
                    ]
                }
            )
            raw = wire.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        except (ValueError, KeyError, IndexError, TypeError):
            self.send_error(400)


@contextmanager
def local_house() -> Iterator[None]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), StandIn)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    old = {key: os.environ.get(key) for key in ("MODEL_ENDPOINT", "MODEL_NAME", "MODEL_TOKEN")}
    try:
        os.environ["MODEL_ENDPOINT"] = f"http://127.0.0.1:{server.server_port}"
        os.environ["MODEL_NAME"] = "wire-test-only"
        os.environ["MODEL_TOKEN"] = "activation-test-only"
        yield
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def run(
    out: pathlib.Path, mode: str, units: tuple[str, ...], docker_image: str = ""
) -> list[dict[str, Any]]:
    """Fail closed unless F2 and F4 each alter samples after every gate succeeds."""
    if out == ROOT or ROOT in out.parents:
        raise ValueError("diagnostic output must be outside the public repository")
    if mode == "live" and any(
        not os.environ.get(key) for key in ("MODEL_ENDPOINT", "MODEL_NAME", "MODEL_TOKEN")
    ):
        raise ValueError("live mode requires MODEL_ENDPOINT, MODEL_NAME and MODEL_TOKEN")
    if os.environ.get("F1_CALIBRATION_PATH") or os.environ.get("NUMERIC_VARIANT", "v3") != "v3":
        raise ValueError("activation probe requires the unchanged V3 anchor")
    if os.environ.get("TEXT_INTEGRATION", "on").lower() in {"off", "false", "0"}:
        raise ValueError("TEXT_INTEGRATION must be enabled")
    out.mkdir(parents=True, exist_ok=False)
    results: list[dict[str, Any]] = []
    for unit in units:
        card_dir = ROOT / "units" / unit
        card = tomllib.loads((card_dir / "card.toml").read_text())
        family = card["metadata"]["category"]
        if family not in {"T2-F2", "T2-F4"}:
            raise ValueError("only F2/F4 can enter this probe")
        asof = card["provenance"]["data_cutoff"]
        args = [
            "--panels",
            str(card_dir),
            "--text",
            str(card_dir / "text"),
            "--asof",
            asof,
            "--seed",
            "23",
        ]
        numeric = out / unit / "numeric" / "forecast.parquet"
        active = out / unit / "family-heads" / "forecast.parquet"
        for mode_name, output in (("numeric", numeric), ("family-heads", active)):
            os.environ["FORECAST_MODE"] = mode_name
            if docker_image:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.parent.chmod(0o777)
                command = [
                    "docker",
                    "run",
                    "--rm",
                    "--read-only",
                    "--tmpfs",
                    "/tmp",
                    "--network=host",
                    "-e",
                    "FORECAST_MODE",
                    "-e",
                    "MODEL_ENDPOINT",
                    "-e",
                    "MODEL_NAME",
                    "-e",
                    "MODEL_TOKEN",
                    "-v",
                    f"{card_dir}:/input:ro",
                    "-v",
                    f"{output.parent}:/output",
                    docker_image,
                    "forecast",
                    "--panels",
                    "/input",
                    "--text",
                    "/input/text",
                    "--asof",
                    asof,
                    "--seed",
                    "23",
                    "--out",
                    "/output/forecast.parquet",
                ]
                subprocess.run(command, check=True)
            elif forecast([*args, "--out", str(output)]) != 0:
                raise RuntimeError(f"{mode_name} forecast failed")
        meta = json.loads((active.parent / "forecast_meta.json").read_text())
        route = meta["family_heads"]["router"]
        changed = not pd.read_parquet(numeric).equals(pd.read_parquet(active))
        success = (
            all(
                route.get(field) is True
                for field in (
                    "endpoint_configured",
                    "call_succeeded",
                    "parse_succeeded",
                    "validation_succeeded",
                    "gate_passed",
                    "samples_changed",
                )
            )
            and changed
        )
        results.append(
            {
                "unit": unit,
                "family": family,
                "passed": success,
                "samples_differ": changed,
                "router": route,
                "head_reason": meta["family_heads"]["reason"],
            }
        )
    (out / "activation-results.json").write_text(
        json.dumps({"mode": mode, "cases": results}, indent=2) + "\n"
    )
    if not {x["family"] for x in results if x["passed"]} >= {"T2-F2", "T2-F4"}:
        raise RuntimeError("F2 and F4 both require a complete, changed-samples activation")
    return results


def main() -> int:
    p = argparse.ArgumentParser(description="Gate F2/F4 activation before scoring")
    p.add_argument("--out", type=pathlib.Path, required=True)
    p.add_argument("--mode", choices=("mock", "live"), required=True)
    p.add_argument("--units", nargs="+", default=UNITS)
    p.add_argument(
        "--docker-image",
        default="",
        help="also exercise the Docker forecast command over real HTTP",
    )
    args = p.parse_args()
    if args.mode == "mock":
        with local_house():
            rows = run(args.out.resolve(), args.mode, tuple(args.units), args.docker_image)
    else:
        rows = run(args.out.resolve(), args.mode, tuple(args.units), args.docker_image)
    print(
        json.dumps(
            {
                "mode": args.mode,
                "cases": [
                    {
                        "unit": x["unit"],
                        "passed": x["passed"],
                        "samples_differ": x["samples_differ"],
                        "gate_passed": x["router"]["gate_passed"],
                    }
                    for x in rows
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
