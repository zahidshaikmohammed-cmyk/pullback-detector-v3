from pathlib import Path

from app.replay_dataset_harness import load_jsonl, run_dataset, write_results


FIXTURE = Path(__file__).parent / "fixtures" / "replay_sample.jsonl"


def test_replay_dataset_load_and_run(tmp_path):
    cases = load_jsonl(FIXTURE)
    assert len(cases) == 2

    results = run_dataset(cases)
    assert [item.case_id for item in results] == ["sideways_lower_boundary_reclaim", "insufficient_data"]
    assert results[1].regime == "unknown"
    assert results[1].signal is None

    output = tmp_path / "replay_results.csv"
    write_results(output, results)
    assert output.exists()
    assert "case_id" in output.read_text(encoding="utf-8")
