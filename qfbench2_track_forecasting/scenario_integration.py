"""## Executive summary (read this first)

This module connects validated Phase-4 evidence to Numeric v3 Monte Carlo draws.  It samples one
scenario world per draw and applies that same world across every asset and horizon.  Family routes
are deliberately different: F1 permits only a small contextual adjustment, F2 changes regime
mixture, F3 changes joint pairing while preserving every marginal value, and F4 adds a bounded
directional shock branch.  Missing or unusable evidence returns Numeric v3 exactly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .text_evidence import SCENARIOS, ReasoningResult

_EPSILON = 1e-12
_RNG_SALT = 0x5A17C3E9
_SHOCK_SCENARIOS = {
    "INFLATION_SHOCK",
    "GROWTH_SHOCK",
    "LIQUIDITY_SHOCK",
    "CARRY_UNWIND",
    "POLICY_MISTAKE",
    "UNKNOWN_DOWNSIDE",
    "UNKNOWN_UPSIDE",
}


@dataclass(frozen=True)
class IntegrationConfig:
    """Auditable caps for one family-specific evidence route."""

    name: str
    mean_shift_sd: float
    volatility_scale: float
    tail_fraction: float
    tail_scale_sd: float
    rank_strength: float
    max_change_sd: float


FAMILY_CONFIGS = {
    "T2-F1": IntegrationConfig(
        name="F1 conservative context",
        mean_shift_sd=0.05,
        volatility_scale=0.03,
        tail_fraction=0.00,
        tail_scale_sd=0.00,
        rank_strength=0.00,
        max_change_sd=0.15,
    ),
    "T2-F2": IntegrationConfig(
        name="F2 regime-shift mixture",
        mean_shift_sd=0.25,
        volatility_scale=0.12,
        tail_fraction=0.03,
        tail_scale_sd=0.60,
        rank_strength=0.00,
        max_change_sd=1.50,
    ),
    "T2-F3": IntegrationConfig(
        name="F3 scenario world pairing",
        mean_shift_sd=0.00,
        volatility_scale=0.00,
        tail_fraction=0.00,
        tail_scale_sd=0.00,
        rank_strength=0.15,
        max_change_sd=0.00,
    ),
    "T2-F4": IntegrationConfig(
        name="F4 asymmetric shock branch",
        mean_shift_sd=0.10,
        volatility_scale=0.10,
        tail_fraction=0.07,
        tail_scale_sd=1.40,
        rank_strength=0.00,
        max_change_sd=3.50,
    ),
}

# Frozen deployment config selected by the public Nemotron F4 calibration.
# Do not derive this dynamically from FAMILY_CONFIGS: the exact values below are
# part of the approved experiment provenance.
APPROVED_F4_CONFIG = IntegrationConfig(
    name="F4 asymmetric shock branch x0.50",
    mean_shift_sd=0.05,
    volatility_scale=0.05,
    tail_fraction=0.035,
    tail_scale_sd=0.70,
    rank_strength=0.00,
    max_change_sd=1.75,
)


@dataclass(frozen=True)
class ScenarioProfiles:
    """Scenario-conditioned asset directions and distribution effects."""

    direction: NDArray[np.float64]
    volatility: NDArray[np.float64]
    tail: NDArray[np.float64]
    activation: NDArray[np.float64]


@dataclass(frozen=True)
class IntegrationResult:
    """Integrated samples plus an audit ledger describing every bounded transformation."""

    samples: NDArray[np.float64]
    metadata: dict[str, Any]


def _direction_value(value: str) -> float:
    return {"up": 1.0, "down": -1.0, "mixed": 0.0, "none": 0.0}.get(value, 0.0)


def _volatility_value(value: str) -> float:
    return {"up": 1.0, "down": -0.5, "mixed": 0.5, "none": 0.0}.get(value, 0.0)


def _tail_value(value: str) -> float:
    return {"upside": 1.0, "downside": -1.0, "two_sided": 0.0, "none": 0.0}.get(value, 0.0)


def build_scenario_profiles(evidence: dict[str, Any], assets: list[str]) -> ScenarioProfiles:
    """Convert cited evidence into scenario-by-asset effects without inventing missing signs."""
    asset_index = {asset: index for index, asset in enumerate(assets)}
    scenario_index = {name: index for index, name in enumerate(SCENARIOS)}
    evidence_by_id = {item["id"]: item for item in evidence.get("evidence", [])}
    shape = (len(SCENARIOS), len(assets))
    direction = np.zeros(shape, dtype=np.float64)
    volatility = np.zeros(shape, dtype=np.float64)
    tail = np.zeros(shape, dtype=np.float64)
    activation = np.zeros(len(SCENARIOS), dtype=np.float64)

    for scenario in evidence.get("scenarios", []):
        name = scenario.get("name")
        if name not in scenario_index:
            continue
        scenario_row = scenario_index[name]
        net_support = max(
            0.0, float(scenario.get("support", 0.0)) - float(scenario.get("contradiction", 0.0))
        )
        activation[scenario_row] = float(
            np.clip(
                net_support
                * float(scenario.get("confidence", 0.0))
                * float(scenario.get("relevance", 0.0)),
                0.0,
                1.0,
            )
        )
        direction_weight = np.zeros(len(assets), dtype=np.float64)
        distribution_weight = 0.0
        for evidence_id in scenario.get("evidence_ids", []):
            item = evidence_by_id.get(evidence_id)
            if not item:
                continue
            base_weight = (
                float(item.get("strength", 0.0))
                * float(item.get("confidence", 0.0))
                * float(item.get("relevance", 0.0))
            )
            if item.get("stance") == "contradiction":
                base_weight *= -0.5
            absolute_weight = abs(base_weight)
            distribution_weight += absolute_weight
            vol_value = _volatility_value(str(item.get("volatility_impact", "none")))
            tail_value = _tail_value(str(item.get("tail_impact", "none")))
            for impact in item.get("asset_impacts", []):
                asset = impact.get("asset")
                if asset not in asset_index:
                    continue
                column = asset_index[asset]
                sign = _direction_value(str(impact.get("direction", "none")))
                intensity = float(impact.get("intensity", 0.0))
                weight = base_weight * intensity
                direction[scenario_row, column] += weight * sign
                direction_weight[column] += absolute_weight * intensity
                volatility[scenario_row, column] += absolute_weight * vol_value
                # A per-asset direction is less ambiguous than a document-wide tail label.
                tail_sign = sign if sign else tail_value
                tail[scenario_row, column] += absolute_weight * tail_sign * intensity

        valid = direction_weight > _EPSILON
        direction[scenario_row, valid] /= direction_weight[valid]
        if distribution_weight > _EPSILON:
            volatility[scenario_row] /= distribution_weight
            tail[scenario_row] /= distribution_weight

    return ScenarioProfiles(
        direction=np.clip(direction, -1.0, 1.0),
        volatility=np.clip(volatility, -0.5, 1.0),
        tail=np.clip(tail, -1.0, 1.0),
        activation=activation,
    )


def _sample_worlds(
    probabilities: dict[str, float], n_draws: int, seed: int
) -> tuple[NDArray[np.int64], NDArray[np.float64], np.random.Generator]:
    """Sample one scenario and one positive severity for each complete joint draw."""
    probability = np.asarray([float(probabilities[name]) for name in SCENARIOS], dtype=float)
    probability = np.clip(probability, 0.0, None)
    if not np.isfinite(probability).all() or probability.sum() <= 0.0:
        raise ValueError("scenario probabilities must be finite and have positive mass")
    probability /= probability.sum()
    rng = np.random.default_rng(int(seed) ^ _RNG_SALT)
    worlds = rng.choice(len(SCENARIOS), size=n_draws, p=probability).astype(np.int64)
    severity = np.clip(0.65 + 0.35 * np.abs(rng.standard_t(df=5, size=n_draws)), 0.65, 3.0)
    return worlds, np.asarray(severity, dtype=np.float64), rng


def _cell_scales(samples: NDArray[np.float64]) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    centres = np.mean(samples, axis=0)
    scales = np.std(samples, axis=0, ddof=1)
    fallback = np.maximum(np.abs(centres) * 1e-6, _EPSILON)
    return centres, np.where(scales > _EPSILON, scales, fallback)


def _horizon_scale(horizons: list[int]) -> NDArray[np.float64]:
    longest = max(horizons)
    return np.sqrt(np.asarray(horizons, dtype=np.float64) / float(longest))


def _value_route(
    samples: NDArray[np.float64],
    profiles: ScenarioProfiles,
    probabilities: dict[str, float],
    horizons: list[int],
    config: IntegrationConfig,
    worlds: NDArray[np.int64],
    severity: NDArray[np.float64],
    rng: np.random.Generator,
) -> tuple[NDArray[np.float64], dict[str, Any]]:
    """Apply bounded scenario shifts, scale changes, and an optional directional shock branch."""
    n_draws, n_assets, _ = samples.shape
    centres, scales = _cell_scales(samples)
    time_scale = _horizon_scale(horizons)[None, None, :]
    probability = np.asarray([probabilities[name] for name in SCENARIOS], dtype=np.float64)
    expected_volatility = probability @ (profiles.volatility * profiles.activation[:, None])
    volatility_multiplier = np.clip(
        1.0 + config.volatility_scale * expected_volatility,
        0.98,
        1.0 + config.volatility_scale,
    )

    centred = samples - centres[None, :, :]
    out = centres[None, :, :] + centred * volatility_multiplier[None, :, None]
    selected_direction = profiles.direction[worlds]
    selected_activation = profiles.activation[worlds]
    world_shift = selected_direction * selected_activation[:, None] * severity[:, None]
    out += config.mean_shift_sd * world_shift[:, :, None] * scales[None, :, :] * time_scale

    shock_mask = np.zeros(n_draws, dtype=bool)
    shock_direction = np.zeros((n_draws, n_assets), dtype=np.float64)
    if config.tail_fraction > 0.0 and config.tail_scale_sd > 0.0:
        selected_tail = profiles.tail[worlds]
        selected_names = np.asarray(SCENARIOS, dtype=object)[worlds]
        eligible = np.asarray([name in _SHOCK_SCENARIOS for name in selected_names], dtype=bool)
        priority = np.max(np.abs(selected_tail), axis=1) * selected_activation * severity * eligible
        positive = np.flatnonzero(priority > 0.0)
        requested = int(round(config.tail_fraction * n_draws))
        count = min(requested, len(positive))
        if count:
            selected = positive[np.argsort(priority[positive], kind="mergesort")[-count:]]
            shock_mask[selected] = True
            shock_direction[selected] = selected_tail[selected]
            # Directional Student-t magnitude makes the branch heavy-tailed but remains capped.
            magnitude = np.clip(1.0 + 0.45 * np.abs(rng.standard_t(df=4, size=count)), 1.0, 3.0)
            shock = (
                config.tail_scale_sd
                * shock_direction[selected, :, None]
                * magnitude[:, None, None]
                * scales[None, :, :]
                * time_scale
            )
            out[selected] += shock

    delta = out - samples
    cap = config.max_change_sd * scales[None, :, :]
    delta = np.clip(delta, -cap, cap)
    out = samples + delta
    if not np.isfinite(out).all():
        raise ValueError("scenario integration produced non-finite forecast values")
    return out, {
        "marginals_preserved_exactly": False,
        "volatility_multiplier": volatility_multiplier.tolist(),
        "shock_draw_count": int(shock_mask.sum()),
        "shock_draw_fraction": float(shock_mask.mean()),
        "maximum_absolute_change_sd": config.max_change_sd,
        "mean_absolute_change_sd": float(np.mean(np.abs(delta) / scales[None, :, :])),
    }


def _rank_route(
    samples: NDArray[np.float64],
    profiles: ScenarioProfiles,
    worlds: NDArray[np.int64],
    severity: NDArray[np.float64],
    config: IntegrationConfig,
    rng: np.random.Generator,
) -> tuple[NDArray[np.float64], dict[str, Any]]:
    """Re-pair F3 marginal values into scenario worlds while retaining each value exactly."""
    del rng  # The same sampled scenario worlds already provide the stochastic ordering signal.
    n_draws, n_assets, n_horizons = samples.shape
    selected_direction = profiles.direction[worlds]
    selected_activation = profiles.activation[worlds]
    scenario_signal = selected_direction * selected_activation[:, None] * severity[:, None]
    if np.max(np.std(scenario_signal, axis=0)) <= _EPSILON:
        return samples.copy(), {
            "marginals_preserved_exactly": True,
            "rank_strength": config.rank_strength,
            "pairing_changed": False,
            "reason": "validated evidence contained no varying cross-asset scenario direction",
        }
    signal_scale = np.std(scenario_signal, axis=0, ddof=1)
    active = signal_scale > _EPSILON
    scenario_signal[:, active] = (
        scenario_signal[:, active] - np.mean(scenario_signal[:, active], axis=0)
    ) / signal_scale[active]
    scenario_signal[:, ~active] = 0.0

    out = np.empty_like(samples)
    for horizon_index in range(n_horizons):
        values = samples[:, :, horizon_index]
        centre = np.mean(values, axis=0)
        scale = np.std(values, axis=0, ddof=1)
        scale = np.where(scale > _EPSILON, scale, 1.0)
        base_score = (values - centre) / scale
        score = base_score.copy()
        score[:, active] = (1.0 - config.rank_strength) * base_score[
            :, active
        ] + config.rank_strength * scenario_signal[:, active]
        for asset_index in range(n_assets):
            order = np.argsort(score[:, asset_index], kind="mergesort")
            out[order, asset_index, horizon_index] = np.sort(
                values[:, asset_index], kind="mergesort"
            )
    if not np.isfinite(out).all():
        raise ValueError("scenario rank integration produced non-finite forecast values")
    changed = not np.array_equal(out, samples)
    return out, {
        "marginals_preserved_exactly": True,
        "rank_strength": config.rank_strength,
        "pairing_changed": changed,
    }


def integrate_scenario_worlds(
    samples: NDArray[np.float64],
    reasoning: ReasoningResult,
    assets: list[str],
    horizons: list[int],
    family: str,
    seed: int,
    *,
    enabled: bool = True,
    config_override: IntegrationConfig | None = None,
) -> IntegrationResult:
    """Integrate validated evidence, or return an exact copy with a machine-readable reason."""
    config = config_override or FAMILY_CONFIGS.get(family)
    base_metadata: dict[str, Any] = {
        "enabled": enabled,
        "family": family,
        "applied": False,
        "numeric_fallback_exact": True,
    }
    if not enabled:
        return IntegrationResult(
            samples.copy(), {**base_metadata, "reason": "TEXT_INTEGRATION kill switch is off"}
        )
    if not reasoning.applied or not reasoning.evidence:
        return IntegrationResult(
            samples.copy(),
            {**base_metadata, "reason": reasoning.skipped_reason or "no validated evidence"},
        )
    if config is None:
        return IntegrationResult(
            samples.copy(), {**base_metadata, "reason": f"unsupported family {family!r}"}
        )
    if samples.ndim != 3 or samples.shape[1:] != (len(assets), len(horizons)):
        raise ValueError("sample tensor does not match the requested asset-horizon grid")

    profiles = build_scenario_profiles(reasoning.evidence, assets)
    worlds, severity, rng = _sample_worlds(reasoning.scenario_probabilities, samples.shape[0], seed)
    if family == "T2-F3":
        if len(assets) < 2:
            return IntegrationResult(
                samples.copy(),
                {**base_metadata, "config": config.name, "reason": "F3 route needs two assets"},
            )
        integrated, details = _rank_route(samples, profiles, worlds, severity, config, rng)
    else:
        integrated, details = _value_route(
            samples,
            profiles,
            reasoning.scenario_probabilities,
            horizons,
            config,
            worlds,
            severity,
            rng,
        )

    changed = not np.array_equal(integrated, samples)
    counts = np.bincount(worlds, minlength=len(SCENARIOS))
    metadata = {
        **base_metadata,
        "config": config.name,
        "config_values": {
            "mean_shift_sd": config.mean_shift_sd,
            "volatility_scale": config.volatility_scale,
            "tail_fraction": config.tail_fraction,
            "tail_scale_sd": config.tail_scale_sd,
            "rank_strength": config.rank_strength,
            "max_change_sd": config.max_change_sd,
        },
        "applied": changed,
        "numeric_fallback_exact": not changed,
        "reason": "" if changed else details.get("reason", "integration made no numerical change"),
        "scenario_draw_counts": {name: int(counts[index]) for index, name in enumerate(SCENARIOS)},
        "scenario_probabilities": dict(reasoning.scenario_probabilities),
        "mean_activation": float(np.mean(profiles.activation[worlds])),
        **details,
    }
    return IntegrationResult(integrated, metadata)
