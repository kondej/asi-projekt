"""Konfiguracja startowa projektu Kedro (Sprint 2).

Logika przetwarzania pozostaje w ``data.py`` i ``model.py``.
"""

from kedro.config import OmegaConfigLoader

CONFIG_LOADER_CLASS = OmegaConfigLoader
CONFIG_LOADER_ARGS = {
    "base_env": "base",
    "default_run_env": "local",
    # Nadpisanie pojedynczej ścieżki w conf/ci/catalog.yml nie powinno usuwać
    # pozostałych definicji Dataset z conf/base/catalog.yml.
    "merge_strategy": {"catalog": "soft", "parameters": "soft"},
}
