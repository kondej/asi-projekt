import json
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from asi_project.config import DatasetContract
from asi_project.data import label_text, normalize_column_names, normalize_input
from asi_project.model_metadata import validate_metadata

MODEL_FORMAT_SKLEARN = "sklearn-joblib"
MODEL_FORMAT_AUTOGLUON = "autogluon"
SUPPORTED_MODEL_FORMATS = (MODEL_FORMAT_SKLEARN, MODEL_FORMAT_AUTOGLUON)

METADATA_FILENAME = "metadata.json"
SKLEARN_MODEL_FILENAME = "model.joblib"
AUTOGLUON_MODEL_DIRNAME = "model"
PREDICTION_COLUMNS = ("prediction", "probability")


@dataclass(frozen=True)
class ModelPackage:
    model: Any
    metadata: dict[str, Any]
    path: Path | None = None


def _ensure_valid_metadata(
    metadata: Any,
    contract: DatasetContract | None = None,
) -> dict[str, Any]:
    problems = validate_metadata(metadata, contract=contract)
    if problems:
        raise ValueError("Niepoprawne metadane pakietu modelu:\n" + "\n".join(problems))
    return dict(metadata)


def _check_model_format(metadata: Mapping[str, Any]) -> str:
    model_format = metadata.get("model_format")
    if model_format not in SUPPORTED_MODEL_FORMATS:
        raise ValueError(
            f"Nieznany model_format {model_format!r}; dozwolone: {SUPPORTED_MODEL_FORMATS}."
        )
    return str(model_format)


def _save_autogluon_model(model: Any, model_dir: Path) -> None:
    model_path = getattr(model, "path", None)
    if model_path is not None and Path(model_path).resolve() == model_dir.resolve():
        model.save()
        return
    if hasattr(model, "clone"):
        model.clone(str(model_dir), dirs_exist_ok=True)
        return
    if model_path is not None and Path(model_path).is_dir():
        shutil.copytree(model_path, model_dir, dirs_exist_ok=True)
        return
    raise TypeError(
        "Model AutoGluon musi udostępniać metodę clone() lub katalog path do skopiowania."
    )


def _load_autogluon_model(model_dir: Path) -> Any:
    from autogluon.tabular import TabularPredictor

    return TabularPredictor.load(str(model_dir))


