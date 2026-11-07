"""Nody pipeline'u data_science (Sprint 2).

Każdy node to czysta funkcja: dostaje dane i parametry z argumentów, nie zna ścieżek do plików.
Logika przetwarzania zostaje w ``asi_project.data``, ``asi_project.model`` i
``asi_project.metrics`` — nody tylko ją wywołują.
"""

from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import Any

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline

from asi_project.config import ConfigError, DatasetContract, load_registry
from asi_project.data import make_xy, split_train_test
from asi_project.metrics import build_metrics_record, compute_metrics, validate_metrics_record
from asi_project.model import build_baseline_pipeline, make_dummy


def get_dataset_contract(dataset: str) -> DatasetContract:
    """Kontrakt datasetu o danym id z rejestru prowadzącej (``datasets.yaml``)."""
    registry = load_registry()
    if dataset not in registry:
        known = ", ".join(sorted(registry))
        raise ConfigError(f"Nieznany dataset '{dataset}'. Dozwolone: {known}.")
    return registry[dataset]


def model_feature_names(features: Mapping[str, Sequence[str]]) -> list[str]:
    """Cechy modelu w ustalonej kolejności: najpierw numeryczne, potem kategoryczne."""
    return [*features["numeric"], *features["categorical"]]


def make_features_target(
    training_data: pd.DataFrame,
    dataset: str,
    features: Mapping[str, Sequence[str]],
) -> tuple[pd.DataFrame, pd.Series]:
    """``training_data`` -> ``X`` (tylko zadeklarowane ALLOWED FEATURES) i ``y`` (0/1)."""
    contract = get_dataset_contract(dataset)
    return make_xy(training_data, contract, model_feature_names(features))


def split_data(
    X: pd.DataFrame,
    y: pd.Series,
    dataset: str,
    split: Mapping[str, float | int],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """``X``, ``y`` -> ``X_train``, ``X_test``, ``y_train``, ``y_test``.

    Strategia splitu pochodzi z kontraktu datasetu, a ``test_size`` i ``random_state``
    z parametrów (``params:split``).
    """
    contract = get_dataset_contract(dataset)
    return split_train_test(
        X,
        y,
        contract,
        test_size=split["test_size"],
        random_state=split["random_state"],
    )


def train_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    features: Mapping[str, Sequence[str]],
) -> tuple[Pipeline, DummyClassifier]:
    """``X_train``, ``y_train`` -> ``model`` (sklearn Pipeline) i ``dummy_model``.

    Model preprocessing (imputacja, skalowanie, kodowanie) jest wewnątrz sklearn Pipeline,
    więc uczy się wyłącznie na ``X_train`` i jest zapisywany razem z modelem.
    """
    model = build_baseline_pipeline(features["numeric"], features["categorical"])
    model.fit(X_train, y_train)
    dummy_model = make_dummy()
    dummy_model.fit(X_train, y_train)
    return model, dummy_model


def evaluate_models(
    model: Pipeline,
    dummy_model: DummyClassifier,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    dataset: str,
    features: Mapping[str, Sequence[str]],
    split: Mapping[str, float | int],
    data_mode: str,
) -> dict[str, Any]:
    """Modele i ``X_test``, ``y_test`` -> ``metrics`` w formacie ``metrics.json`` ze Sprintu 1.

    Metryki liczy ``compute_metrics``, rekord składa ``build_metrics_record`` (klucze ``dummy``
    i ``logistic_regression``), a ``validate_metrics_record`` pilnuje kontraktu pliku.
    """
    contract = get_dataset_contract(dataset)
    results = {
        "dummy": compute_metrics(y_test, dummy_model.predict(X_test)),
        "logistic_regression": compute_metrics(y_test, model.predict(X_test)),
    }
    # build_metrics_record czyta z config tylko test_size i random_state; bierzemy je
    # z parametrów Kedro zamiast z project.yaml.
    split_config = SimpleNamespace(
        test_size=split["test_size"],
        random_state=split["random_state"],
    )
    record = build_metrics_record(
        contract=contract,
        config=split_config,
        features=model_feature_names(features),
        n_train=len(X_train),
        n_test=len(X_test),
        data_mode=data_mode,
        results=results,
    )
    problems = validate_metrics_record(record, contract)
    if problems:
        raise ValueError("metrics nie spełniają kontraktu:\n" + "\n".join(problems))
    return record
