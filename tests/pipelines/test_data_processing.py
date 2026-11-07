from pathlib import Path

import pandas as pd
import pytest

from asi_project.config import load_registry
from asi_project.data import DataContractError
from asi_project.pipelines.data_processing.nodes import (
    filter_training_data,
    normalize_input_data,
    validate_raw_data,
)
from asi_project.pipelines.data_processing.pipeline import create_pipeline


@pytest.fixture
def parameters() -> dict:
    contract = load_registry()["online_shoppers"]
    return {
        "dataset": "online_shoppers",
        "model_features": list(contract.allowed_features),
    }


@pytest.fixture
def sample_df() -> pd.DataFrame:
    sample_path = Path("data/01_raw/sample.csv")
    return pd.read_csv(sample_path)


def test_validate_raw_data_raises_on_missing_target(
    sample_df: pd.DataFrame, parameters: dict
) -> None:
    df_without_target = sample_df.drop(columns=["Revenue"])
    with pytest.raises(DataContractError, match="Brak wymaganych kolumn"):
        validate_raw_data(df_without_target, parameters)


def test_normalize_input_data_is_idempotent(sample_df: pd.DataFrame) -> None:
    df = sample_df.copy()
    df.loc[df.index[0], "Month"] = "June"
    df.loc[df.index[0], "VisitorType"] = " Returning_Visitor "

    once = normalize_input_data(df)
    twice = normalize_input_data(once)

    pd.testing.assert_frame_equal(once, twice)
    assert once.loc[df.index[0], "Month"] == "Jun"
    assert once.loc[df.index[0], "VisitorType"] == "Returning_Visitor"


def test_filter_training_data_removes_missing_target_and_duplicates(
    sample_df: pd.DataFrame, parameters: dict
) -> None:
    df = sample_df.iloc[:10].copy()
    row_missing_target = df.iloc[[0]].copy()
    row_missing_target["Revenue"] = None
    row_duplicate = df.iloc[[0]].copy()

    dirty_df = pd.concat([df, row_missing_target, row_duplicate], ignore_index=True)
    filtered = filter_training_data(dirty_df, parameters)

    assert filtered["Revenue"].isna().sum() == 0
    assert not filtered.duplicated().any()
    assert len(filtered) == len(df.drop_duplicates())


def test_full_data_processing_on_ci_sample(
    sample_df: pd.DataFrame, parameters: dict
) -> None:
    validated = validate_raw_data(sample_df, parameters)
    normalized = normalize_input_data(validated)
    training = filter_training_data(normalized, parameters)

    assert len(training) > 0
    assert len(training) <= len(sample_df)
    assert training["Revenue"].notna().all()
    assert not training.duplicated().any()


def test_create_pipeline_structure() -> None:
    dp_pipeline = create_pipeline()
    node_names = [n.name for n in dp_pipeline.nodes]
    assert node_names == [
        "validate_raw_data_node",
        "normalize_input_data_node",
        "filter_training_data_node",
    ]