# data/01_raw

- `<id datasetu>/` — pełne dane pobrane przez `python scripts/download_data.py` razem
  z `fingerprint.json` (SHA-256 pliku). Katalog jest ignorowany przez git — pełne dane nigdy
  nie trafiają do repozytorium.
- `sample.csv` — próbka CI tworzona przez `python scripts/make_ci_sample.py`. Jest commitowana:
  CI uruchamia na niej testy kontraktu i baseline. Maksymalnie 500 KB, obie klasy targetu,
  zachowana kolejność rekordów.

Źródła, licencje i kontrakty datasetów: `docs/datasets.md`.
