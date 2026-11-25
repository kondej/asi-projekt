"""Smoke modelu `production` (Sprint 3) — uruchamiany poza CI, w świeżym procesie.

Ścieżka:
    W&B Artifact `<dataset>-model:production` → pobranie → load_model_package (bez treningu)
    → predykcja 5 wierszy z próbki CI → kontrola schematu odpowiedzi.

Skrypt nie importuje pipeline'u treningowego ani Kedro i nigdy nie wywołuje ``fit``.

Użycie:
    wandb login
    export WANDB_PROJECT=<projekt> WANDB_ENTITY=<zespół>
    python scripts/smoke_model.py
    python scripts/smoke_model.py --artifact <entity>/<projekt>/<nazwa>:production

Kody wyjścia: 0 — OK, 1 — błąd pakietu / predykcji / konfiguracji, 2 — brak dostępu do W&B.
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

from asi_project.config import get_contract, load_project_config
from asi_project.model_package import (
    load_model_package,
    predict_from_package,
    validate_prediction_output,
)

DEFAULT_ALIAS = "production"
N_ROWS = 5
EXIT_OK, EXIT_FAILED, EXIT_NO_ACCESS = 0, 1, 2


class SmokeError(RuntimeError):
    """Smoke nie przeszedł (zły pakiet, zła odpowiedź albo brak konfiguracji)."""


class NoAccessError(RuntimeError):
    """Nie udało się pobrać artefaktu z W&B (logowanie, uprawnienia, nazwa, sieć)."""


def artifact_path(
    *,
    entity: str | None,
    project: str | None,
    dataset: str,
    alias: str,
    name: str | None = None,
) -> str:
    """Pełna ścieżka artefaktu; domyślna nazwa jak w ``publish_model.py``: ``<dataset>-model``."""
    if not project:
        raise SmokeError("Brak projektu W&B: ustaw WANDB_PROJECT albo podaj --artifact.")
    prefix = f"{entity}/{project}" if entity else project
    return f"{prefix}/{name or f'{dataset}-model'}:{alias}"


def download_artifact(path: str, target_dir: Path) -> Any:
    """Pobiera artefakt do ``target_dir`` i zwraca obiekt artefaktu W&B."""
    try:
        import wandb  # import leniwy: tylko ten krok wymaga W&B
    except ImportError as error:
        raise NoAccessError("Brak biblioteki wandb (requirements/preflight-s3.txt).") from error
    try:
        artifact = wandb.Api().artifact(path, type="model")
        artifact.download(root=str(target_dir))
    except Exception as error:  # noqa: BLE001 — W&B rzuca różne typy błędów
        raise NoAccessError(
            f"Nie udało się pobrać artefaktu {path}: {error}\n"
            "Sprawdź `wandb login`, dostęp do zespołu W&B, WANDB_ENTITY/WANDB_PROJECT i alias."
        ) from error
    return artifact


def run_smoke(package_dir: Path, sample_path: Path, contract) -> tuple[dict, pd.DataFrame]:
    """Wczytuje pakiet, wykonuje predykcję 5 wierszy i sprawdza schemat odpowiedzi."""
    try:
        package = load_model_package(package_dir, contract=contract)
    except (FileNotFoundError, ValueError) as error:
        raise SmokeError(f"Pakiet z W&B nie daje się wczytać:\n{error}") from error
    rows = pd.read_csv(sample_path).head(N_ROWS)
    if len(rows) < N_ROWS:
        raise SmokeError(f"Próbka {sample_path} ma mniej niż {N_ROWS} wierszy.")
    try:
        out = predict_from_package(package, rows)
        validate_prediction_output(out, N_ROWS)
    except ValueError as error:
        raise SmokeError(f"Niepoprawna predykcja:\n{error}") from error
    return package.metadata, out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke modelu production z W&B.")
    parser.add_argument("--artifact", help="Pełna ścieżka artefaktu entity/projekt/nazwa:alias.")
    parser.add_argument("--alias", default=DEFAULT_ALIAS)
    parser.add_argument("--name", help="Nazwa artefaktu. Domyślnie: <dataset>-model.")
    parser.add_argument("--project", default=os.environ.get("WANDB_PROJECT"))
    parser.add_argument("--entity", default=os.environ.get("WANDB_ENTITY"))
    parser.add_argument("--sample", type=Path, help="CSV z wierszami do predykcji.")
    args = parser.parse_args(argv)

    try:
        config = load_project_config()
        contract = get_contract(config)
        path = args.artifact or artifact_path(
            entity=args.entity,
            project=args.project,
            dataset=contract.dataset_id,
            alias=args.alias,
            name=args.name,
        )
        sample_path = args.sample or config.ci_sample_path
        print(f"Artefakt: {path}")
        with tempfile.TemporaryDirectory(prefix="smoke_model_") as tmp:
            artifact = download_artifact(path, Path(tmp))
            metadata, out = run_smoke(Path(tmp), sample_path, contract)
    except NoAccessError as error:
        print(f"BRAK DOSTĘPU DO W&B: {error}", file=sys.stderr)
        return EXIT_NO_ACCESS
    except SmokeError as error:
        print(f"SMOKE NIEUDANY: {error}", file=sys.stderr)
        return EXIT_FAILED

    aliases = ", ".join(getattr(artifact, "aliases", []) or [])
    base_name = artifact.name.split(":", 1)[0]
    print(f"Wersja:   {base_name}:{artifact.version} (aliasy: {aliases})")
    print(f"Model:    {metadata['model_name']} ({metadata['model_format']})")
    print(f"Git SHA:  {metadata['git_sha']}")
    print(f"Dane:     {metadata['data_fingerprint']}")
    print(f"Metryki:  {metadata['metrics']}")
    print(f"Predykcja dla {N_ROWS} wierszy z {sample_path}:")
    print(out.to_string())
    print("SMOKE OK")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
