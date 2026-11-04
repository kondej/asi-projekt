"""Rejestrowanie pipeline'ów Kedro (Sprint 2).

Po przygotowaniu ``create_pipeline()`` w podpakietach
``data_processing`` oraz ``data_science`` Kedro wykrywa je automatycznie.
Ten plik NIE zawiera implementacji nodów ani gotowego pipeline'u.
"""

from kedro.framework.project import find_pipelines
from kedro.pipeline import Pipeline


def register_pipelines() -> dict[str, Pipeline]:
    """Wykryj pipeline'y z ``src/asi_project/pipelines/``."""
    return find_pipelines()
