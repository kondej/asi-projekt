import json
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib

from asi_project.config import DatasetContract
from asi_project.model_metadata import validate_metadata

MODEL_FORMAT_SKLEARN = "sklearn-joblib"
MODEL_FORMAT_AUTOGLUON = "autogluon"
SUPPORTED_MODEL_FORMATS = (MODEL_FORMAT_SKLEARN, MODEL_FORMAT_AUTOGLUON)

METADATA_FILENAME = "metadata.json"
SKLEARN_MODEL_FILENAME = "model.joblib"
AUTOGLUON_MODEL_DIRNAME = "model"


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
