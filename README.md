# ASI — projekt zespołowy

W tym repozytorium pracujecie jako zespół nad kompletnym systemem ML. W ciągu sześciu sprintów
rozwijacie jeden wspólny projekt: od danych i poprawnego eksperymentu, przez reprodukowalny
pipeline i wybór modelu, aż po API, persistence, interfejs użytkownika, konteneryzację
i wdrożenie w Google Cloud.

Od pierwszego dnia widzicie docelową strukturę systemu na wszystkie sprinty (S1–S6), ale na
starcie realizujecie wyłącznie **Sprint 1**. Elementy kolejnych sprintów są przygotowanym
scaffoldem: pokazują, co będziecie później rozwijać i z jakimi częściami systemu będzie to
powiązane, ale nie zawierają gotowych rozwiązań ani zadań do wykonania wcześniej
(szczegóły: sekcja „Architektura i scaffold S1–S6”).

<!-- KARTA-PROJEKTU:START -->
## Karta projektu (wypełnia zespół w Sprincie 1)

| Pole | Wartość |
|---|---|
| Zespół i integrator Sprintu 1 | TODO |
| Dataset (id z `docs/datasets.md`) | TODO |
| Źródło, licencja i cytowanie (DOI) | TODO |
| Data pobrania danych | TODO |
| SHA-256 pliku danych (`fingerprint.json`) | TODO |
| Dane osobowe w zbiorze i sposób postępowania | TODO |
| Target i klasa pozytywna | TODO |
| Metryka główna i uzasadnienie | TODO |
| Użytkownik systemu i decyzja, którą wspiera model | TODO |
<!-- KARTA-PROJEKTU:END -->

## Mapa projektu

| Sprint | Daty | Warstwa systemu | Główny rezultat |
|---|---|---|---|
| S1 | 15.10 – 29.10.2026 | dane i poprawny eksperyment | kontrakt danych, input normalization, baseline, CI |
| S2 | 29.10 – 12.11.2026 | reprodukowalny pipeline | `kedro run` od surowych danych do modelu i metryk |
| S3 | 12.11 – 26.11.2026 | eksperymenty i artefakt | model produkcyjny jako pakiet ładowalny poza treningiem |
| S4 | 26.11 – 17.12.2026 | usługa, stan, kontener | API z tokenem dostępu i persistence, w kontenerze |
| S5 | 17.12.2026 – 07.01.2027 | system lokalny | API + UI + Postgres uruchamiane jedną komendą |
| S6 | 07.01 – 21.01.2027 | platforma i obserwowalność | system w Cloud Run, sekret, logi, release v1.0 |

Szczegóły każdego sprintu: `docs/sprints/SPRINT_N.md`. Release candidate Sprintu 6 jest
14.01.2027, finał i demo 21.01.2027.

## Zespoły

- Rekomendowane zespoły liczą 3–4 osoby.
- Praca w parach jest dopuszczalna. Para realizuje ten sam zakres CORE i musi liczyć się
  z większym obciążeniem na osobę.
- Elementy OPTIONAL pozostają opcjonalne dla wszystkich zespołów, niezależnie od ich wielkości.
- W każdym sprincie każda osoba ma co najmniej jeden owned item, robi merytoryczne review
  cudzej pracy, a rola integratora sprintu rotuje.

## Datasety

Wszystkie projekty dotyczą binary classification. Dataset wybieracie z listy w
[`docs/datasets.md`](docs/datasets.md) — tam są też ALLOWED i EXCLUDED FEATURES, moment
predykcji i strategia splitu. Kilka zespołów może wybrać ten sam dataset.

## Start Sprintu 1

Wymagania: Miniforge (conda), Git, VS Code (wspierane oficjalnie) i środowisko `asi-ml`
z onboardingu.

```bash
git clone <adres repozytorium zespołu>
cd <katalog repozytorium>
conda env update -n asi-ml -f environment.yml --prune
conda activate asi-ml
python -m pip install --no-deps -e .
pre-commit install
python scripts/check_env.py
pytest
```

Na czystym starcie `pytest` przechodzi, a testy projektu są pomijane z komunikatem, co zrobić.
Dalej postępujcie według [`docs/sprints/SPRINT_1.md`](docs/sprints/SPRINT_1.md). Postęp
względem Definition of Done pokazuje `python scripts/check_dod.py --sprint 1`.

Najważniejsze pliki Sprintu 1:

| Plik | Kto edytuje | Po co |
|---|---|---|
| `project.yaml` | zespół | wybrany dataset, typy cech, parametry splitu |
| `src/asi_project/data.py` | zespół (miejsca oznaczone TODO) | input normalization i training-only filtering |
| `src/asi_project/model.py` | zespół (TODO) | sklearn Pipeline z model preprocessing |
| `notebooks/01_eda.ipynb` | zespół | EDA i decyzje o danych |
| `notebooks/02_baseline.ipynb` | zespół | baseline i `metrics.json` |
| `docs/architecture.md` | zespół | diagram v0 systemu docelowego |
| `src/asi_project/datasets.yaml` | prowadząca | kontrakt datasetów — nie edytujemy |

## Gałęzie, Pull Requesty i review

- Gałąź `main` jest chroniona. Każda zmiana trafia przez gałąź i Pull Request.
- Jedna gałąź na jedno zadanie, np. `s1/data-contract`, `s1/baseline`.
- PR przegląda osoba inna niż autor. Review jest merytoryczne: recenzent sprawdza zgodność
  z kontraktem i DoD, a nie tylko styl.
