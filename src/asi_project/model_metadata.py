"""Metadane pakietu modelu (``metadata.json``): pochodzenie modelu, budowa i walidacja (Sprint 3)."""

import importlib.metadata
import json
import os
import platform
import subprocess
from pathlib import Path

from asi_project.config import DatasetContract, ProjectConfig
from asi_project.data import raw_data_path
from asi_project.download import sha256_hex
from asi_project.metrics import DATA_MODES

UNKNOWN = "unknown"
REQUIRED_LIBRARIES = ("scikit-learn", "pandas", "numpy", "joblib")
OPTIONAL_LIBRARIES = ("autogluon.tabular", "wandb")


def get_git_sha(cwd: Path | str | None = None) -> str:
    """SHA bieżącego commita: ``git rev-parse HEAD``, potem ``GITHUB_SHA``, w końcu ``unknown``.

    Brak gita albo katalogu bez repozytorium nie zgłasza wyjątku — CI nie może się przez to wywrócić.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        result = None
    if result is not None and result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return os.environ.get("GITHUB_SHA") or UNKNOWN


def get_data_fingerprint(config: ProjectConfig, contract: DatasetContract, data_mode: str) -> str:
    """Odcisk SHA-256 danych użytych w treningu albo ``unknown``, gdy nie da się go ustalić.

    - ``full``: ``sha256`` z ``fingerprint.json`` zapisanego przez ``download.py``,
    - ``sample``: SHA-256 pliku próbki CI.
    Brak pliku albo uszkodzony ``fingerprint.json`` daje ``unknown`` (bez wyjątku).
    """
    if data_mode == "full":
        path = raw_data_path(config, contract).parent / "fingerprint.json"
        try:
            sha256 = json.loads(path.read_text(encoding="utf-8")).get("sha256")
        except (OSError, ValueError, AttributeError):
            return UNKNOWN
        return sha256 if isinstance(sha256, str) and sha256 else UNKNOWN
    if data_mode == "sample":
        try:
            return sha256_hex(config.ci_sample_path.read_bytes())
        except OSError:
            return UNKNOWN
    raise ValueError(f"Nieznany tryb danych {data_mode!r}; dozwolone: {DATA_MODES}.")


def _installed_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def get_library_versions() -> dict[str, str]:
    """Wersje bibliotek modelu: Python i biblioteki podstawowe oraz opcjonalnie AutoGluon i W&B.

    Wersje czytamy przez ``importlib.metadata``, bez importowania bibliotek. Brakującą bibliotekę
    podstawową zapisujemy jako ``unknown``, a brakującą opcjonalną (AutoGluon, W&B) pomijamy.
    """
    versions = {"python": platform.python_version()}
    for name in REQUIRED_LIBRARIES:
        versions[name] = _installed_version(name) or UNKNOWN
    for name in OPTIONAL_LIBRARIES:
        version = _installed_version(name)
        if version:
            versions[name] = version
    return versions
