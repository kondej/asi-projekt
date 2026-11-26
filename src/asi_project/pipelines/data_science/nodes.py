import os
import shutil
import statistics
import tempfile
import time
import tracemalloc
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline

from asi_project.config import ConfigError, DatasetContract, load_project_config, load_registry
from asi_project.data import make_xy, split_train_test
from asi_project.metrics import build_metrics_record, compute_metrics, validate_metrics_record
from asi_project.model import build_baseline_pipeline, make_dummy
from asi_project.model_metadata import (
    build_metadata,
    get_data_fingerprint,
    get_git_sha,
    get_library_versions,
)
from asi_project.model_package import (
    AUTOGLUON_MODEL_DIRNAME,
    MODEL_FORMAT_AUTOGLUON,
    MODEL_FORMAT_SKLEARN,
    SKLEARN_MODEL_FILENAME,
    load_model_package,
    predict_from_package,
    save_model_package,
)


def get_dataset_contract(dataset: str) -> DatasetContract:
    registry = load_registry()
    if dataset not in registry:
        known = ", ".join(sorted(registry))
        raise ConfigError(f"Nieznany dataset '{dataset}'. Dozwolone: {known}.")
    return registry[dataset]


def model_feature_names(features: Mapping[str, Sequence[str]]) -> list[str]:
    return [*features["numeric"], *features["categorical"]]


def make_features_target(
    training_data: pd.DataFrame,
    dataset: str,
    features: Mapping[str, Sequence[str]],
) -> tuple[pd.DataFrame, pd.Series]:
    contract = get_dataset_contract(dataset)
    return make_xy(training_data, contract, model_feature_names(features))


