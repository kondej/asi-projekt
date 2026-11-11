from typing import Any

import pandas as pd

from asi_project.config import (
    ConfigError,
    DatasetContract,
    get_contract,
    load_project_config,
    load_registry,
)
from asi_project.data import (
    DataContractError,
    assert_valid,
    feature_list_problems,
    filter_training_rows,
    normalize_input,
)


def _resolve_contract(parameters: dict[str, Any]) -> DatasetContract:
    dataset_id = parameters.get("dataset")
    if isinstance(dataset_id, str) and dataset_id:
        registry = load_registry()
        if dataset_id not in registry:
            known = ", ".join(sorted(registry))
            raise ConfigError(f"Nieznany dataset '{dataset_id}'. Dozwolone: {known}.")
        return registry[dataset_id]

    config = load_project_config()
    return get_contract(config)


def _resolve_model_features(parameters: dict[str, Any]) -> list[str]:
    if parameters.get("model_features"):
        return list(parameters["model_features"])

    if "numeric_features" in parameters or "categorical_features" in parameters:
        numeric = parameters.get("numeric_features") or []
        categorical = parameters.get("categorical_features") or []
        return [*numeric, *categorical]

    features_cfg = parameters.get("features")
    if isinstance(features_cfg, dict):
        numeric = features_cfg.get("numeric") or []
        categorical = features_cfg.get("categorical") or []
        if numeric or categorical:
            return [*numeric, *categorical]

    config = load_project_config()
    return list(config.model_features)


def validate_raw_data(df: pd.DataFrame, parameters: dict[str, Any]) -> pd.DataFrame:
    contract = _resolve_contract(parameters)
    assert_valid(df, contract)

    model_features = _resolve_model_features(parameters)
    problems = feature_list_problems(contract, model_features)
    if problems:
        raise DataContractError("\n".join(problems))

    return df


def normalize_input_data(df: pd.DataFrame) -> pd.DataFrame:
    return normalize_input(df)


def filter_training_data(df: pd.DataFrame, parameters: dict[str, Any]) -> pd.DataFrame:
    contract = _resolve_contract(parameters)
    return filter_training_rows(df, contract)
