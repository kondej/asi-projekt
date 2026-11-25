import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import pandas as pd
import pytest

from asi_project import model_metadata, model_package
from asi_project.data import encode_target, filter_training_rows, make_xy, normalize_input
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
    saved_path = model_package.save_model_package(
        model, metadata, package_dir, contract=toy_contract
    )

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


def test_predict_from_package_sklearn_normalizes_reorders_and_drops_extra(
    tmp_path, toy_contract, toy_frame
):
    features = {"numeric": ["num"], "categorical": ["cat"]}
    clean = normalize_input(toy_frame)
    X = clean[["num", "cat"]]
    y = encode_target(clean["label"], toy_contract.positive_class)

    model = build_baseline_pipeline(features["numeric"], features["categorical"])
    model.fit(X, y)

    metadata = _make_metadata(toy_contract, model_format="sklearn-joblib")
    pkg_dir = model_package.save_model_package(
        model, metadata, tmp_path / "pkg", contract=toy_contract
    )
    loaded = model_package.load_model_package(pkg_dir, contract=toy_contract)

    raw_input = pd.DataFrame(
        {
            "extra_col": [999, 888, 777],
            "cat": [" a ", "  b", ""],
            "num": [0.0, 1.0, 2.0],
            "label": ["yes", "no", "no"],
        },
        index=[10, 20, 30],
    )
    out = model_package.predict_from_package(loaded, raw_input)

    model_package.validate_prediction_output(out, len(raw_input))
    assert list(out.index) == [10, 20, 30]
    expected_X = normalize_input(raw_input[["num", "cat"]])
    np.testing.assert_allclose(out["probability"], model.predict_proba(expected_X)[:, 1])
    np.testing.assert_array_equal(out["prediction"], model.predict(expected_X))


def test_predict_from_package_sample_five_rows(tmp_path, project):
    config, contract, sample = project.config, project.contract, project.sample
    df_train = filter_training_rows(normalize_input(sample), contract)
    features = {
        "numeric": list(config.numeric_features),
        "categorical": list(config.categorical_features),
    }
    X, y = make_xy(df_train, contract, config.model_features)

    model = build_baseline_pipeline(features["numeric"], features["categorical"])
    model.fit(X, y)
    metrics = compute_metrics(y, model.predict(X))
    metadata = model_metadata.build_metadata(
        contract=contract,
        features=features,
        metrics=metrics,
        model_format="sklearn-joblib",
        model_name="baseline",
        data_fingerprint="sample",
        git_sha="deadbeef",
        library_versions={"python": "3.11"},
    )

    pkg_dir = model_package.save_model_package(
        model, metadata, tmp_path / "sample_pkg", contract=contract
    )
    loaded = model_package.load_model_package(pkg_dir, contract=contract)

    five_rows = sample.head(5)
    out = model_package.predict_from_package(loaded, five_rows)
    model_package.validate_prediction_output(out, 5)


def test_predict_from_package_autogluon_positive_class(tmp_path, toy_contract):
    class FakeAG:
        def predict_proba(self, df: pd.DataFrame) -> pd.DataFrame:
            return pd.DataFrame({"no": [0.8, 0.2], "yes": [0.2, 0.8]}, index=df.index)

        def predict(self, df: pd.DataFrame) -> pd.Series:
            return pd.Series(["no", "yes"], index=df.index)

    metadata = _make_metadata(toy_contract, model_format="autogluon", model_name="ag_fast")
    pkg = model_package.ModelPackage(model=FakeAG(), metadata=metadata, path=tmp_path)
    df_in = pd.DataFrame({"cat": ["a", "b"], "num": [1.0, 2.0]})

    out = model_package.predict_from_package(pkg, df_in)
    model_package.validate_prediction_output(out, 2)
    assert list(out["prediction"]) == [0, 1]
    np.testing.assert_allclose(out["probability"], [0.2, 0.8])


