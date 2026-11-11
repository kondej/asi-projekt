"""Testy nodów pipeline'u data_science (na próbce CI, bez uruchamiania Kedro)."""

import pytest

from asi_project.config import ConfigError
from asi_project.data import filter_training_rows, normalize_input
from asi_project.metrics import MODEL_KEYS, validate_metrics_record
from asi_project.pipelines.data_science.nodes import (
    evaluate_models,
    make_features_target,
    split_data,
    train_models,
)
from asi_project.pipelines.data_science.pipeline import create_pipeline


@pytest.fixture
def training_data(project):
    """Dane po data_processing: input normalization, a potem training-only filtering."""
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
    """Wynik node'a ewaluacji razem z danymi, na których powstał."""
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


def test_pipeline_uses_agreed_dataset_and_parameter_names():
    pipeline = create_pipeline()

    assert pipeline.inputs() == {
        "training_data",
        "params:dataset",
        "params:features",
        "params:split",
        "params:data_mode",
    }
    assert {"X_train", "X_test", "y_train", "y_test", "model", "dummy_model", "metrics"} <= (
        pipeline.all_outputs()
    )
