# conf/ — konfiguracja Kedro

> Scaffold for Sprint 2 — do not implement before this sprint.

Katalog wypełnia się w Sprincie 2, gdy projekt przechodzi z notebooka na pipeline Kedro.
W Sprincie 1 nic tu nie konfigurujemy.

| Katalog | Sprint | Rola |
|---|---|---|
| `conf/base/` | S2 (rozszerzany w S3) | konfiguracja wspólna: katalog danych i parametry |
| `conf/local/` | S2 | ustawienia lokalne i poświadczenia — poza gitem (oprócz README) |
| `conf/ci/` | S2 | nadpisania dla CI: te same pipeline'y na próbce `data/01_raw/sample.csv` |

Kontrakt (z planu Sprintu 2):

- `kedro run` — pełne dane (`base` + `local`);
- `kedro run --env ci` — próbka CI (`base` + `ci`), uruchamiane w GitHub Actions;
- kod pipeline'ów nie zna ścieżek do plików — ścieżki i parametry są w konfiguracji.

Pliki konfiguracyjne i ustawienia projektu Kedro w `pyproject.toml` dodaje PR referencyjny
na starcie Sprintu 2. Przypięta wersja Kedro: `requirements/preflight-s2.txt`.