def test_predict_from_package_raises_on_missing_feature(tmp_path, toy_contract, toy_frame):
    features = {"numeric": ["num"], "categorical": ["cat"]}
    clean = normalize_input(toy_frame)
    model = build_baseline_pipeline(features["numeric"], features["categorical"])
    model.fit(clean[["num", "cat"]], encode_target(clean["label"], toy_contract.positive_class))
    metadata = _make_metadata(toy_contract)
    pkg = model_package.ModelPackage(model=model, metadata=metadata, path=tmp_path)

    with pytest.raises(ValueError, match="cat"):
        model_package.predict_from_package(pkg, pd.DataFrame({"num": [1.0, 2.0]}))


@pytest.mark.parametrize(
    "bad_df,n_rows",
    [
        (pd.DataFrame({"pred": [0, 1], "probability": [0.1, 0.9]}), 2),
        (pd.DataFrame({"prediction": [0, 1], "probability": [0.1, 0.9]}), 3),
        (pd.DataFrame({"prediction": [0.0, 1.0], "probability": [0.1, 0.9]}), 2),
        (pd.DataFrame({"prediction": [0, 2], "probability": [0.1, 0.9]}), 2),
        (pd.DataFrame({"prediction": [0, 1], "probability": [0.1, 1.2]}), 2),
        (pd.DataFrame({"prediction": [0, 1], "probability": [-0.1, 0.9]}), 2),
        (pd.DataFrame({"prediction": [0, 1], "probability": [0.1, np.nan]}), 2),
    ],
)
def test_validate_prediction_output_rejects_invalid(bad_df, n_rows):
    with pytest.raises(ValueError):
        model_package.validate_prediction_output(bad_df, n_rows)


_FRESH_PROCESS_SCRIPT = """
import json
import sys

import pandas as pd

from asi_project.model_package import (
    load_model_package,
    predict_from_package,
    validate_prediction_output,
)

package_dir, sample_path = sys.argv[1], sys.argv[2]
package = load_model_package(package_dir)
rows = pd.read_csv(sample_path).head(5)
out = predict_from_package(package, rows)
validate_prediction_output(out, 5)
banned = sorted(name for name in ("wandb", "autogluon") if name in sys.modules)
print(json.dumps({"predictions": out.to_dict(orient="list"), "banned_modules": banned}))
"""


def test_package_roundtrip_in_fresh_process(tmp_path, project):
    """Zapis w tym procesie, odczyt i predykcja w świeżym procesie (bez W&B i bez fit)."""
    config, contract, sample = project.config, project.contract, project.sample
    features = {
        "numeric": list(config.numeric_features),
        "categorical": list(config.categorical_features),
    }
    df_train = filter_training_rows(normalize_input(sample), contract)
    X, y = make_xy(df_train, contract, config.model_features)
    model = build_baseline_pipeline(features["numeric"], features["categorical"])
    model.fit(X, y)
    metadata = model_metadata.build_metadata(
        contract=contract,
        features=features,
        metrics=compute_metrics(y, model.predict(X)),
        model_format="sklearn-joblib",
        model_name="baseline",
        data_fingerprint="sample",
        git_sha="deadbeef",
        library_versions={"python": "3.11"},
    )
    pkg_dir = model_package.save_model_package(
        model, metadata, tmp_path / "fresh_pkg", contract=contract
    )
    expected = model_package.predict_from_package(
        model_package.load_model_package(pkg_dir, contract=contract), sample.head(5)
    )

    src_dir = Path(model_package.__file__).resolve().parents[1]
    env = {
        **os.environ,
        "WANDB_MODE": "disabled",
        "PYTHONPATH": os.pathsep.join(filter(None, [str(src_dir), os.environ.get("PYTHONPATH")])),
    }
    result = subprocess.run(
        [sys.executable, "-c", _FRESH_PROCESS_SCRIPT, str(pkg_dir), str(config.ci_sample_path)],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout.strip().splitlines()[-1])
    assert report["banned_modules"] == []
    assert report["predictions"]["prediction"] == expected["prediction"].tolist()
    np.testing.assert_allclose(report["predictions"]["probability"], expected["probability"])
