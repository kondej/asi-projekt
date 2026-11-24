"""Metadane pakietu modelu: pochodzenie, budowa i walidacja ``metadata.json``.

Lista ``REQUIRED_KEYS`` poniżej dokumentuje kontrakt ``metadata.json``. Zmiana kluczy wymaga
uzgodnienia z zespołem (Piotr: ``model_package.py``, Denys: testy CI, W&B i smoke) oraz
aktualizacji sekcji „Klucze metadata.json” w ``src/asi_project/README.md``.
"""

import hashlib
import importlib.metadata
import json
import subprocess
from datetime import datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pytest

from asi_project import model_metadata
from asi_project.metrics import METRIC_NAMES, compute_metrics

REQUIRED_KEYS = [
    "schema_version",
    "created_at",
    "dataset",
    "target",
    "positive_class",
    "model_format",
    "model_name",
    "features",
    "feature_types",
    "metrics",
    "data_fingerprint",
    "git_sha",
    "library_versions",
]


def _fake_git(returncode, stdout=""):
    def run(*args, **kwargs):
        return subprocess.CompletedProcess(args, returncode, stdout=stdout, stderr="")

    return run


def _git_missing(*args, **kwargs):
    raise FileNotFoundError("git")


def test_git_sha_comes_from_git(monkeypatch):
    monkeypatch.setattr(model_metadata.subprocess, "run", _fake_git(0, "abc123\n"))
    monkeypatch.setenv("GITHUB_SHA", "from-env")
    assert model_metadata.get_git_sha() == "abc123"


def test_git_sha_falls_back_to_github_sha_when_git_fails(monkeypatch):
    monkeypatch.setattr(model_metadata.subprocess, "run", _fake_git(128))
    monkeypatch.setenv("GITHUB_SHA", "from-env")
    assert model_metadata.get_git_sha() == "from-env"


def test_git_sha_falls_back_to_github_sha_when_git_is_missing(monkeypatch):
    monkeypatch.setattr(model_metadata.subprocess, "run", _git_missing)
    monkeypatch.setenv("GITHUB_SHA", "from-env")
    assert model_metadata.get_git_sha() == "from-env"


def test_git_sha_is_unknown_without_git_and_github_sha(monkeypatch):
    monkeypatch.setattr(model_metadata.subprocess, "run", _git_missing)
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    assert model_metadata.get_git_sha() == model_metadata.UNKNOWN == "unknown"


def _config(tmp_path):
    return SimpleNamespace(root=tmp_path, ci_sample_path=tmp_path / "sample.csv")


def _write_fingerprint(tmp_path, text):
    directory = tmp_path / "data" / "01_raw" / "toy"
    directory.mkdir(parents=True)
    (directory / "fingerprint.json").write_text(text, encoding="utf-8")


def test_data_fingerprint_full_reads_sha256_from_fingerprint_file(tmp_path, toy_contract):
    _write_fingerprint(tmp_path, json.dumps({"sha256": "abc"}))
    result = model_metadata.get_data_fingerprint(_config(tmp_path), toy_contract, "full")
    assert result == "abc"


@pytest.mark.parametrize("content", ["not json", '{"file": "toy.csv"}', "[]"])
def test_data_fingerprint_full_is_unknown_for_broken_file(tmp_path, toy_contract, content):
    _write_fingerprint(tmp_path, content)
    result = model_metadata.get_data_fingerprint(_config(tmp_path), toy_contract, "full")
    assert result == model_metadata.UNKNOWN


def test_data_fingerprint_full_is_unknown_without_file(tmp_path, toy_contract):
    result = model_metadata.get_data_fingerprint(_config(tmp_path), toy_contract, "full")
    assert result == model_metadata.UNKNOWN


def test_data_fingerprint_sample_hashes_ci_sample(tmp_path, toy_contract):
    content = b"num,cat,label\n1,a,yes\n"
    (tmp_path / "sample.csv").write_bytes(content)
    result = model_metadata.get_data_fingerprint(_config(tmp_path), toy_contract, "sample")
    assert result == hashlib.sha256(content).hexdigest()


def test_data_fingerprint_sample_is_unknown_without_file(tmp_path, toy_contract):
    result = model_metadata.get_data_fingerprint(_config(tmp_path), toy_contract, "sample")
    assert result == model_metadata.UNKNOWN


def test_data_fingerprint_rejects_unknown_data_mode(tmp_path, toy_contract):
    with pytest.raises(ValueError, match="Nieznany tryb danych"):
        model_metadata.get_data_fingerprint(_config(tmp_path), toy_contract, "xyz")


