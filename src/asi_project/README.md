# Pakiet `asi_project`

Wspólny kod projektu. Jeden pakiet gwarantuje, że trening i serwowanie korzystają z tej samej
logiki (np. `normalize_input` działa identycznie w notebooku, w pipeline Kedro i w API).

## Moduły podstawowe (od Sprintu 1)

| Moduł | Rola |
|---|---|
| `datasets.yaml` | kontrakt zatwierdzonych datasetów (prowadząca; zespół nie edytuje) |
| `config.py` | odczyt `project.yaml` i rejestru datasetów |
| `data.py` | kontrakt danych, input normalization, training-only filtering, X/y, split |
| `model.py` | DummyClassifier i sklearn Pipeline z model preprocessing (TODO zespołu) |
| `metrics.py` | metryki i kontrakt `metrics.json` |
| `download.py` | pobieranie danych i odcisk SHA-256 |

## Rozszerzenia w Sprintach 2–4

> Implementacje poszczególnych sprintów przygotowują zespoły. Scaffold nie zawiera rozwiązań.

| Element | Sprint | Kontrakt |
|---|---|---|
| `pipelines/data_processing/` | S2 | nody: walidacja → input normalization → training-only filtering (funkcje z `data.py`) |
| `pipelines/data_science/` | S2 → S3 | split → trening Pipeline → ewaluacja; w S3 tracking W&B i AutoGluon |
| `pipeline_registry.py`, `settings.py` | S2 | pliki projektu Kedro (rejestracja pipeline'ów, ustawienia) |
| `model_package.py` | S3 | zapis i odczyt pakietu modelu: katalog z modelem i `metadata.json` (cechy, target i klasa pozytywna, metryki, git SHA, fingerprint danych, wersje bibliotek); wspólny dla Kedro, smoke modelu i API |
| `api/` | S4 | usługa predykcji — patrz `api/README.md` |

Zasada: moduły aktywne w Sprincie 1 nie importują Kedro, W&B, AutoGluona, FastAPI ani innych
bibliotek przyszłych sprintów. Pilnuje tego test w `tests/test_repo_hygiene.py`.

## Kontrakt pakietu modelu (Sprint 3)

Zespół implementuje `model_package.py` z jedną, wspólną ścieżką zapisu i odczytu
modelu, wykorzystywaną później również w API. Nie ma gotowego kodu w scaffoldzie.

Pakiet jest katalogiem z zapisanym modelem (plik lub katalog, zależnie od biblioteki)
i `metadata.json`. Metadane muszą obejmować **już wymagane** informacje:
listę cech wejściowych (ALLOWED FEATURES), target, klasę pozytywną, metryki,
Git SHA, fingerprint danych i wersje bibliotek. Dokładne nazwy kluczy JSON
ustala zespół i dokumentuje w testach; nie są osobnym kryterium oceniania.

Dwa niezależne sprawdzenia:

1. **W CI:** szybki test lokalnego zapisu → odczytu → predykcji, bez dostępu
   do W&B, bez pobierania pełnych danych i bez pełnego treningu AutoGluona.
   Można zastosować mały model testowy i mocki; test ma używać tych samych
   funkcji pakowania, których użyje kod produkcyjny.
2. **Smoke poza CI:** w świeżym procesie pobranie W&B Artifact z aliasem
   `production` → wczytanie modelu → predykcja 5 wierszy → kontrola schematu.
   Ten test wymaga dostępu do właściwego artefaktu i odpowiednich uprawnień.

Są to dwa sposoby weryfikacji **istniejących wymagań Sprintu 3**, a nie nowe
zadania. Żaden z nich nie powinien uruchamiać treningu tylko po to, by użyć modelu.
