import sys
from pathlib import Path
from types import ModuleType

import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier

from asi_project.config import ConfigError
from asi_project.data import filter_training_rows, normalize_input
from asi_project.metrics import MODEL_KEYS, validate_metrics_record
from asi_project.model_metadata import validate_metadata
from asi_project.model_package import (
    METADATA_FILENAME,
    MODEL_FORMAT_SKLEARN,
    SKLEARN_MODEL_FILENAME,
    load_model_package,
)
from asi_project.pipelines.data_science.nodes import (
    build_model_package,
    evaluate_models,
    make_features_target,
    run_experiments,
    split_data,
    train_models,
)
from asi_project.pipelines.data_science.pipeline import create_pipeline


@pytest.fixture
def training_data(project):
    return filter_training_rows(normalize_input(project.sample), project.contract)


@pytest.fixture
def features(project):
    return {
        "numeric": list(project.config.numeric_features),
        "categorical": list(project.config.categorical_features),
    }


@pytest.fixture
def xy(project, training_data, features):
    return make_features_target(training_data, project.config.dataset_id, features)


@pytest.fixture
def split_params(project):
    return {
        "test_size": project.config.test_size,
        "random_state": project.config.random_state,
    }


@pytest.fixture
def train_test(project, xy, split_params):
    X, y = xy
    return split_data(X, y, project.config.dataset_id, split_params)


@pytest.fixture
def evaluation(project, train_test, features, split_params):
    X_train, X_test, y_train, y_test = train_test
    model, dummy_model = train_models(X_train, y_train, features)
    metrics = evaluate_models(
        model,
        dummy_model,
        X_train,
        X_test,
        y_test,
        project.config.dataset_id,
        features,
        split_params,
        "sample",
    )
    return metrics, train_test


def test_make_features_target_returns_only_declared_features(project, training_data, features):
    X, y = make_features_target(training_data, project.config.dataset_id, features)

    assert list(X.columns) == [*features["numeric"], *features["categorical"]]
    assert project.contract.target not in X.columns
    assert not set(X.columns) & set(project.contract.excluded_features)
    assert len(X) == len(y) == len(training_data)


def test_make_features_target_encodes_binary_target(project, training_data, features):
    _, y = make_features_target(training_data, project.config.dataset_id, features)

    assert set(y.unique()) == {0, 1}


def test_make_features_target_rejects_unknown_dataset(training_data, features):
    with pytest.raises(ConfigError):
        make_features_target(training_data, "nie_ma_takiego_datasetu", features)


def test_split_data_has_correct_structure(project, xy, split_params):
    X, y = xy
    X_train, X_test, y_train, y_test = split_data(X, y, project.config.dataset_id, split_params)

    assert len(X_train) == len(y_train)
    assert len(X_test) == len(y_test)
    assert len(X_train) + len(X_test) == len(X)
    assert len(X_test) == pytest.approx(len(X) * split_params["test_size"], abs=1)
    assert list(X_train.columns) == list(X_test.columns) == list(X.columns)
    assert not set(X_train.index) & set(X_test.index)


def test_split_data_keeps_both_classes_in_train_and_test(project, xy, split_params):
    X, y = xy
    _, _, y_train, y_test = split_data(X, y, project.config.dataset_id, split_params)

    assert set(y_train.unique()) == {0, 1}
    assert set(y_test.unique()) == {0, 1}


def test_split_data_is_reproducible_and_uses_random_state(project, xy, split_params):
    X, y = xy
    dataset = project.config.dataset_id
    first = split_data(X, y, dataset, split_params)
    again = split_data(X, y, dataset, split_params)
    other = split_data(X, y, dataset, {**split_params, "random_state": 7})

    assert first[1].index.equals(again[1].index)
    assert not first[1].index.equals(other[1].index)


def test_train_models_returns_fitted_model_with_predict_proba(train_test, features):
    X_train, X_test, y_train, _ = train_test
    model, _ = train_models(X_train, y_train, features)

    proba = model.predict_proba(X_test)

    assert proba.shape == (len(X_test), 2)
    assert ((proba >= 0) & (proba <= 1)).all()


