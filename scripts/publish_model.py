"""Publikuje gotowy pakiet modelu jako W&B Artifact (typ ``model``) z aliasem ``production``.

Skrypt NIE trenuje modelu. Wczytuje istniejący pakiet (``model_package.py``), sprawdza
``metadata.json`` i dopiero wtedy wysyła katalog pakietu do W&B.

Użycie:
    export WANDB_PROJECT=<projekt> WANDB_ENTITY=<zespół lub login>
    python scripts/publish_model.py --package data/06_models/model_package --alias production

    # tylko walidacja pakietu, bez wysyłania do W&B:
    python scripts/publish_model.py --dry-run
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from asi_project.config import get_contract, load_project_config
from asi_project.model_metadata import validate_metadata
from asi_project.model_package import load_model_package

DEFAULT_PACKAGE = Path("data/06_models/model_package")
DEFAULT_ALIASES = ("production",)
ARTIFACT_TYPE = "model"


class PublishError(RuntimeError):
    """Pakietu nie można opublikować (zły pakiet albo brak konfiguracji W&B)."""


def default_artifact_name(metadata: dict[str, Any]) -> str:
    """Stała nazwa artefaktu, np. ``online_shoppers-model``; z niej korzysta smoke modelu."""
    return f"{metadata['dataset']}-model"


def load_and_validate(package_dir: Path, contract=None) -> dict[str, Any]:
    """Wczytuje pakiet wspólną funkcją projektu i zwraca jego metadane po walidacji."""
    if not package_dir.is_dir():
        raise PublishError(f"Brak katalogu pakietu: {package_dir}. Uruchom najpierw `kedro run`.")
    try:
        package = load_model_package(package_dir, contract=contract)
    except (FileNotFoundError, ValueError) as error:
        raise PublishError(f"Pakiet {package_dir} jest niepoprawny:\n{error}") from error
    problems = validate_metadata(package.metadata, contract=contract)
    if problems:
        raise PublishError("Niepoprawne metadata.json:\n" + "\n".join(problems))
    return package.metadata


def publish(
    package_dir: Path,
    metadata: dict[str, Any],
    *,
    artifact_name: str,
    aliases: list[str],
    project: str,
    entity: str | None,
) -> str:
    """Wysyła katalog pakietu jako W&B Artifact i zwraca jego pełną nazwę z wersją."""
    import wandb  # import leniwy: moduły projektu nie zależą od W&B

    run = wandb.init(
        project=project,
        entity=entity,
        job_type="publish-model",
        config={
            "model_name": metadata["model_name"],
            "model_format": metadata["model_format"],
            "git_sha": metadata["git_sha"],
            "data_fingerprint": metadata["data_fingerprint"],
        },
    )
    try:
        artifact = wandb.Artifact(
            name=artifact_name,
            type=ARTIFACT_TYPE,
            description=f"Pakiet modelu {metadata['model_name']} ({metadata['dataset']}).",
            metadata=metadata,
        )
        artifact.add_dir(str(package_dir))
        logged = run.log_artifact(artifact, aliases=aliases)
        logged.wait()
        return f"{logged.entity}/{logged.project}/{logged.name}"
    finally:
        run.finish()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publikacja pakietu modelu jako W&B Artifact.")
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument(
        "--alias",
        action="append",
        dest="aliases",
        help="Alias artefaktu (można podać kilka razy). Domyślnie: production.",
    )
    parser.add_argument("--name", help="Nazwa artefaktu. Domyślnie: <dataset>-model.")
    parser.add_argument("--project", default=os.environ.get("WANDB_PROJECT"))
    parser.add_argument("--entity", default=os.environ.get("WANDB_ENTITY"))
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Tylko wczytanie i walidacja pakietu, bez wysyłania do W&B.",
    )
    args = parser.parse_args(argv)
    aliases = args.aliases or list(DEFAULT_ALIASES)

    try:
        contract = get_contract(load_project_config())
        metadata = load_and_validate(args.package, contract=contract)
        name = args.name or default_artifact_name(metadata)
        print(f"Pakiet {args.package}: OK ({metadata['model_name']}, git {metadata['git_sha']})")
        if args.dry_run:
            print(f"--dry-run: pominięto wysyłkę artefaktu {name} z aliasami {aliases}.")
            return 0
        if not args.project:
            raise PublishError("Brak projektu W&B: ustaw WANDB_PROJECT albo podaj --project.")
        qualified = publish(
            args.package,
            metadata,
            artifact_name=name,
            aliases=aliases,
            project=args.project,
            entity=args.entity,
        )
    except PublishError as error:
        print(f"BŁĄD: {error}", file=sys.stderr)
        return 1

    print(f"Opublikowano {qualified} z aliasami {aliases}.")
    print(f"Pobranie: wandb.Api().artifact('{qualified.rsplit(':', 1)[0]}:{aliases[0]}')")
    return 0


if __name__ == "__main__":
    sys.exit(main())
