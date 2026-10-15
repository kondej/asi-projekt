"""Kontrakt metrics.json i obliczanie metryk."""

import json

import pytest

from asi_project.config import load_project_config
from asi_project.metrics import (
    build_metrics_record,
    compute_metrics,
    save_metrics,
    validate_metrics_record,
)


def _record(toy_contract, repo_root, n_test=4):
    config = load_project_config(repo_root)
    results = {
        "dummy": compute_metrics([0, 0, 1, 1], [0, 0, 0, 0]),
        "logistic_regression": compute_metrics([0, 0, 1, 1], [0, 1, 1, 1]),
    }
    return build_metrics_record(
        contract=toy_contract,
        config=config,
        features=["num", "cat"],
        n_train=12,
        n_test=n_test,
        data_mode="full",
        results=results,
    )


def test_compute_metrics_for_positive_class():
    metrics = compute_metrics([0, 0, 1, 1], [0, 1, 1, 1])
    assert metrics["accuracy"] == pytest.approx(0.75)
    assert metrics["precision"] == pytest.approx(2 / 3)
    assert metrics["recall"] == pytest.approx(1.0)
    assert metrics["confusion_matrix"] == {"tn": 1, "fp": 1, "fn": 0, "tp": 2}


def test_valid_record_passes(toy_contract, repo_root):
    assert validate_metrics_record(_record(toy_contract, repo_root), toy_contract) == []


def test_invalid_records_are_reported(toy_contract, repo_root):
    record = _record(toy_contract, repo_root)
    record["models"]["dummy"]["f1"] = 1.5
    assert validate_metrics_record(record, toy_contract)

    record = _record(toy_contract, repo_root, n_test=99)
    assert any("n_test" in p for p in validate_metrics_record(record, toy_contract))

    record = _record(toy_contract, repo_root)
    record["features"] = ["num", "leak"]
    assert any("ALLOWED" in p for p in validate_metrics_record(record, toy_contract))

    record = _record(toy_contract, repo_root)
    del record["models"]["logistic_regression"]
    assert validate_metrics_record(record, toy_contract)


def test_save_metrics_writes_newline_terminated_json(toy_contract, repo_root, tmp_path):
    path = save_metrics(_record(toy_contract, repo_root), tmp_path / "metrics.json", toy_contract)
    text = path.read_text(encoding="utf-8")
    assert text.endswith("}\n")
    assert json.loads(text)["dataset"] == "toy"
    broken = _record(toy_contract, repo_root)
    broken["data_mode"] = "maybe"
    with pytest.raises(ValueError):
        save_metrics(broken, tmp_path / "broken.json")
