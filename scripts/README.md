# scripts/

## Aktywne w Sprincie 1

| Skrypt | Rola |
|---|---|
| `download_data.py` | pobranie pełnych danych wybranego datasetu i odcisk SHA-256 |
| `make_ci_sample.py` | próbka CI `data/01_raw/sample.csv` |
| `check_env.py` | kontrola środowiska; `--autogluon` to pre-flight gotowości do Sprintu 3 |
| `check_dod.py` | raport Definition of Done (`--sprint 1`; kolejne sprinty dopiszą swoje punkty) |
| `check_metrics.py`, `project_status.py`, `run_notebook.py` | kroki CI |
| `build_issues.py` | generowanie `github_issues/` z `docs/sprints/` |
| `smoke_datasets.py` | narzędzie prowadzącej: smoke prawdziwych źródeł wszystkich datasetów |

## Future scaffold (Sprinty 3–6)

> Scaffold for Sprints 3–6 — do not implement before these sprints.

| Skrypt | Sprint | Kontrakt |
|---|---|---|
| smoke modelu | S3 | pobranie pakietu `production` z W&B → wczytanie w czystym procesie → predykcja 5 wierszy → sprawdzenie schematu odpowiedzi |
| wspólny smoke API | S4 → S6 | `/healthz` → tryb persistence → `/predict` z tokenem → kontrakt odpowiedzi → w trybie `sql` zapisany rekord, w trybie `disabled` brak wymogu zapisu; ten sam skrypt na kontenerze, na compose i na Cloud Run |

Skrypt wdrożenia (`deploy.sh`, Sprint 6) znajdzie się w katalogu `deploy/`.
