# data/ — warstwy danych

Pełne dane i wyniki pipeline'ów nigdy nie trafiają do repozytorium. W gicie są wyłącznie pliki
README oraz próbka CI `01_raw/sample.csv`.

| Katalog | Sprint | Zawartość |
|---|---|---|
| `01_raw/` | S1 (aktywny) | pełne dane z `scripts/download_data.py` (poza gitem) i próbka CI |
| `02_intermediate/` | S2 | dane po input normalization i training-only filtering (wyjście pipeline'u) |
| `06_models/` | S2 → S3 | model z pipeline'u; od S3 lokalne kopie pakietu modelu |
| `08_reporting/` | S2 | metryki generowane przez pipeline |