def save_model_package(
    model: Any,
    metadata: Mapping[str, Any],
    path: Path | str,
    *,
    contract: DatasetContract | None = None,
) -> Path:
    validated_metadata = _ensure_valid_metadata(dict(metadata), contract=contract)
    model_format = _check_model_format(validated_metadata)

    package_dir = Path(path)
    package_dir.mkdir(parents=True, exist_ok=True)

    if model_format == MODEL_FORMAT_SKLEARN:
        joblib.dump(model, package_dir / SKLEARN_MODEL_FILENAME)
    elif model_format == MODEL_FORMAT_AUTOGLUON:
        _save_autogluon_model(model, package_dir / AUTOGLUON_MODEL_DIRNAME)

    metadata_path = package_dir / METADATA_FILENAME
    metadata_path.write_text(
        json.dumps(validated_metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return package_dir


def load_model_package(
    path: Path | str,
    *,
    contract: DatasetContract | None = None,
) -> ModelPackage:
    package_dir = Path(path)
    metadata_path = package_dir / METADATA_FILENAME
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Brak pliku {METADATA_FILENAME} w pakiecie modelu: {package_dir}.")

    try:
        raw_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Nie udało się odczytać {metadata_path}: {exc}") from exc

    metadata = _ensure_valid_metadata(raw_metadata, contract=contract)
    model_format = _check_model_format(metadata)

    if model_format == MODEL_FORMAT_SKLEARN:
        model_path = package_dir / SKLEARN_MODEL_FILENAME
        if not model_path.is_file():
            raise FileNotFoundError(
                f"Brak pliku modelu {SKLEARN_MODEL_FILENAME} w pakiecie: {package_dir}."
            )
        model = joblib.load(model_path)
    elif model_format == MODEL_FORMAT_AUTOGLUON:
        model_dir = package_dir / AUTOGLUON_MODEL_DIRNAME
        if not model_dir.is_dir():
            raise FileNotFoundError(
                f"Brak katalogu modelu {AUTOGLUON_MODEL_DIRNAME}/ w pakiecie: {package_dir}."
            )
        model = _load_autogluon_model(model_dir)

    return ModelPackage(model=model, metadata=metadata, path=package_dir)


def _prepare_prediction_features(package: ModelPackage, df: pd.DataFrame) -> pd.DataFrame:
    features = list(package.metadata["features"])
    df_norm = normalize_column_names(df)
    missing = [col for col in features if col not in df_norm.columns]
    if missing:
        raise ValueError(f"Brak wymaganych cech wejściowych: {missing}.")
    return normalize_input(df_norm.loc[:, features].copy())


def _encode_predictions(raw_preds: Any, positive_class: str) -> np.ndarray:
    pos_label = label_text(positive_class)
    series = pd.Series(raw_preds)
    if pd.api.types.is_integer_dtype(series) and set(series.dropna().unique()).issubset({0, 1}):
        return series.to_numpy(dtype="int64")
    return (series.map(label_text) == pos_label).to_numpy(dtype="int64")


def _positive_proba_sklearn(model: Any, X: pd.DataFrame, positive_class: str) -> np.ndarray:
    proba = np.asarray(model.predict_proba(X), dtype=float)
    classes = list(getattr(model, "classes_", []))
    if 1 in classes:
        pos_idx = classes.index(1)
    elif positive_class in classes:
        pos_idx = classes.index(positive_class)
    elif classes:
        matched = [
            i for i, cls in enumerate(classes) if label_text(cls) == label_text(positive_class)
        ]
        if not matched:
            raise ValueError(
                f"Nie znaleziono klasy pozytywnej {positive_class!r} w model.classes_={classes}."
            )
        pos_idx = matched[0]
    elif proba.ndim == 2 and proba.shape[1] == 2:
        pos_idx = 1
    else:
        raise ValueError("Model sklearn nie udostępnia classes_ ani dwuklasowego predict_proba.")
    return proba[:, pos_idx].astype(float)


def _positive_proba_autogluon(model: Any, X: pd.DataFrame, positive_class: str) -> np.ndarray:
    proba_df = model.predict_proba(X)
    if not isinstance(proba_df, pd.DataFrame):
        proba_df = pd.DataFrame(proba_df)
    pos_label = label_text(positive_class)
    if positive_class in proba_df.columns:
        col = positive_class
    else:
        matched = [c for c in proba_df.columns if label_text(c) == pos_label]
        if matched:
            col = matched[0]
        elif 1 in proba_df.columns:
            col = 1
        else:
            raise ValueError(
                f"Nie znaleziono kolumny klasy pozytywnej {positive_class!r} "
                f"w wyniku predict_proba: {list(proba_df.columns)}."
            )
    return proba_df[col].to_numpy(dtype=float)


def predict_from_package(package: ModelPackage, df: pd.DataFrame) -> pd.DataFrame:
    X = _prepare_prediction_features(package, df)
    model_format = _check_model_format(package.metadata)
    positive_class = str(package.metadata["positive_class"])

    if model_format == MODEL_FORMAT_SKLEARN:
        probability = _positive_proba_sklearn(package.model, X, positive_class)
    else:
        probability = _positive_proba_autogluon(package.model, X, positive_class)

    prediction = _encode_predictions(package.model.predict(X), positive_class)
    return pd.DataFrame(
        {"prediction": prediction, "probability": probability},
        index=df.index,
    )


def validate_prediction_output(df_out: pd.DataFrame, n_rows: int) -> None:
    if not isinstance(df_out, pd.DataFrame):
        raise ValueError(f"Oczekiwano DataFrame, otrzymano {type(df_out).__name__}.")
    if list(df_out.columns) != list(PREDICTION_COLUMNS):
        raise ValueError(
            f"Niepoprawne kolumny wyniku: {list(df_out.columns)}; oczekiwano {list(PREDICTION_COLUMNS)}."
        )
    if len(df_out) != n_rows:
        raise ValueError(f"Niepoprawna liczba wierszy: {len(df_out)}; oczekiwano {n_rows}.")

    pred = df_out["prediction"]
    if pred.isna().any() or not pd.api.types.is_integer_dtype(pred):
        raise ValueError(
            f"Kolumna 'prediction' musi mieć typ całkowity bez braków (jest {pred.dtype})."
        )
    invalid_preds = set(pred.unique()) - {0, 1}
    if invalid_preds:
        raise ValueError(
            f"Kolumna 'prediction' zawiera wartości spoza {{0, 1}}: {sorted(invalid_preds)}."
        )

    prob = df_out["probability"]
    if (
        prob.isna().any()
        or pd.api.types.is_bool_dtype(prob)
        or not pd.api.types.is_numeric_dtype(prob)
    ):
        raise ValueError(
            f"Kolumna 'probability' musi być numeryczna bez braków (jest {prob.dtype})."
        )
    prob_values = prob.to_numpy(dtype=float)
    if not np.isfinite(prob_values).all() or ((prob_values < 0.0) | (prob_values > 1.0)).any():
        raise ValueError("Kolumna 'probability' musi zawierać skończone wartości z zakresu [0, 1].")