- PR scalamy po zielonym CI i akceptacji recenzenta.
- Opis PR wypełniamy według szablonu (w tym informację o użyciu narzędzi AI).
- Przy pracy w parze dopiszcie w commicie `Co-authored-by: Imię Nazwisko <email>`.
- Nie ma wymogu konkretnej liczby PR-ów na osobę. Liczy się owned item i realny wkład.

## Zasady danych

- Pełne dane nigdy nie trafiają do repozytorium. Pobiera je `scripts/download_data.py`
  do `data/01_raw/<id datasetu>/` (katalog ignorowany przez git).
- W repozytorium jest tylko próbka CI `data/01_raw/sample.csv` (maks. 500 KB, obie klasy
  targetu), tworzona przez `scripts/make_ci_sample.py`.
- Odcisk SHA-256 pliku danych (z `fingerprint.json`) wpisujecie do karty projektu.
- Do X modelu trafiają wyłącznie ALLOWED FEATURES wybranego datasetu.
- Plików `.env` nie commitujemy; w repozytorium może być tylko `.env.example`
  bez prawdziwych wartości.
- Zbiory są na licencji CC BY 4.0 — podajcie źródło i cytowanie w karcie projektu.

## Testy, pre-commit i CI

```bash
pytest                       # wszystkie testy
pre-commit run --all-files   # ruff (lint i formatowanie), nbstripout, hooki plików
python scripts/check_dod.py --sprint 1  # raport Definition of Done Sprintu 1
```

Hooki pre-commit działają przy każdym commicie po `pre-commit install`. Commitujcie
w aktywnym środowisku `asi-ml`.

CI (GitHub Actions, `.github/workflows/ci.yml`) przy każdym pushu do `main` i każdym PR:

1. buduje środowisko z `environment.yml` i sprawdza wersje bibliotek;
2. uruchamia pre-commit na wszystkich plikach;
3. uruchamia `pytest`;
4. gdy w repozytorium jest `metrics.json`, wykonuje notebook 02 od początku do końca na
   próbce CI i sprawdza wynik;
5. publikuje raport Definition of Done w podsumowaniu joba.

CI nie korzysta z sekretów, W&B ani AutoGluona.

## Definition of Done Sprintu 1

- CI na `main` jest zielone, a żaden test z `tests/test_project.py` nie jest pominięty.
- Świeży klon → środowisko → dane → notebook 02 od zera → `metrics.json`.
- Kontrakt danych potwierdza dokładnie dwie klasy targetu i obecność klasy pozytywnej.
- LogisticRegression porównana z DummyClassifier na metryce głównej.
- `metrics.json` z pełnych danych przechodzi walidację.
- Karta projektu i diagram v0 są uzupełnione.
- Każda osoba ma owned item z merytorycznym review innej osoby.

Pełna lista i kroki: [`docs/sprints/SPRINT_1.md`](docs/sprints/SPRINT_1.md).

## Architektura i scaffold S1–S6

Docelowy system budujemy warstwami — każdy sprint aktywuje i rozwija kolejną:

dane → pipeline → eksperymenty i artefakt → API i stan → UI i compose → chmura

Cały docelowy scaffold jest widoczny od początku, ale **aktywny jest tylko Sprint 1**.
Katalogi przyszłych sprintów zawierają README oznaczone „Scaffold for Sprint N — do not
implement before this sprint.”: opisują, co powstanie, w którym sprincie i z jakim kontraktem.
To nie są rozwiązania ani zadania do wykonania wcześniej. Kod Sprintu 1 nie korzysta z żadnego
z tych elementów.

| Element / katalog | Sprint | Rola |
|---|---|---|
| `src/asi_project/datasets.yaml` | S1 | kontrakt datasetów (prowadząca) |
| `project.yaml` | S1 | decyzje zespołu: dataset, typy cech, split |
| `src/asi_project/` (`config`, `data`, `model`, `metrics`, `download`) | S1 | kontrakt danych, trzy typy przetwarzania, baseline, metryki |
| `notebooks/` | S1 | EDA i baseline |
| `data/01_raw/` | S1 | pełne dane (poza gitem) i próbka CI |
| `scripts/` | S1, rozszerzany w S3–S6 | dane, próbka CI, środowisko, DoD; później smoke modelu i smoke API |
| `tests/` | S1, rozszerzany w S2 i S4 | testy kontraktów; później testy nodów (`tests/pipelines/`) i API (`tests/api/`) |
| `.github/workflows/ci.yml` | S1 → S6 | CI rośnie razem z systemem |
| `conf/` (`base`, `local`, `ci`) | S2 | konfiguracja Kedro |
| `src/asi_project/pipelines/` | S2 → S3 | pipeline'y `data_processing` i `data_science` |
| `data/02_intermediate/`, `data/06_models/`, `data/08_reporting/` | S2 → S3 | wyjścia pipeline'u (poza gitem) |
| pakiet modelu (opis w `src/asi_project/README.md`) | S3 | katalog z modelem i `metadata.json` |
| `docs/model_card.md` | S3 | Model Card |
| `src/asi_project/api/` | S4 | usługa: kontrakt, ustawienia, persistence |
| `docker/` | S4 → S5 | obrazy API i UI, docker compose |
| `ui/` | S5 | interfejs Streamlit |
| `deploy/` | S6 | Cloud Run, Secret Manager, release |
| `docs/adr/` | S2 → S6 | ADR-1, ADR-2, ADR-3 |
| `docs/sprints/`, `github_issues/` | S1–S6 | wymagania sprintów |

Ogólną architekturę warstw opisuje [`docs/architecture.md`](docs/architecture.md).
Przypięte instalacje kolejnych sprintów: `requirements/preflight-s2.txt` (Kedro, pod koniec S1)
i `requirements/preflight-s3.txt` (W&B i AutoGluon, pod koniec S2).