def _fake_versions(missing):
    def version(name):
        if name in missing:
            raise importlib.metadata.PackageNotFoundError(name)
        return "1.2.3"

    return version


def test_library_versions_in_current_environment():
    versions = model_metadata.get_library_versions()
    assert {"python", *model_metadata.REQUIRED_LIBRARIES} <= set(versions)
    assert all(isinstance(value, str) and value for value in versions.values())
    json.dumps(versions)


def test_library_versions_skip_missing_optional_libraries(monkeypatch):
    fake = _fake_versions({"autogluon.tabular", "wandb"})
    monkeypatch.setattr(model_metadata.importlib.metadata, "version", fake)
    versions = model_metadata.get_library_versions()
    assert "autogluon.tabular" not in versions
    assert "wandb" not in versions
    assert versions["pandas"] == "1.2.3"


def test_library_versions_mark_missing_required_library_as_unknown(monkeypatch):
    fake = _fake_versions({"pandas"})
    monkeypatch.setattr(model_metadata.importlib.metadata, "version", fake)
    versions = model_metadata.get_library_versions()
    assert versions["pandas"] == model_metadata.UNKNOWN
    assert versions["numpy"] == "1.2.3"


def _build(contract, **overrides):
    arguments = {
        "contract": contract,
        "features": {"numeric": ["num"], "categorical": ["cat"]},
        "metrics": compute_metrics([0, 0, 1, 1], [0, 1, 1, 1]),
        "model_format": "sklearn",
        "model_name": "logistic_regression",
        "data_fingerprint": "abc",
        "git_sha": "deadbeef",
        "library_versions": {"python": "3.11.18"},
    }
    arguments.update(overrides)
    return model_metadata.build_metadata(**arguments)


def test_build_metadata_takes_values_from_contract(toy_contract):
    metadata = _build(toy_contract)
    assert metadata["dataset"] == "toy"
    assert metadata["target"] == "label"
    assert metadata["positive_class"] == "yes"
    assert metadata["schema_version"] == model_metadata.METADATA_SCHEMA_VERSION == 1


def test_build_metadata_keeps_declared_order_numeric_first(toy_contract):
    metadata = _build(toy_contract)
    assert metadata["features"] == ["num", "cat"]
    assert metadata["feature_types"] == {"numeric": ["num"], "categorical": ["cat"]}
    # Kolejność wynika z deklaracji (numeryczne, potem kategoryczne), a nie z listy ALLOWED.
    swapped = _build(toy_contract, features={"numeric": ["cat"], "categorical": ["num"]})
    assert swapped["features"] == ["cat", "num"]


def test_build_metadata_keeps_only_main_metrics_as_floats(toy_contract):
    metrics = _build(toy_contract)["metrics"]
    assert list(metrics) == list(METRIC_NAMES)
    assert metrics["f1"] == pytest.approx(0.8)
    assert all(type(value) is float for value in metrics.values())


def test_build_metadata_created_at_is_utc_iso_8601(toy_contract):
    created = datetime.fromisoformat(_build(toy_contract)["created_at"])
    assert created.utcoffset() == timedelta(0)


def test_build_metadata_is_json_serializable_without_numpy_types(toy_contract):
    metrics = {name: np.float32(0.5) for name in METRIC_NAMES}
    features = {"numeric": ("num",), "categorical": ("cat",)}
    metadata = _build(toy_contract, metrics=metrics, features=features)
    assert json.loads(json.dumps(metadata)) == metadata


def test_build_metadata_stores_provenance_values(toy_contract):
    metadata = _build(toy_contract)
    assert metadata["model_format"] == "sklearn"
    assert metadata["model_name"] == "logistic_regression"
    assert metadata["data_fingerprint"] == "abc"
    assert metadata["git_sha"] == "deadbeef"
    assert metadata["library_versions"] == {"python": "3.11.18"}


@pytest.mark.parametrize("feature", ["leak", "other", "label"])
def test_build_metadata_rejects_feature_outside_allowed_features(toy_contract, feature):
    features = {"numeric": ["num", feature], "categorical": ["cat"]}
    with pytest.raises(ValueError, match=feature):
        _build(toy_contract, features=features)


def test_build_metadata_requires_all_main_metrics(toy_contract):
    metrics = {"accuracy": 0.5, "precision": 0.5, "recall": 0.5}
    with pytest.raises(ValueError, match="f1"):
        _build(toy_contract, metrics=metrics)