def test_train_models_keeps_model_preprocessing_inside_sklearn_pipeline(train_test, features):
    X_train, _, y_train, _ = train_test
    model, _ = train_models(X_train, y_train, features)

    assert list(model.named_steps) == ["preprocessing", "model"]


def test_train_models_dummy_predicts_most_frequent_class(train_test, features):
    X_train, X_test, y_train, _ = train_test
    _, dummy_model = train_models(X_train, y_train, features)

    assert set(dummy_model.predict(X_test)) == {y_train.value_counts().idxmax()}


def test_evaluate_models_returns_valid_metrics_record(project, evaluation):
    metrics, _ = evaluation

    assert set(metrics["models"]) == set(MODEL_KEYS)
    assert validate_metrics_record(metrics, project.contract) == []


def test_evaluate_models_describes_split_and_data_mode(project, evaluation, split_params):
    metrics, (X_train, X_test, _, _) = evaluation

    assert metrics["data_mode"] == "sample"
    assert metrics["split"]["n_train"] == len(X_train)
    assert metrics["split"]["n_test"] == len(X_test)
    assert metrics["split"]["test_size"] == split_params["test_size"]
    assert metrics["split"]["random_state"] == split_params["random_state"]


def test_evaluate_models_rejects_unknown_data_mode(project, train_test, features, split_params):
    X_train, X_test, y_train, y_test = train_test
    model, dummy_model = train_models(X_train, y_train, features)

    with pytest.raises(ValueError, match="data_mode"):
        evaluate_models(
            model,
            dummy_model,
            X_train,
            X_test,
            y_test,
            project.config.dataset_id,
            features,
            split_params,
            "nieznany",
        )


def test_build_model_package_saves_toy_model_and_valid_metadata(project, features, tmp_path):
    toy_model = DummyClassifier(strategy="most_frequent").fit([[0], [1], [1]], [0, 1, 1])
    metrics = {
        "models": {
            "logistic_regression": {
                "accuracy": 0.75,
                "precision": 0.8,
                "recall": 0.7,
                "f1": 0.74,
            }
        }
    }
    package_dir = tmp_path / "model_package"

    metadata = build_model_package(
        model=toy_model,
        metrics=metrics,
        dataset=project.config.dataset_id,
        features=features,
        data_mode="sample",
        package_path=package_dir,
    )

    assert (package_dir / SKLEARN_MODEL_FILENAME).is_file()
    assert (package_dir / METADATA_FILENAME).is_file()
    assert validate_metadata(metadata, project.contract) == []

    loaded = load_model_package(package_dir, contract=project.contract)
    assert loaded.metadata["model_name"] == "logistic_regression"
    assert loaded.metadata["model_format"] == MODEL_FORMAT_SKLEARN
    assert list(loaded.model.predict([[0], [1]])) == [1, 1]


def test_run_experiments_returns_empty_table_when_disabled(project, evaluation, features):
    metrics, (X_train, X_test, y_train, y_test) = evaluation
    model, _ = train_models(X_train, y_train, features)

    table = run_experiments(
        model=model,
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        metrics=metrics,
        dataset=project.config.dataset_id,
        features=features,
        data_mode="sample",
        experiments={"enabled": False},
    )

    assert table.empty
    assert {"model_name", "model_format", "f1", "predict_time_ms", "package_size_kb"} <= set(
        table.columns
    )


