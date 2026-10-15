"""Testy projektu zespołu (Sprint 1): kontrakt danych, input normalization, baseline, metrics.json.

Testy sprawdzają efekty i kontrakty, a nie konkretny kod. Dopóki dany krok Sprintu 1 nie jest
wykonany, odpowiedni test jest pomijany z komunikatem, co zrobić. Naruszenie kontraktu
(np. kolumna EXCLUDED w X albo input normalization zależna od innych rekordów) to błąd.
"""

import numpy as np
import pandas as pd
import pytest

from asi_project.data import (
    DataContractError,
    feature_list_problems,
    filter_training_rows,
    label_text,
    make_xy,
    normalize_input,
    split_train_test,
    target_classes,
    validate,
)
from asi_project.metrics import load_metrics, validate_metrics_record
from asi_project.model import build_baseline_pipeline

MAX_ROWS_CHECKED = 200


def _require_features(project):
    if not project.config.features_declared:
        pytest.skip("S1: zadeklaruj typy cech (features) w project.yaml.")


def _training_data(project):
    data = filter_training_rows(normalize_input(project.sample), project.contract)
    X, y = make_xy(data, project.contract, project.config.model_features)
    return split_train_test(
        X,
        y,
        project.contract,
        test_size=project.config.test_size,
        random_state=project.config.random_state,
    )


def _fitted_pipeline(project):
    _require_features(project)
    try:
        pipeline = build_baseline_pipeline(
            list(project.config.numeric_features),
            list(project.config.categorical_features),
        )
    except NotImplementedError:
        pytest.skip("S1: zaimplementuj build_baseline_pipeline w src/asi_project/model.py.")
    X_train, X_test, y_train, _ = _training_data(project)
    pipeline.fit(X_train, y_train)
    return pipeline, X_test


# --- dane i kontrakt ---------------------------------------------------------------------------


def test_sample_has_exactly_two_classes_including_positive(project):
    classes = target_classes(project.sample[project.contract.target])
    assert len(classes) == 2, f"Target w próbce musi mieć dokładnie 2 klasy, ma: {classes}"
    assert label_text(project.contract.positive_class) in classes


def test_sample_satisfies_data_contract(project):
    problems = validate(normalize_input(project.sample), project.contract)
    assert problems == [], "\n".join(problems)


def test_feature_declarations_follow_contract(project):
    _require_features(project)
    config = project.config
    problems = feature_list_problems(project.contract, config.model_features)
    assert problems == [], "\n".join(problems)
    assert not set(config.numeric_features) & set(config.categorical_features)
    assert validate(normalize_input(project.sample), project.contract, config) == []


# --- input normalization i training-only filtering ---------------------------------------------


def test_input_normalization_works_on_single_records(project):
    sample = project.sample.head(MAX_ROWS_CHECKED)
    normalized = normalize_input(sample)
    for position in range(len(sample)):
        single = normalize_input(sample.iloc[[position]])
        pd.testing.assert_frame_equal(
            single,
            normalized.iloc[[position]],
            check_dtype=False,
            obj=f"input normalization dla rekordu {position}",
        )


def test_input_normalization_is_idempotent(project):
    once = normalize_input(project.sample)
    pd.testing.assert_frame_equal(normalize_input(once), once, check_dtype=False)


def test_input_normalization_does_not_depend_on_target(project):
    target = project.contract.target
    without_target = normalize_input(project.sample.drop(columns=target))
    with_target = normalize_input(project.sample).drop(columns=target)
    pd.testing.assert_frame_equal(without_target, with_target, check_dtype=False)


def test_training_filter_only_removes_records(project):
    normalized = normalize_input(project.sample)
    filtered = filter_training_rows(normalized, project.contract)
    assert len(filtered) <= len(normalized)
    assert set(filtered.index) <= set(normalized.index)
    assert list(filtered.columns) == list(normalized.columns)
    assert filtered[project.contract.target].notna().all()
    pd.testing.assert_frame_equal(
        filtered,
        normalized.loc[filtered.index],
        obj="training-only filtering może usuwać rekordy, ale nie zmieniać ich wartości",
    )


# --- X / y i baseline --------------------------------------------------------------------------


def test_model_input_contains_only_allowed_features(project):
    _require_features(project)
    data = filter_training_rows(normalize_input(project.sample), project.contract)
    X, y = make_xy(data, project.contract, project.config.model_features)
    assert set(X.columns) <= set(project.contract.allowed_features)
    assert not set(X.columns) & set(project.contract.excluded_features)
    assert set(y.unique()) == {0, 1}
    if project.contract.excluded_features:
        excluded = next(iter(project.contract.excluded_features))
        with pytest.raises(DataContractError):
            make_xy(data, project.contract, [*project.config.model_features, excluded])


def test_pipeline_predict_proba_for_binary_target(project):
    pipeline, X_test = _fitted_pipeline(project)
    assert hasattr(pipeline, "predict_proba")
    proba = pipeline.predict_proba(X_test)
    assert proba.shape == (len(X_test), 2)
    assert np.allclose(proba.sum(axis=1), 1.0)
    assert list(pipeline.classes_) == [0, 1]


def test_pipeline_uses_only_declared_features(project):
    pipeline, _ = _fitted_pipeline(project)
    assert set(pipeline.feature_names_in_) == set(project.config.model_features)


def test_pipeline_is_deterministic(project):
    first, X_test = _fitted_pipeline(project)
    second, _ = _fitted_pipeline(project)
    np.testing.assert_array_equal(first.predict_proba(X_test), second.predict_proba(X_test))


# --- metrics.json ------------------------------------------------------------------------------


def test_committed_metrics_json_follows_contract(project):
    if not project.config.metrics_path.is_file():
        pytest.skip("S1: brak metrics.json — uruchom notebook 02 na pełnych danych.")
    record = load_metrics(project.config.metrics_path)
    problems = validate_metrics_record(record, project.contract)
    assert problems == [], "\n".join(problems)
    assert record["data_mode"] == "full", "metrics.json w repo musi pochodzić z pełnych danych."
