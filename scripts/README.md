# scripts/

## Skrypty bazowe (od Sprintu 1)

| Skrypt | Rola |
|---|---|
| `download_data.py` | pobranie pełnych danych wybranego datasetu i odcisk SHA-256 |
| `make_ci_sample.py` | próbka CI `data/01_raw/sample.csv` |
| `check_env.py` | kontrola środowiska; `--autogluon` to pre-flight gotowości do Sprintu 3 |
| `check_dod.py` | automatyczny raport tylko dla Sprintu 1; w S2–S6 wskazuje dokumentację i nie ocenia projektu |
| `check_metrics.py`, `project_status.py`, `run_notebook.py` | kroki CI |
| `build_issues.py` | generowanie `github_issues/` z `docs/sprints/` |
| `smoke_datasets.py` | narzędzie prowadzącej: smoke prawdziwych źródeł wszystkich datasetów |
| `publish_model.py` | S3: publikacja gotowego pakietu modelu jako W&B Artifact (typ `model`) z aliasem `production` — bez treningu |
| `smoke_model.py` | S3, poza CI: pobranie modelu `production` z W&B → wczytanie bez treningu → predykcja 5 wierszy → kontrola schematu |

## Publikacja modelu `production` (Sprint 3)

Skrypt wczytuje istniejący pakiet przez `load_model_package`, sprawdza `metadata.json`
(`validate_metadata`) i dopiero wtedy wysyła katalog pakietu do W&B. Nie uruchamia treningu.

```bash
kedro run                                   # tworzy data/06_models/model_package/
wandb login                                 # jednorazowo, klucz API trzymamy poza repo
export WANDB_PROJECT=<projekt> WANDB_ENTITY=<zespół lub login>
python scripts/publish_model.py --dry-run   # tylko walidacja pakietu, bez W&B
python scripts/publish_model.py --package data/06_models/model_package --alias production
```

- Nazwa artefaktu: `<dataset>-model` (np. `online_shoppers-model`), typ `model`; można ją zmienić `--name`.
- Metadane artefaktu = zawartość `metadata.json`.
- Alias `production` w W&B wskazuje zawsze jedną wersję — nowa publikacja przenosi go na nowy pakiet.
- Pobranie (np. w smoke modelu): `wandb.Api().artifact("<entity>/<projekt>/online_shoppers-model:production")`.
- Skrypt nie jest uruchamiany w CI (wymaga konta W&B); w CI testy używają atrapy `wandb`
  (`tests/test_publish_model.py`).

## Smoke modelu `production` (Sprint 3, poza CI)

Sprawdza, czy model `production` da się pobrać z W&B i użyć bez treningu. Uruchamiamy go
w świeżym procesie, niezależnie od `kedro run`. Wymaga konta W&B i dostępu do zespołu,
dlatego nie jest częścią CI (w CI `tests/test_smoke_model.py` używa atrapy `wandb`).

```bash
wandb login                                         # jednorazowo
export WANDB_PROJECT=<projekt> WANDB_ENTITY=<zespół>
python scripts/smoke_model.py                       # <entity>/<projekt>/<dataset>-model:production
python scripts/smoke_model.py --artifact <entity>/<projekt>/<nazwa>:production
```

Kroki: pobranie artefaktu do katalogu tymczasowego → `load_model_package` (walidacja
`metadata.json` względem kontraktu datasetu) → `predict_from_package` dla 5 wierszy
z `data/01_raw/sample.csv` → `validate_prediction_output`. Skrypt wypisuje wersję artefaktu,
`git_sha`, metryki i predykcje oraz kończy się `SMOKE OK`.

Kody wyjścia: `0` — OK, `1` — zły pakiet lub predykcja, `2` — brak dostępu do W&B.

## Kolejne etapy (Sprinty 3–6)

> Opis kontraktów. Implementacje przygotowują zespoły w odpowiednim sprincie.

| Skrypt | Sprint | Kontrakt |
|---|---|---|
| smoke modelu | S3 | pobranie pakietu `production` z W&B → wczytanie w czystym procesie → predykcja 5 wierszy → sprawdzenie schematu odpowiedzi |
| wspólny smoke API | S4 → S6 | `/healthz` → tryb persistence → `/predict` z tokenem → kontrakt odpowiedzi → w trybie `sql` zapisany rekord, w trybie `disabled` brak wymogu zapisu; ten sam skrypt na kontenerze, na compose i na Cloud Run |

Skrypt wdrożenia (`deploy.sh`, Sprint 6) znajdzie się w katalogu `deploy/`.
