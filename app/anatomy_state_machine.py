from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AnatomyState(str, Enum):
    NONE = "none"
    DETECTED = "detected"
    TESTING = "testing"
    CONFIRMED = "confirmed"
    INVALIDATED = "invalidated"
    EXPIRED = "expired"


@dataclass
class AnatomyStateMachine:
    state: AnatomyState = AnatomyState.NONE
    bars_alive: int = 0

    def detect(self) -> AnatomyState:
        if self.state == AnatomyState.NONE:
            self.state = AnatomyState.DETECTED
            self.bars_alive = 0
        return self.state

    def test(self) -> AnatomyState:
        if self.state == AnatomyState.DETECTED:
            self.state = AnatomyState.TESTING
        return self.state

    def confirm(self) -> AnatomyState:
        if self.state == AnatomyState.TESTING:
            self.state = AnatomyState.CONFIRMED
        return self.state

    def invalidate(self) -> AnatomyState:
        if self.state in {AnatomyState.DETECTED, AnatomyState.TESTING, AnatomyState.CONFIRMED}:
            self.state = AnatomyState.INVALIDATED
        return self.state

    def expire(self, max_bars: int) -> AnatomyState:
        if self.state in {AnatomyState.DETECTED, AnatomyState.TESTING}:
            self.bars_alive += 1
            if self.bars_alive > max_bars:
                self.state = AnatomyState.EXPIRED
        return self.state

    def reset(self) -> None:
        self.state = AnatomyState.NONE
        self.bars_alive = 0
