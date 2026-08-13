from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfirmationResult:
    confirmed: bool
    structure_intact: bool
    retest_valid: bool
    response_valid: bool
    displacement_valid: bool
    score: int


def confirm_pullback(
    *,
    structure_intact: bool,
    retest_valid: bool,
    response_valid: bool,
    displacement_valid: bool,
) -> ConfirmationResult:
    checks = (
        structure_intact,
        retest_valid,
        response_valid,
        displacement_valid,
    )
    score = sum(bool(value) for value in checks)
    return ConfirmationResult(
        confirmed=score == 4,
        structure_intact=structure_intact,
        retest_valid=retest_valid,
        response_valid=response_valid,
        displacement_valid=displacement_valid,
        score=score,
    )
