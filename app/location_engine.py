from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LocationResult:
    location: str
    normalized_position: float
    distance_to_boundary: float
    tradable: bool


def classify_location(
    price: float,
    range_low: float,
    range_high: float,
    tolerance: float = 0.15,
) -> LocationResult:
    """Classify price within a validated range.

    Returns boundary locations only when price is near the lower/upper edge;
    mid-range is deliberately non-tradable for pullback detection.
    """
    width = range_high - range_low
    if width <= 0:
        return LocationResult("unknown", 0.0, 0.0, False)

    position = (price - range_low) / width
    distance_to_boundary = min(position, 1.0 - position)

    if position <= tolerance:
        return LocationResult("lower_boundary", position, distance_to_boundary, True)
    if position >= 1.0 - tolerance:
        return LocationResult("upper_boundary", position, distance_to_boundary, True)

    return LocationResult("mid_range", position, distance_to_boundary, False)