def split_data(
    X: pd.DataFrame,
    y: pd.Series,
    dataset: str,
    split: Mapping[str, float | int],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
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


def _extract_model_metrics(metrics: Mapping[str, Any], model_name: str) -> Mapping[str, Any]:
    models = metrics.get("models")
    if isinstance(models, Mapping) and model_name in models:
        return models[model_name]
    if model_name in metrics and isinstance(metrics[model_name], Mapping):
        return metrics[model_name]
    return metrics


def _clear_package_model_artifacts(package_dir: Path) -> None:
    joblib_file = package_dir / SKLEARN_MODEL_FILENAME
    if joblib_file.is_file():
        joblib_file.unlink()
    ag_dir = package_dir / AUTOGLUON_MODEL_DIRNAME
    if ag_dir.is_dir():
        shutil.rmtree(ag_dir)


def build_model_package(
    model: Any,
    metrics: Mapping[str, Any],
    dataset: str,
    features: Mapping[str, Sequence[str]],
    data_mode: str,
    package_path: str | Path,
    production_model: Mapping[str, Any] | None = None,
    experiment_comparison: pd.DataFrame | None = None,
    model_name: str = "logistic_regression",
    model_format: str = MODEL_FORMAT_SKLEARN,
) -> dict[str, Any]:
    del experiment_comparison  # wymusza kolejność po run_experiments w DAG Kedro
    contract = get_dataset_contract(dataset)
    selected_name = (
        str(production_model.get("name", model_name)) if production_model else model_name
    )
    selected_format = (
        str(production_model.get("format", model_format)) if production_model else model_format
    )
    package_dir = Path(package_path)

    if selected_format == MODEL_FORMAT_AUTOGLUON:
        package = load_model_package(package_dir, contract=contract)
        if package.metadata.get("model_name") != selected_name:
            raise ValueError(
                f"Oczekiwano pakietu modelu '{selected_name}', "
                f"ale w {package_dir} zapisano '{package.metadata.get('model_name')}'."
            )
        return package.metadata

    config = load_project_config()
    model_metrics = _extract_model_metrics(metrics, selected_name)
    metadata = build_metadata(
        contract=contract,
        features=features,
        metrics=model_metrics,
        model_format=selected_format,
        model_name=selected_name,
        data_fingerprint=get_data_fingerprint(config, contract, data_mode),
        git_sha=get_git_sha(),
        library_versions=get_library_versions(),
    )
    _clear_package_model_artifacts(package_dir)
    save_model_package(model, metadata, package_dir, contract=contract)
    return metadata


def _package_size_kb(package_dir: Path) -> float:
    total_bytes = sum(path.stat().st_size for path in package_dir.rglob("*") if path.is_file())
    return round(total_bytes / 1024.0, 2)


def _measure_load_and_predict(
    package_dir: Path,
    contract: DatasetContract,
    X_test: pd.DataFrame,
    *,
    repeats: int = 5,
) -> tuple[float, float, float, pd.DataFrame]:
    was_tracing = tracemalloc.is_tracing()
    if not was_tracing:
        tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        t_load_start = time.perf_counter()
        package = load_model_package(package_dir, contract=contract)
        load_time_ms = (time.perf_counter() - t_load_start) * 1000.0
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        if not was_tracing:
            tracemalloc.stop()

    # Rozgrzewka przed pomiarem latencji (pomija jednorazowe koszty inicjalizacji).
    out = predict_from_package(package, X_test)
    latencies_ms = []
    for _ in range(max(1, repeats)):
        t_pred_start = time.perf_counter()
        out = predict_from_package(package, X_test)
        latencies_ms.append((time.perf_counter() - t_pred_start) * 1000.0)

    return (
        round(load_time_ms, 2),
        round(peak_bytes / (1024.0 * 1024.0), 3),
        round(statistics.median(latencies_ms), 2),
        out,
    )


def _log_experiment_to_wandb(
    row: Mapping[str, Any],
    run_config: Mapping[str, Any],
    *,
    project: str | None,
    entity: str | None,
) -> None:
    import wandb

    init_kwargs: dict[str, Any] = {
        "name": str(row["model_name"]),
        "job_type": "experiment",
        "config": dict(run_config),
    }
    if project:
        init_kwargs["project"] = project
    if entity:
        init_kwargs["entity"] = entity

    run = wandb.init(**init_kwargs)
    try:
        run.log(
            {
                "accuracy": float(row["accuracy"]),
                "precision": float(row["precision"]),
                "recall": float(row["recall"]),
                "f1": float(row["f1"]),
                "predict_time_ms": float(row["predict_time_ms"]),
                "load_time_ms": float(row["load_time_ms"]),
                "package_size_kb": float(row["package_size_kb"]),
                "load_peak_memory_mb": float(row["load_peak_memory_mb"]),
            }
        )
    finally:
        run.finish()


def _evaluate_and_log_candidate(
    *,
    model: Any,
    model_name: str,
    model_format: str,
    model_metrics: Mapping[str, Any],
    contract: DatasetContract,
    features: Mapping[str, Sequence[str]],
    X_test: pd.DataFrame,
    y_test: pd.Series,
    data_fingerprint: str,
    git_sha: str,
    library_versions: Mapping[str, str],
    data_mode: str,
    extra_config: Mapping[str, Any],
    wandb_enabled: bool,
    wandb_project: str | None,
    wandb_entity: str | None,
    package_save_path: str | Path | None = None,
) -> dict[str, Any]:
    metadata = build_metadata(
        contract=contract,
        features=features,
        metrics=model_metrics,
        model_format=model_format,
        model_name=model_name,
        data_fingerprint=data_fingerprint,
        git_sha=git_sha,
        library_versions=library_versions,
    )
    with tempfile.TemporaryDirectory(prefix=f"exp_{model_name}_") as tmp_dir:
        pkg_dir = save_model_package(model, metadata, Path(tmp_dir) / "pkg", contract=contract)
        size_kb = _package_size_kb(pkg_dir)
        load_ms, peak_mb, pred_ms, pred_out = _measure_load_and_predict(pkg_dir, contract, X_test)

    if package_save_path is not None:
        target_dir = Path(package_save_path)
        _clear_package_model_artifacts(target_dir)
        save_model_package(model, metadata, target_dir, contract=contract)

    measured_metrics = compute_metrics(y_test, pred_out["prediction"])
    row = {
        "model_name": model_name,
        "model_format": model_format,
        "f1": round(float(measured_metrics["f1"]), 6),
        "precision": round(float(measured_metrics["precision"]), 6),
        "recall": round(float(measured_metrics["recall"]), 6),
        "accuracy": round(float(measured_metrics["accuracy"]), 6),
        "predict_time_ms": pred_ms,
        "load_time_ms": load_ms,
        "package_size_kb": size_kb,
        "load_peak_memory_mb": peak_mb,
        "git_sha": git_sha,
        "data_fingerprint": data_fingerprint,
    }
    if wandb_enabled:
        run_config = {
            "model_name": model_name,
            "model_format": model_format,
            "dataset": contract.dataset_id,
            "data_mode": data_mode,
            "git_sha": git_sha,
            "data_fingerprint": data_fingerprint,
            **extra_config,
        }
        _log_experiment_to_wandb(row, run_config, project=wandb_project, entity=wandb_entity)
    return row


def _train_autogluon_candidate(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    contract: DatasetContract,
    config_params: Mapping[str, Any],
    work_dir: Path,
) -> tuple[Any, dict[str, Any]]:
    from autogluon.tabular import TabularPredictor

    train_df = X_train.copy()
    train_df[contract.target] = y_train.to_numpy()

    predictor = TabularPredictor(
        label=contract.target,
        problem_type="binary",
        eval_metric="f1",
        path=str(work_dir),
        verbosity=1,
    )
    fit_kwargs: dict[str, Any] = {"time_limit": config_params["time_limit"]}
    if config_params.get("presets") is not None:
        fit_kwargs["presets"] = config_params["presets"]
    if config_params.get("hyperparameters") is not None:
        fit_kwargs["hyperparameters"] = dict(config_params["hyperparameters"])

    predictor.fit(train_df, **fit_kwargs)
    y_pred = predictor.predict(X_test)
    metrics = compute_metrics(y_test, pd.Series(y_pred).astype(int))
    return predictor, metrics


def run_experiments(
    model: Pipeline,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    metrics: Mapping[str, Any],
    dataset: str,
    features: Mapping[str, Sequence[str]],
    data_mode: str,
    experiments: Mapping[str, Any],
    package_path: str | Path | None = None,
    production_model: Mapping[str, Any] | None = None,
) -> pd.DataFrame:
    columns = [
        "model_name",
        "model_format",
        "f1",
        "precision",
        "recall",
        "accuracy",
        "predict_time_ms",
        "load_time_ms",
        "package_size_kb",
        "load_peak_memory_mb",
        "git_sha",
        "data_fingerprint",
    ]
    if not experiments.get("enabled", False):
        return pd.DataFrame(columns=columns)

    contract = get_dataset_contract(dataset)
    config = load_project_config()
    data_fingerprint = get_data_fingerprint(config, contract, data_mode)
    git_sha = get_git_sha()
    library_versions = get_library_versions()

    wandb_enabled = bool(experiments.get("wandb_enabled", True)) and (
        os.environ.get("WANDB_MODE") != "disabled"
    )
    wandb_project = experiments.get("wandb_project") or os.environ.get("WANDB_PROJECT")
    wandb_entity = experiments.get("wandb_entity") or os.environ.get("WANDB_ENTITY")

    rows: list[dict[str, Any]] = [
        _evaluate_and_log_candidate(
            model=model,
            model_name="logistic_regression",
            model_format=MODEL_FORMAT_SKLEARN,
            model_metrics=_extract_model_metrics(metrics, "logistic_regression"),
            contract=contract,
            features=features,
            X_test=X_test,
            y_test=y_test,
            data_fingerprint=data_fingerprint,
            git_sha=git_sha,
            library_versions=library_versions,
            data_mode=data_mode,
            extra_config={"kind": "baseline"},
            wandb_enabled=wandb_enabled,
            wandb_project=wandb_project,
            wandb_entity=wandb_entity,
        )
    ]

    selected_name = str(production_model.get("name", "")) if production_model else ""

    for name, cfg in (experiments.get("autogluon_configs") or {}).items():
        with tempfile.TemporaryDirectory(prefix=f"ag_train_{name}_") as train_dir:
            predictor, ag_metrics = _train_autogluon_candidate(
                X_train,
                y_train,
                X_test,
                y_test,
                contract,
                cfg,
                Path(train_dir) / "predictor",
            )
            save_target = (
                package_path if package_path is not None and str(name) == selected_name else None
            )
            rows.append(
                _evaluate_and_log_candidate(
                    model=predictor,
                    model_name=str(name),
                    model_format=MODEL_FORMAT_AUTOGLUON,
                    model_metrics=ag_metrics,
                    contract=contract,
                    features=features,
                    X_test=X_test,
                    y_test=y_test,
                    data_fingerprint=data_fingerprint,
                    git_sha=git_sha,
                    library_versions=library_versions,
                    data_mode=data_mode,
                    extra_config={
                        "kind": "autogluon",
                        "time_limit": cfg.get("time_limit"),
                        "presets": cfg.get("presets"),
                        "hyperparameters": cfg.get("hyperparameters"),
                    },
                    wandb_enabled=wandb_enabled,
                    wandb_project=wandb_project,
                    wandb_entity=wandb_entity,
                    package_save_path=save_target,
                )
            )

    return pd.DataFrame(rows, columns=columns)
