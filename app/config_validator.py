from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


REQUIRED_TOP_LEVEL = {
    "version",
    "mode",
    "session",
    "data",
    "regime",
    "location",
    "anatomy",
    "confirmation",
    "signal",
    "entry",
    "risk",
    "replay",
    "observability",
}

ALLOWED_MODES = {"shadow", "research", "live"}
ALLOWED_REGIMES = {"sideways", "transitional"}
ALLOWED_ANATOMIES = {
    "failed_auction",
    "sweep_reclaim",
    "breakout_retest",
    "compression_expansion",
}


def load_config(path: str | Path) -> dict[str, Any]:
    """Load and validate a V3 YAML configuration."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    if not isinstance(config, dict):
        raise ValueError("Configuration root must be a mapping")

    validate_config(config)
    return config


def validate_config(config: dict[str, Any]) -> None:
    """Fail closed when configuration is missing or unsafe."""
    missing = REQUIRED_TOP_LEVEL - config.keys()
    if missing:
        raise ValueError(f"Missing configuration sections: {sorted(missing)}")

    if config["mode"] not in ALLOWED_MODES:
        raise ValueError(f"Unsupported mode: {config['mode']}")

    data = config["data"]
    if data["primary_timeframe"] != "5m":
        raise ValueError("V3 primary timeframe must be 5m")
    if not data["fail_closed"]:
        raise ValueError("fail_closed must remain enabled")
    if not data["reject_future_timestamps"]:
        raise ValueError("Future timestamps must be rejected")

    regime = config["regime"]
    if not regime["enabled"]:
        raise ValueError("Regime gate cannot be disabled")
    if not set(regime["allowed"]).issubset(ALLOWED_REGIMES):
        raise ValueError("Unknown regime configured")

    location = config["location"]
    if location["allow_mid_range"]:
        raise ValueError("Mid-range signals are disabled by V3 design")

    anatomies = set(config["anatomy"]["enabled"])
    if not anatomies.issubset(ALLOWED_ANATOMIES):
        raise ValueError("Unknown anatomy configured")

    confirmation = config["confirmation"]
    required_confirmation = (
        "require_structure_intact",
        "require_retest",
        "require_response",
        "require_displacement",
    )
    if not all(confirmation[key] for key in required_confirmation):
        raise ValueError("All confirmation gates must remain enabled")

    signal = config["signal"]
    if signal["max_signal_per_anatomy"] != 1:
        raise ValueError("Maximum one signal per anatomy is required")

    risk = config["risk"]
    if not risk["enabled"] or not risk["require_valid_invalidation"]:
        raise ValueError("Risk and structural invalidation gates are mandatory")
    if risk["minimum_reward_risk"] <= 0:
        raise ValueError("minimum_reward_risk must be positive")

    replay = config["replay"]
    if not replay["chronological_only"] or not replay["forbid_lookahead"]:
        raise ValueError("Replay must be chronological and look-ahead free")


if __name__ == "__main__":
    load_config("config/v3.yaml")
    print("V3 configuration valid")
