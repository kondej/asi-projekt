# pipelines/ — pipeline'y Kedro

> Scaffold for Sprint 2 — do not implement before this sprint.

| Pipeline | Sprint | Wejście → wyjście |
|---|---|---|
| `data_processing/` | S2 | surowe dane → dane po input normalization i training-only filtering |
| `data_science/` | S2, rozszerzany w S3 | dane → split → model i metryki (S3: runy W&B, AutoGluon, pakiet modelu) |

Zasady (ADR-1, Sprint 2): nody to czyste funkcje, a logika przetwarzania pochodzi z `data.py`
i `model.py` — Kedro odpowiada tylko za połączenie nodów i konfigurację. Testy nodów:
`tests/pipelines/`.
