"""Konfiguracja projektu zespołu i rejestr zatwierdzonych datasetów.

- ``project.yaml`` (katalog główny repo): decyzje zespołu — dataset, typy cech, parametry splitu.
- ``datasets.yaml`` (ten pakiet): kontrakt prowadzącej — target, klasa pozytywna,
  ALLOWED / EXCLUDED FEATURES, moment predykcji, strategia splitu. Zespół go nie edytuje.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_FILE = "project.yaml"
REGISTRY_PATH = Path(__file__).with_name("datasets.yaml")
SPLIT_STRATEGIES = ("stratified_random", "time_ordered")


class ConfigError(ValueError):
    """Błąd w project.yaml albo w rejestrze datasetów."""


@dataclass(frozen=True)
class DatasetContract:
    """Kontrakt jednego zatwierdzonego datasetu (źródło prawdy: ``datasets.yaml``)."""

    dataset_id: str
    title: str
    source_url: str
    doi: str
    license: str
    download_url: str
    download_member: str
    read_csv_kwargs: dict[str, Any]
    target: str
    positive_class: str
    prediction_moment: str
    split_strategy: str
    allowed_features: tuple[str, ...]
    excluded_features: dict[str, str]

    @property
    def required_columns(self) -> tuple[str, ...]:
        """Kolumny wymagane w surowych danych: target i wszystkie ALLOWED FEATURES."""
        return (self.target, *self.allowed_features)


@dataclass(frozen=True)
class ProjectConfig:
    """Decyzje zespołu zapisane w ``project.yaml``."""

    root: Path
    dataset_id: str | None
    numeric_features: tuple[str, ...]
    categorical_features: tuple[str, ...]
    test_size: float
    random_state: int
    ci_sample_path: Path
    metrics_path: Path

    @property
    def dataset_selected(self) -> bool:
        return bool(self.dataset_id)

    @property
    def model_features(self) -> tuple[str, ...]:
        """Cechy modelu w ustalonej kolejności: najpierw numeryczne, potem kategoryczne."""
        return (*self.numeric_features, *self.categorical_features)

    @property
    def features_declared(self) -> bool:
        return bool(self.model_features)


def find_repo_root(start: Path | None = None) -> Path:
    """Zwraca katalog z ``project.yaml``, idąc w górę od ``start`` (domyślnie: bieżący katalog)."""
    env_root = os.environ.get("ASI_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / PROJECT_FILE).is_file():
            return candidate
    raise ConfigError(f"Nie znaleziono pliku {PROJECT_FILE} w {current} ani w katalogach wyżej.")


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        content = yaml.safe_load(handle)
    if not isinstance(content, dict):
        raise ConfigError(f"Plik {path} musi zawierać mapę klucz-wartość.")
    return content


def _parse_contract(dataset_id: str, spec: dict[str, Any]) -> DatasetContract:
    try:
        download = spec["download"]
        excluded = spec.get("excluded_features") or {}
        contract = DatasetContract(
            dataset_id=dataset_id,
            title=str(spec["title"]),
            source_url=str(spec["source_url"]),
            doi=str(spec["doi"]),
            license=str(spec["license"]),
            download_url=str(download["url"]),
            download_member=str(download["member"]),
            read_csv_kwargs=dict(download.get("read_csv") or {}),
            target=str(spec["target"]),
            positive_class=str(spec["positive_class"]),
            prediction_moment=" ".join(str(spec["prediction_moment"]).split()),
            split_strategy=str(spec["split"]),
            allowed_features=tuple(str(name) for name in spec["allowed_features"]),
            excluded_features={str(name): str(reason) for name, reason in excluded.items()},
        )
    except KeyError as error:
        raise ConfigError(f"Dataset {dataset_id}: w rejestrze brakuje pola {error}.") from error
    if contract.split_strategy not in SPLIT_STRATEGIES:
        strategy = contract.split_strategy
        raise ConfigError(f"Dataset {dataset_id}: nieznana strategia splitu {strategy}.")
    return contract


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, DatasetContract]:
    """Wczytuje rejestr zatwierdzonych datasetów."""
    raw = _read_yaml(path)
    return {dataset_id: _parse_contract(dataset_id, spec) for dataset_id, spec in raw.items()}


def load_project_config(root: Path | None = None) -> ProjectConfig:
    """Wczytuje ``project.yaml`` zespołu."""
    root = find_repo_root(root)
    raw = _read_yaml(root / PROJECT_FILE)
    features = raw.get("features") or {}
    split = raw.get("split") or {}
    paths = raw.get("paths") or {}
    dataset_id = raw.get("dataset")
    return ProjectConfig(
        root=root,
        dataset_id=str(dataset_id) if dataset_id else None,
        numeric_features=tuple(str(name) for name in features.get("numeric") or ()),
        categorical_features=tuple(str(name) for name in features.get("categorical") or ()),
        test_size=float(split.get("test_size", 0.2)),
        random_state=int(split.get("random_state", 42)),
        ci_sample_path=root / str(paths.get("ci_sample", "data/01_raw/sample.csv")),
        metrics_path=root / str(paths.get("metrics", "metrics.json")),
    )


def get_contract(
    config: ProjectConfig,
    registry: dict[str, DatasetContract] | None = None,
) -> DatasetContract:
    """Zwraca kontrakt datasetu wybranego w ``project.yaml``."""
    if not config.dataset_selected:
        raise ConfigError("Nie wybrano datasetu: uzupełnij pole 'dataset' w project.yaml.")
    registry = registry if registry is not None else load_registry()
    if config.dataset_id not in registry:
        known = ", ".join(sorted(registry))
        raise ConfigError(f"Nieznany dataset '{config.dataset_id}'. Dozwolone: {known}.")
    return registry[config.dataset_id]
