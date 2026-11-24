import json
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import pandas as pd
import pytest

from asi_project import model_metadata, model_package
from asi_project.metrics import compute_metrics
from asi_project.model import build_baseline_pipeline


def _make_metadata(contract, *, model_format: str = "sklearn-joblib", model_name: str = "baseline"):
    return model_metadata.build_metadata(
        contract=contract,
        features={"numeric": ["num"], "categorical": ["cat"]},
        metrics=compute_metrics([0, 0, 1, 1], [0, 1, 1, 1]),
        model_format=model_format,
        model_name=model_name,
        data_fingerprint="abc123",
        git_sha="deadbeef",
        library_versions={"python": "3.11.18"},
    )


def test_import_works_without_wandb_and_autogluon(monkeypatch):
    monkeypatch.setitem(sys.modules, "wandb", None)
    monkeypatch.setitem(sys.modules, "autogluon", None)
    monkeypatch.setitem(sys.modules, "autogluon.tabular", None)
    monkeypatch.delitem(sys.modules, "asi_project.model_package", raising=False)

    import asi_project.model_package as reloaded_module

    assert hasattr(reloaded_module, "save_model_package")
    assert hasattr(reloaded_module, "load_model_package")


def test_sklearn_save_and_load_preserves_predictions(tmp_path, toy_contract, toy_frame):
    features = {"numeric": ["num"], "categorical": ["cat"]}
    X = toy_frame[["num", "cat"]]
    y = (toy_frame["label"] == "yes").astype(int)

    model = build_baseline_pipeline(features["numeric"], features["categorical"])
    model.fit(X, y)
    expected_pred = model.predict(X)
    expected_proba = model.predict_proba(X)

    metadata = _make_metadata(toy_contract, model_format="sklearn-joblib")
    package_dir = tmp_path / "pkg"
    saved_path = model_package.save_model_package(model, metadata, package_dir, contract=toy_contract)

    assert saved_path == package_dir
    assert (package_dir / "model.joblib").is_file()
    assert (package_dir / "metadata.json").is_file()

    loaded = model_package.load_model_package(package_dir, contract=toy_contract)
    assert isinstance(loaded, model_package.ModelPackage)
    assert loaded.metadata == metadata
    assert loaded.path == package_dir
    np.testing.assert_array_equal(loaded.model.predict(X), expected_pred)
    np.testing.assert_allclose(loaded.model.predict_proba(X), expected_proba)


def test_autogluon_save_and_load_uses_lazy_import_and_model_dir(
    tmp_path, monkeypatch, toy_contract
):
    source_dir = tmp_path / "ag_source"
    source_dir.mkdir()
    (source_dir / "predictor.pkl").write_text("fake", encoding="utf-8")

    class FakePredictor:
        def __init__(self, path: Path):
            self.path = str(path)

        def clone(self, target_path: str, *, dirs_exist_ok: bool = False) -> str:
            target = Path(target_path)
            target.mkdir(parents=True, exist_ok=dirs_exist_ok)
            (target / "predictor.pkl").write_text("cloned", encoding="utf-8")
            return target_path

        @classmethod
        def load(cls, path: str) -> "FakePredictor":
            return cls(Path(path))

        def predict(self, df: pd.DataFrame) -> pd.Series:
            return pd.Series([1] * len(df))

    fake_ag = ModuleType("autogluon")
    fake_tabular = ModuleType("autogluon.tabular")
    fake_tabular.TabularPredictor = FakePredictor
    monkeypatch.setitem(sys.modules, "autogluon", fake_ag)
    monkeypatch.setitem(sys.modules, "autogluon.tabular", fake_tabular)

    metadata = _make_metadata(toy_contract, model_format="autogluon", model_name="ag_fast")
    package_dir = tmp_path / "ag_pkg"
    model_package.save_model_package(FakePredictor(source_dir), metadata, package_dir)

    assert (package_dir / "model" / "predictor.pkl").is_file()
    assert (package_dir / "metadata.json").is_file()

    loaded = model_package.load_model_package(package_dir)
    assert isinstance(loaded.model, FakePredictor)
    assert Path(loaded.model.path) == package_dir / "model"
    assert list(loaded.model.predict(pd.DataFrame({"num": [1.0, 2.0]}))) == [1, 1]


def test_load_raises_when_metadata_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="metadata.json"):
        model_package.load_model_package(tmp_path)


def test_load_raises_on_corrupt_metadata_json(tmp_path):
    (tmp_path / "metadata.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="Nie udało się odczytać"):
        model_package.load_model_package(tmp_path)


def test_save_and_load_reject_unknown_model_format(tmp_path, toy_contract):
    metadata = _make_metadata(toy_contract, model_format="pytorch")
    with pytest.raises(ValueError, match="Nieznany model_format"):
        model_package.save_model_package(object(), metadata, tmp_path / "pkg")

    pkg_dir = tmp_path / "broken_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="Nieznany model_format"):
        model_package.load_model_package(pkg_dir)


def test_save_and_load_reject_invalid_metadata(tmp_path, toy_contract):
    bad_metadata = _make_metadata(toy_contract)
    del bad_metadata["git_sha"]

    with pytest.raises(ValueError, match="git_sha"):
        model_package.save_model_package(object(), bad_metadata, tmp_path / "pkg")

    pkg_dir = tmp_path / "invalid_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "metadata.json").write_text(json.dumps(bad_metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="git_sha"):
        model_package.load_model_package(pkg_dir)


def test_load_raises_when_sklearn_model_file_missing(tmp_path, toy_contract):
    pkg_dir = tmp_path / "missing_model"
    pkg_dir.mkdir()
    metadata = _make_metadata(toy_contract, model_format="sklearn-joblib")
    (pkg_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="model.joblib"):
        model_package.load_model_package(pkg_dir)


def test_load_raises_when_autogluon_model_dir_missing(tmp_path, toy_contract):
    pkg_dir = tmp_path / "missing_ag_dir"
    pkg_dir.mkdir()
    metadata = _make_metadata(toy_contract, model_format="autogluon")
    (pkg_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="model/"):
        model_package.load_model_package(pkg_dir)
