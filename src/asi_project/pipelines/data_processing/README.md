# pipelines/data_processing

> Scaffold for Sprint 2 — do not implement before this sprint.

Pliki, które powstaną w Sprincie 2: definicje nodów i definicja pipeline'u.

Kontrakt:

- kolejność: walidacja kontraktu → input normalization → training-only filtering;
- nody korzystają z istniejących funkcji `validate`, `normalize_input` i `filter_training_rows`
  (`src/asi_project/data.py`) — bez kopiowania logiki;
- wyjście: dane gotowe do splitu (warstwa `data/02_intermediate/`, poza gitem).
