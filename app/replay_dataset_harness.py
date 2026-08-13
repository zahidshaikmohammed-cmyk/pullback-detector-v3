from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .market_data_ingestion import Candle
from .pipeline_orchestrator import PipelineResult, run_pipeline


@dataclass(frozen=True)
class ReplayCase:
    case_id: str
    location: str
    candles: list[Candle]


@dataclass(frozen=True)
class ReplayResult:
    case_id: str
    regime: str
    anatomy_count: int
    confirmation_count: int
    signal: str | None
    entry_available: bool


def load_jsonl(path: str | Path) -> list[ReplayCase]:
    cases: list[ReplayCase] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        candles = [Candle(instrument=row["instrument"], timestamp=datetime.fromisoformat(row["timestamp"]),
                          open=row["open"], high=row["high"], low=row["low"], close=row["close"], volume=row["volume"])
                   for row in raw["candles"]]
        cases.append(ReplayCase(raw["case_id"], raw["location"], candles))
    return cases


def run_case(case: ReplayCase) -> ReplayResult:
    result: PipelineResult = run_pipeline(case.candles, case.location)
    signal = getattr(result.signal, "direction", None) if result.signal else None
    return ReplayResult(case.case_id, result.regime.regime, len(result.anatomies),
                        len(result.confirmations), signal, result.entry is not None)


def run_dataset(cases: Iterable[ReplayCase]) -> list[ReplayResult]:
    return [run_case(case) for case in cases]


def write_results(path: str | Path, results: Iterable[ReplayResult]) -> None:
    rows = [asdict(result) for result in results]
    if not rows:
        Path(path).write_text("", encoding="utf-8")
        return
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
