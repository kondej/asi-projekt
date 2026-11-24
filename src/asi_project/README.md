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
| `model_metadata.py` | S3 | budowa i walidacja `metadata.json`: `build_metadata`, `validate_metadata`, pochodzenie modelu (`get_git_sha`, `get_data_fingerprint`, `get_library_versions`); używany przez `model_package.py`, W&B i smoke modelu |
| `model_package.py` | S3 | zapis i odczyt pakietu modelu (`ModelPackage`, `save_model_package`, `load_model_package`): katalog z modelem (`model.joblib` dla `sklearn-joblib` lub `model/` dla `autogluon`) i `metadata.json`; wspólny dla Kedro, smoke test modelu i API |
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

## Klucze metadata.json

`metadata.json` buduje `build_metadata`, a sprawdza `validate_metadata` (oba w
`model_metadata.py`). Zepsutych metadanych nie wolno zapisać ani wczytać: `save_model_package`
wywołuje `validate_metadata` przed zapisem, a `load_model_package` po odczycie; niepusta lista
problemów oznacza błąd. Lista kluczy jest udokumentowana w teście
[`tests/test_model_metadata.py`](../../tests/test_model_metadata.py) (`REQUIRED_KEYS`) — zmiana
kluczy wymaga zmiany tego testu i uzgodnienia z zespołem.

| Klucz | Typ | Znaczenie |
|---|---|---|
| `schema_version` | int | wersja formatu metadanych (obecnie `1`) |
| `created_at` | tekst | czas utworzenia, UTC, ISO 8601 |
| `dataset` | tekst | id datasetu z kontraktu (`datasets.yaml`) |
| `target` | tekst | kolumna docelowa z kontraktu |
| `positive_class` | tekst | klasa pozytywna z kontraktu |
| `model_format` | tekst | format modelu w pakiecie (`sklearn-joblib`, `autogluon`) |
| `model_name` | tekst | nazwa modelu, np. `logistic_regression` |
| `features` | lista tekstów | cechy wejściowe: najpierw numeryczne, potem kategoryczne (tylko ALLOWED FEATURES) |
| `feature_types` | mapa | `numeric` i `categorical`: listy nazw; `features` = `numeric` + `categorical` |
| `metrics` | mapa | `accuracy`, `precision`, `recall`, `f1` jako liczby z zakresu [0, 1] |
| `data_fingerprint` | tekst | SHA-256 danych (pełnych z `fingerprint.json` albo próbki CI), `unknown` gdy brak |
| `git_sha` | tekst | commit, z którego pochodzi model (`git`, potem `GITHUB_SHA`, potem `unknown`) |
| `library_versions` | mapa | wersje: `python`, `scikit-learn`, `pandas`, `numpy`, `joblib` oraz `autogluon.tabular` i `wandb`, jeśli są zainstalowane |

Gdy `validate_metadata` dostaje kontrakt datasetu, sprawdza też zgodność `dataset`, `target`
i `positive_class` oraz to, że `features` należą do ALLOWED FEATURES.
