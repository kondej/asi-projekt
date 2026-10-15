# Pakiet `asi_project`

Wspólny kod projektu. Jeden pakiet gwarantuje, że trening i serwowanie korzystają z tej samej
logiki (np. `normalize_input` działa identycznie w notebooku, w pipeline Kedro i w API).

## Aktywne w Sprincie 1

| Moduł | Rola |
|---|---|
| `datasets.yaml` | kontrakt zatwierdzonych datasetów (prowadząca; zespół nie edytuje) |
| `config.py` | odczyt `project.yaml` i rejestru datasetów |
| `data.py` | kontrakt danych, input normalization, training-only filtering, X/y, split |
| `model.py` | DummyClassifier i sklearn Pipeline z model preprocessing (TODO zespołu) |
| `metrics.py` | metryki i kontrakt `metrics.json` |
| `download.py` | pobieranie danych i odcisk SHA-256 |

## Future scaffold (Sprinty 2–4)

> Scaffold for Sprints 2–4 — do not implement before these sprints.

| Element | Sprint | Kontrakt |
|---|---|---|
| `pipelines/data_processing/` | S2 | nody: walidacja → input normalization → training-only filtering (funkcje z `data.py`) |
| `pipelines/data_science/` | S2 → S3 | split → trening Pipeline → ewaluacja; w S3 tracking W&B i AutoGluon |
| `pipeline_registry.py`, `settings.py` | S2 | pliki projektu Kedro (rejestracja pipeline'ów, ustawienia) |
| `model_package.py` | S3 | zapis i odczyt pakietu modelu: katalog z modelem i `metadata.json` (cechy, target i klasa pozytywna, metryki, git SHA, fingerprint danych, wersje bibliotek); wspólny dla Kedro, smoke modelu i API |
| `api/` | S4 | usługa predykcji — patrz `api/README.md` |

Zasada: moduły aktywne w Sprincie 1 nie importują Kedro, W&B, AutoGluona, FastAPI ani innych
bibliotek przyszłych sprintów. Pilnuje tego test w `tests/test_repo_hygiene.py`.
