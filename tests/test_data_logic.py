"""Logika kontraktu danych na danych syntetycznych (niezależna od wybranego datasetu)."""

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from asi_project.data import (
    DataContractError,
    encode_target,
    feature_list_problems,
    filter_training_rows,
    make_xy,
    normalize_column_names,
    normalize_input,
    sample_rows,
    split_train_test,
    target_classes,
    validate,
)


def test_encode_target_handles_common_label_types():
    assert encode_target(pd.Series(["yes", "no", " YES "]), "yes").tolist() == [1, 0, 1]
    assert encode_target(pd.Series([1, 0, 1]), "1").tolist() == [1, 0, 1]
    assert encode_target(pd.Series([1.0, 0.0]), "1").tolist() == [1, 0]
    assert encode_target(pd.Series([True, False]), "true").tolist() == [1, 0]
    assert encode_target(pd.Series(["TRUE", "FALSE"]), "true").tolist() == [1, 0]


def test_encode_target_rejects_missing_and_multiclass():
    with pytest.raises(DataContractError):
        encode_target(pd.Series(["yes", None]), "yes")
    with pytest.raises(DataContractError):
        encode_target(pd.Series(["a", "b", "c"]), "a")


def test_validate_accepts_valid_frame(toy_contract, toy_frame):
    assert validate(toy_frame, toy_contract) == []


def test_validate_reports_contract_violations(toy_contract, toy_frame):
    missing_column = toy_frame.drop(columns="cat")
    assert any("cat" in problem for problem in validate(missing_column, toy_contract))
    three_classes = toy_frame.assign(label=["yes", "no", "maybe", "no"] * 10)
    assert any("2 klasy" in problem for problem in validate(three_classes, toy_contract))
    no_positive = toy_frame.assign(label="no")
    assert validate(no_positive, toy_contract)


def test_feature_list_problems_blocks_excluded_target_and_unknown(toy_contract):
    assert feature_list_problems(toy_contract, ["num", "cat"]) == []
    assert feature_list_problems(toy_contract, [])
    assert any("EXCLUDED" in p for p in feature_list_problems(toy_contract, ["num", "leak"]))
    assert feature_list_problems(toy_contract, ["num", "label"])
    assert feature_list_problems(toy_contract, ["num", "unknown"])
    assert feature_list_problems(toy_contract, ["num", "num"])


def test_make_xy_returns_only_requested_allowed_features(toy_contract, toy_frame):
    X, y = make_xy(toy_frame, toy_contract, ["num", "cat"])
    assert list(X.columns) == ["num", "cat"]
    assert set(y.unique()) == {0, 1}
    with pytest.raises(DataContractError):
        make_xy(toy_frame, toy_contract, ["num", "leak"])


def test_stratified_split_keeps_both_classes(toy_contract, toy_frame):
    X, y = make_xy(toy_frame, toy_contract, ["num"])
    X_train, X_test, y_train, y_test = split_train_test(X, y, toy_contract, 0.25, 0)
    assert len(X_test) == 10 and len(X_train) == 30
    assert y_test.sum() >= 1 and y_train.sum() >= 1


def test_time_ordered_split_keeps_order(toy_contract, toy_frame):
    ordered = replace(toy_contract, split_strategy="time_ordered")
    X, y = make_xy(toy_frame, ordered, ["num"])
    X_train, X_test, _, _ = split_train_test(X, y, ordered, 0.25, 0)
    assert X_train.index.max() < X_test.index.min()
    assert list(X_test.index) == sorted(X_test.index)


def test_default_input_normalization_rules_and_idempotence(toy_frame):
    normalized = normalize_input(toy_frame)
    assert normalized["cat"].tolist()[:2] == ["a", "b"]
    assert pd.isna(normalized["cat"].iloc[2])
    assert normalized["num"].equals(toy_frame["num"])
    pd.testing.assert_frame_equal(normalize_input(normalized), normalized)


def test_filter_training_rows_only_removes_rows(toy_contract, toy_frame):
    with_missing = toy_frame.copy()
    with_missing.loc[3, "label"] = np.nan
    filtered = filter_training_rows(with_missing, toy_contract)
    assert len(filtered) == len(toy_frame) - 1
    assert set(filtered.index) <= set(with_missing.index)
    assert list(filtered.columns) == list(with_missing.columns)
    pd.testing.assert_frame_equal(filtered, with_missing.loc[filtered.index])


def test_sample_rows_keeps_order_and_minimum_positives(toy_frame):
    y = (toy_frame["label"] == "yes").astype(int)
    sample = sample_rows(toy_frame, y, n_rows=12, min_positive=5, seed=0)
    assert len(sample) == 12
    assert list(sample.index) == sorted(sample.index)
    assert int((sample["label"] == "yes").sum()) >= 5


def test_column_names_and_target_classes():
    frame = normalize_column_names(pd.DataFrame(columns=["Call  Failure", " Age "]))
    assert list(frame.columns) == ["Call Failure", "Age"]
    assert target_classes(pd.Series([1, 0, 1.0, None])) == ["0", "1"]
