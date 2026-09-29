"""Frozen support gate, evaluated once for the entire requested card."""


def supported(artifact: dict, assets: list[str], target_type: str,
              target_frequency: str) -> tuple[bool, str]:
    if target_frequency.lower() not in {"daily", "business_daily"}:
        return False, "non_daily_target"
    known = artifact["assets"]
    for a in assets:
        if a not in known or a in artifact["unsupported_assets"]:
            return False, "missing_decoder_asset"
        index = known.index(a)
        if artifact["fit_cells_by_asset"][index] < 100:
            return False, "fewer_than_100_fit_cells"
        if artifact["decoder_target_types"].get(a) != target_type:
            return False, "decoder_target_type_mismatch"
    return True, "supported"
