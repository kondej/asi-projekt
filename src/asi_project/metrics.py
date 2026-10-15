"""Metryki baseline'u i kontrakt pliku metrics.json (artefakt Definition of Done Sprintu 1)."""

import json
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from asi_project.config import DatasetContract, ProjectConfig

SCHEMA_VERSION = 1
METRIC_NAMES = ("accuracy", "precision", "recall", "f1")
CONFUSION_KEYS = ("tn", "fp", "fn", "tp")
MODEL_KEYS = ("dummy", "logistic_regression")
DATA_MODES = ("full", "sample")


def compute_metrics(y_true: Sequence[int], y_pred: Sequence[int]) -> dict[str, Any]:
    """Metryki dla klasy pozytywnej = 1 oraz macierz pomyłek (tn, fp, fn, tp)."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def build_metrics_record(
    *,
    contract: DatasetContract,
    config: ProjectConfig,
    features: Sequence[str],
    n_train: int,
    n_test: int,
    data_mode: str,
    results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Składa rekord metrics.json w uzgodnionym formacie (``SCHEMA_VERSION``)."""
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset": contract.dataset_id,
        "target": contract.target,
        "positive_class": contract.positive_class,
        "data_mode": data_mode,
        "split": {
            "strategy": contract.split_strategy,
            "test_size": config.test_size,
            "random_state": config.random_state,
            "n_train": int(n_train),
            "n_test": int(n_test),
        },
        "features": [str(name) for name in features],
        "models": {name: results[name] for name in MODEL_KEYS if name in results},
    }


def _model_problems(name: str, model: Any, n_test: Any) -> list[str]:
    if not isinstance(model, dict):
        return [f"models.{name}: brak wyników."]
    problems = []
    for metric in METRIC_NAMES:
        value = model.get(metric)
        valid_number = isinstance(value, int | float) and not isinstance(value, bool)
        if not valid_number or math.isnan(value) or not 0.0 <= value <= 1.0:
            problems.append(f"models.{name}.{metric}: oczekiwana liczba z zakresu [0, 1].")
    matrix = model.get("confusion_matrix")
    if not isinstance(matrix, dict) or set(matrix) != set(CONFUSION_KEYS):
        return [*problems, f"models.{name}.confusion_matrix: oczekiwane klucze {CONFUSION_KEYS}."]
    counts = [matrix[key] for key in CONFUSION_KEYS]
    if not all(isinstance(count, int) and count >= 0 for count in counts):
        problems.append(f"models.{name}.confusion_matrix: liczności muszą być liczbami >= 0.")
    elif isinstance(n_test, int) and sum(counts) != n_test:
        problems.append(f"models.{name}.confusion_matrix: suma liczności różna od n_test.")
    return problems


def validate_metrics_record(
    record: dict[str, Any],
    contract: DatasetContract | None = None,
) -> list[str]:
    """Sprawdza kontrakt metrics.json. Zwraca listę problemów (pusta lista = OK)."""
    problems: list[str] = []
    if record.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version: oczekiwano {SCHEMA_VERSION}.")
    if record.get("data_mode") not in DATA_MODES:
        problems.append(f"data_mode: oczekiwano jednej z wartości {DATA_MODES}.")
    split = record.get("split")
    if not isinstance(split, dict):
        problems.append("split: brak opisu podziału danych.")
        split = {}
    n_test = split.get("n_test")
    for key in ("n_train", "n_test"):
        if not isinstance(split.get(key), int) or split.get(key) <= 0:
            problems.append(f"split.{key}: oczekiwana dodatnia liczba całkowita.")
    features = record.get("features")
    if not isinstance(features, list) or not features:
        problems.append("features: oczekiwana niepusta lista cech modelu.")
        features = []
    models = record.get("models")
    if not isinstance(models, dict):
        problems.append("models: brak wyników modeli.")
        models = {}
    for name in MODEL_KEYS:
        problems.extend(_model_problems(name, models.get(name), n_test))
    if contract is not None:
        expected = {
            "dataset": contract.dataset_id,
            "target": contract.target,
            "positive_class": contract.positive_class,
        }
        for key, value in expected.items():
            if record.get(key) != value:
                problems.append(f"{key}: oczekiwano {value!r}, jest {record.get(key)!r}.")
        if split.get("strategy") != contract.split_strategy:
            problems.append(f"split.strategy: oczekiwano {contract.split_strategy!r}.")
        not_allowed = [name for name in features if name not in contract.allowed_features]
        if not_allowed:
            problems.append(f"features: kolumny spoza ALLOWED FEATURES: {not_allowed}.")
    return problems


def save_metrics(
    record: dict[str, Any],
    path: Path | str,
    contract: DatasetContract | None = None,
) -> Path:
    """Zapisuje metrics.json po walidacji (JSON zakończony znakiem nowej linii)."""
    problems = validate_metrics_record(record, contract)
    if problems:
        raise ValueError("metrics.json nie spełnia kontraktu:\n" + "\n".join(problems))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_metrics(path: Path | str) -> dict[str, Any]:
    """Wczytuje metrics.json."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