def test_build_metadata_accepts_declared_project_features(project):
    config = project.config
    features = {"numeric": config.numeric_features, "categorical": config.categorical_features}
    metadata = _build(project.contract, features=features)
    assert metadata["features"] == list(config.model_features)


def test_required_keys_document_the_metadata_contract(toy_contract):
    assert set(_build(toy_contract)) == set(REQUIRED_KEYS)
    assert set(model_metadata.REQUIRED_KEYS) == set(REQUIRED_KEYS)


def test_validate_metadata_accepts_built_metadata(toy_contract):
    metadata = _build(toy_contract)
    assert model_metadata.validate_metadata(metadata) == []
    assert model_metadata.validate_metadata(metadata, toy_contract) == []


@pytest.mark.parametrize("metadata", [None, [], "text"])
def test_validate_metadata_requires_a_mapping(metadata):
    assert len(model_metadata.validate_metadata(metadata)) == 1


@pytest.mark.parametrize("key", REQUIRED_KEYS)
def test_validate_metadata_reports_missing_key(toy_contract, key):
    metadata = _build(toy_contract)
    del metadata[key]
    problems = model_metadata.validate_metadata(metadata, toy_contract)
    assert f"{key}: brak wymaganego klucza." in problems


def test_validate_metadata_rejects_feature_outside_contract(toy_contract):
    metadata = _build(toy_contract)
    metadata["features"] = ["num", "leak", "cat"]
    metadata["feature_types"]["numeric"] = ["num", "leak"]
    problems = model_metadata.validate_metadata(metadata, toy_contract)
    assert len(problems) == 1
    assert "leak" in problems[0]
    # Bez kontraktu walidator nie wie, które cechy są dozwolone.
    assert model_metadata.validate_metadata(metadata) == []


def test_validate_metadata_rejects_wrong_positive_class(toy_contract):
    metadata = _build(toy_contract)
    metadata["positive_class"] = "no"
    assert model_metadata.validate_metadata(metadata, toy_contract) == [
        "positive_class: oczekiwano 'yes', jest 'no'.",
    ]


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("dataset", "dataset: oczekiwano 'toy', jest 'other'."),
        ("target", "target: oczekiwano 'label', jest 'other'."),
    ],
)
def test_validate_metadata_rejects_dataset_or_target_that_differs_from_contract(
    toy_contract,
    key,
    expected,
):
    metadata = _build(toy_contract)
    metadata[key] = "other"
    assert model_metadata.validate_metadata(metadata, toy_contract) == [expected]


@pytest.mark.parametrize("value", [-0.1, 1.5, float("nan"), "0.5", True])
def test_validate_metadata_rejects_metric_outside_unit_interval(toy_contract, value):
    metadata = _build(toy_contract)
    metadata["metrics"]["f1"] = value
    assert model_metadata.validate_metadata(metadata, toy_contract) == [
        "metrics.f1: oczekiwana liczba z zakresu [0, 1].",
    ]


def test_validate_metadata_requires_all_main_metrics(toy_contract):
    metadata = _build(toy_contract)
    del metadata["metrics"]["recall"]
    problems = model_metadata.validate_metadata(metadata, toy_contract)
    assert "metrics.recall: brak metryki." in problems


def test_validate_metadata_rejects_other_schema_version(toy_contract):
    metadata = _build(toy_contract)
    metadata["schema_version"] = 2
    assert "schema_version: oczekiwano 1." in model_metadata.validate_metadata(metadata)


def test_validate_metadata_rejects_invalid_created_at(toy_contract):
    metadata = _build(toy_contract)
    metadata["created_at"] = "yesterday"
    problems = model_metadata.validate_metadata(metadata)
    assert "created_at: oczekiwana data w formacie ISO 8601." in problems


def test_validate_metadata_requires_features_to_match_feature_types(toy_contract):
    metadata = _build(toy_contract)
    metadata["features"] = ["cat", "num"]
    problems = model_metadata.validate_metadata(metadata, toy_contract)
    assert len(problems) == 1
    assert problems[0].startswith("features:")


@pytest.mark.parametrize("versions", [{}, {"python": 3}])
def test_validate_metadata_rejects_invalid_library_versions(toy_contract, versions):
    metadata = _build(toy_contract)
    metadata["library_versions"] = versions
    problems = model_metadata.validate_metadata(metadata)
    assert len(problems) == 1
    assert problems[0].startswith("library_versions:")


def test_validate_metadata_rejects_empty_text_values(toy_contract):
    metadata = _build(toy_contract)
    metadata["git_sha"] = ""
    assert model_metadata.validate_metadata(metadata) == ["git_sha: oczekiwany niepusty tekst."]