def test_run_experiments_compares_baseline_and_autogluon_with_mocks(
    project, evaluation, features, monkeypatch, tmp_path
):
    metrics, (X_train, X_test, y_train, y_test) = evaluation
    model, _ = train_models(X_train, y_train, features)

    logged_runs = []

    class FakeRun:
        def __init__(self, kwargs):
            self.kwargs = kwargs
            self.logged = {}

        def log(self, payload):
            self.logged.update(payload)

        def finish(self):
            logged_runs.append({"init": self.kwargs, "log": self.logged})

    fake_wandb = ModuleType("wandb")
    fake_wandb.init = lambda **kwargs: FakeRun(kwargs)
    monkeypatch.setitem(sys.modules, "wandb", fake_wandb)
    monkeypatch.delenv("WANDB_MODE", raising=False)

    class FakePredictor:
        def __init__(self, label, problem_type, eval_metric, path, verbosity=0):
            self.label = label
            self.path = str(path)

        def fit(self, train_df, **kwargs):
            target = Path(self.path)
            target.mkdir(parents=True, exist_ok=True)
            (target / "predictor.pkl").write_text("fake", encoding="utf-8")
            return self

        def clone(self, target_path, *, dirs_exist_ok=False):
            target = Path(target_path)
            target.mkdir(parents=True, exist_ok=dirs_exist_ok)
            (target / "predictor.pkl").write_text("cloned", encoding="utf-8")
            return target_path

        @classmethod
        def load(cls, path):
            return cls("Revenue", "binary", "f1", path)

        def predict(self, df):
            return pd.Series([0] * len(df), index=df.index)

        def predict_proba(self, df):
            return pd.DataFrame({0: [0.8] * len(df), 1: [0.2] * len(df)}, index=df.index)

    fake_ag = ModuleType("autogluon")
    fake_tabular = ModuleType("autogluon.tabular")
    fake_tabular.TabularPredictor = FakePredictor
    monkeypatch.setitem(sys.modules, "autogluon", fake_ag)
    monkeypatch.setitem(sys.modules, "autogluon.tabular", fake_tabular)

    pkg_dir = tmp_path / "model_package"
    pkg_dir.mkdir()
    (pkg_dir / SKLEARN_MODEL_FILENAME).write_text("stale", encoding="utf-8")
    production_model = {"name": "ag_fast", "format": "autogluon"}

    table = run_experiments(
        model=model,
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        metrics=metrics,
        dataset=project.config.dataset_id,
        features=features,
        data_mode="sample",
        experiments={
            "enabled": True,
            "wandb_enabled": True,
            "wandb_project": "asi-test",
            "autogluon_configs": {
                "ag_fast": {"time_limit": 10, "presets": "medium_quality"},
            },
        },
        package_path=pkg_dir,
        production_model=production_model,
    )
    metadata = build_model_package(
        model=model,
        metrics=metrics,
        dataset=project.config.dataset_id,
        features=features,
        data_mode="sample",
        package_path=pkg_dir,
        production_model=production_model,
        experiment_comparison=table,
    )

    assert list(table["model_name"]) == ["logistic_regression", "ag_fast"]
    assert list(table["model_format"]) == ["sklearn-joblib", "autogluon"]
    assert (table["package_size_kb"] > 0).all()
    assert (table["predict_time_ms"] >= 0).all()
    assert not (pkg_dir / SKLEARN_MODEL_FILENAME).exists()
    assert (pkg_dir / "model" / "predictor.pkl").is_file()
    assert metadata["model_name"] == "ag_fast"
    assert metadata["model_format"] == "autogluon"
    assert len(logged_runs) == 2
    assert {run["init"]["config"]["model_name"] for run in logged_runs} == {
        "logistic_regression",
        "ag_fast",
    }
    assert all("git_sha" in run["init"]["config"] for run in logged_runs)
    assert all("data_fingerprint" in run["init"]["config"] for run in logged_runs)


def test_pipeline_uses_agreed_dataset_and_parameter_names():
    pipeline = create_pipeline()

    assert pipeline.inputs() == {
        "training_data",
        "params:dataset",
        "params:features",
        "params:split",
        "params:data_mode",
        "params:model_package_path",
        "params:experiments",
        "params:production_model",
    }
    assert {
        "X_train",
        "X_test",
        "y_train",
        "y_test",
        "model",
        "dummy_model",
        "metrics",
        "model_package_metadata",
        "experiment_comparison",
    } <= pipeline.all_outputs()
