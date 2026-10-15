# Sprint 1 — Problem, dane i poprawny baseline

**Daty:** 15.10.2026 – 29.10.2026
**Spotkania:** 15.10, 22.10 oraz 29.10 (zamknięcie Sprintu 1 i start Sprintu 2)
**Deadline:** stan gałęzi `main` na początku zajęć 29.10.2026

## Cel

Zespół wybiera dataset, ustala zasady korzystania z danych i przygotowuje poprawny baseline
w sklearn `Pipeline` z działającymi testami i CI.


## Co zrobicie w tym sprincie

W pierwszym sprincie wybierzecie dataset dla projektu zespołowego, poznacie jego strukturę
i przygotujecie pierwszy poprawny eksperyment ML.

Na koniec sprintu repozytorium ma zawierać:

- opis wybranego problemu i danych;
- zasady korzystania z danych;
- EDA;
- prosty baseline;
- pierwszy model w sklearn `Pipeline`;
- metryki;
- diagram docelowego systemu;
- działające testy i CI.

W tym sprincie **nie używamy jeszcze Kedro, W&B ani AutoGluona**.

---

## Najważniejsza idea Sprintu 1

Zanim zaczniecie budować pipeline i aplikację, musicie ustalić, **jak wasz system rozumie dane**
oraz sprawdzić, czy pierwszy eksperyment jest poprawny.

### Co oznacza kontrakt danych?

W tym projekcie **kontrakt danych (data contract)** to zestaw uzgodnionych zasad określających,
jak zespół korzysta z wybranego datasetu.

Nie jest to osobny plik ani dodatkowa technologia. Chodzi o to, żeby notebooki, kod treningowy,
model i późniejsze API interpretowały dane w ten sam sposób.

Kontrakt danych obejmuje przede wszystkim:

- jaki dataset wykorzystujecie;
- jaki jest target;
- która klasa jest klasą pozytywną;
- które kolumny wolno wykorzystać jako cechy (**ALLOWED FEATURES**);
- których kolumn nie wolno używać (**EXCLUDED FEATURES**);
- które cechy traktujecie jako numeryczne, a które jako kategoryczne;
- jaki jest moment predykcji;
- jak dzielicie dane na train i test;
- jak traktujecie braki danych, wartości specjalne i ewentualne duplikaty;
- które operacje należą do przygotowania danych, a które do modelu.

Część kontraktu jest już określona przez prowadzącą w:

- `docs/datasets.md`;
- `src/asi_project/datasets.yaml`.

Zespół nie zmienia targetu, klasy pozytywnej ani list ALLOWED / EXCLUDED FEATURES.

Decyzje zespołu zapisujecie przede wszystkim w:

- `project.yaml`;
- `notebooks/01_eda.ipynb`;
- `src/asi_project/data.py`;
- karcie projektu w `README.md`.

---

## Trzy rodzaje przetwarzania danych

W tym sprincie rozdzielamy trzy różne rzeczy.

### 1. Input normalization

To proste operacje, które można wykonać również później dla **jednego nowego rekordu**
przesłanego do API.

Nie mogą korzystać z:

- targetu;
- informacji o innych rekordach;
- statystyk całego datasetu.

Ta sama funkcja będzie później używana podczas inferencji.

Przykład: ujednolicenie formatu wartości tekstowej albo zamiana umownej wartości specjalnej
na brak danych.

Kod: `normalize_input()` w `src/asi_project/data.py`.

### 2. Training-only filtering

To operacje wykonywane tylko podczas przygotowania danych treningowych.

Przykłady:

- usunięcie rekordu bez targetu;
- usunięcie duplikatów.

Takich operacji **nie wykonujemy podczas predykcji pojedynczego nowego rekordu**.

Kod: `filter_training_rows()` w `src/asi_project/data.py`.

Jeśli wasz dataset nie wymaga takiego filtrowania, nie dodawajcie go na siłę. Decyzję opiszcie
w notebooku EDA.

### 3. Model preprocessing

To operacje, które wymagają `fit()`, ponieważ uczą się czegoś na danych treningowych.

Przykłady:

- imputacja medianą;
- skalowanie;
- kodowanie kategorii.

Te operacje muszą być częścią sklearn `Pipeline` i nie powinny trafiać do `normalize_input()`.

Kod: `src/asi_project/model.py`.

---

## Co macie zrobić

### Krok 1. Przygotujcie repozytorium i środowisko

W aktywnym środowisku `asi-ml` uruchomcie:

```bash
conda env update -n asi-ml -f environment.yml --prune
python -m pip install --no-deps -e .
pre-commit install
python scripts/check_env.py
pytest
```

Pracujcie przez gałęzie i Pull Requesty do `main`.

Każdy PR musi być przejrzany przez osobę inną niż autor.

---

### Krok 2. Wybierzcie dataset

Przeczytajcie:

```text
docs/datasets.md
```

Wybierzcie jeden dataset z zatwierdzonej listy i wpiszcie jego identyfikator do:

```text
project.yaml
```

Sprawdźcie szczególnie:

- target;
- klasę pozytywną;
- ALLOWED FEATURES;
- EXCLUDED FEATURES;
- moment predykcji;
- strategię splitu.

---

### Krok 3. Uzupełnijcie kartę projektu

W `README.md` uzupełnijcie:

- zespół i integratora Sprintu 1;
- wybrany dataset;
- źródło i licencję;
- DOI;
- datę pobrania danych;
- SHA-256 pobranego pliku;
- informację o danych osobowych;
- target i klasę pozytywną;
- główną metrykę wraz z uzasadnieniem;
- użytkownika systemu;
- decyzję, którą ma wspierać model.

---

### Krok 4. Pobierzcie dane

Pełne dane pobierzcie skryptem:

```bash
python scripts/download_data.py
```

Pełne dane **nie mogą trafić do Gita**.

Zapiszcie SHA-256 z `fingerprint.json` w karcie projektu.

Następnie utwórzcie małą próbkę używaną przez testy i CI:

```bash
python scripts/make_ci_sample.py
```

W repozytorium ma znaleźć się:

```text
data/01_raw/sample.csv
```

---

### Krok 5. Zróbcie EDA

Uzupełnijcie:

```text
notebooks/01_eda.ipynb
```

Sprawdźcie co najmniej:

- liczbę rekordów i kolumn;
- typy danych;
- rozkład targetu;
- braki danych;
- wartości specjalne;
- duplikaty;
- właściwości ALLOWED FEATURES.

EDA nie ma być tylko zbiorem wykresów.

Po każdej ważnej obserwacji zapiszcie **decyzję**, np.:

- czy dana wartość specjalna powinna zostać zamieniona na brak danych;
- czy potrzebne jest training-only filtering;
- które cechy traktujecie jako numeryczne;
- które cechy traktujecie jako kategoryczne.

---

### Krok 6. Zaimplementujcie przygotowanie danych

W:

```text
src/asi_project/data.py
```

uzupełnijcie miejsca TODO.

#### `normalize_input()`

Dodajcie reguły input normalization właściwe dla waszego datasetu.

Funkcja musi być inference-safe, czyli działać na pojedynczym rekordzie bez targetu i bez
statystyk całego zbioru.

#### `filter_training_rows()`

Dodajcie tylko te operacje, które rzeczywiście są potrzebne podczas treningu.

Jeśli dataset nie wymaga filtrowania, pozostawcie funkcję prostą i opiszcie decyzję w EDA.

Po zmianach uruchomcie:

```bash
pytest
```

---

### Krok 7. Zbudujcie baseline

Uzupełnijcie:

```text
src/asi_project/model.py
notebooks/02_baseline.ipynb
```

Macie przygotować dwa modele:

1. `DummyClassifier`;
2. `LogisticRegression` wewnątrz sklearn `Pipeline`.

W `Pipeline` umieśćcie model preprocessing wymagający `fit()`, np.:

- imputację;
- skalowanie;
- kodowanie kategorii.

Użyjcie strategii splitu zapisanej w kontrakcie datasetu.

Policzcie:

- accuracy;
- precision;
- recall;
- F1;
- confusion matrix.

Dodatkowo model ma obsługiwać:

```python
predict_proba()
```

Porównajcie `LogisticRegression` z `DummyClassifier` na głównej metryce projektu.

Na pełnych danych zapiszcie:

```text
metrics.json
```

---

### Krok 8. Narysujcie architekturę v0

Uzupełnijcie:

```text
docs/architecture.md
```

Diagram ma pokazywać docelowy system, który będziecie rozwijać w kolejnych sprintach:

```text
dane
  ↓
pipeline treningowy
  ↓
model
  ↓
API
  ↓
UI
```

oraz osobno miejsce na persistence i późniejsze wdrożenie.

Nie implementujcie jeszcze elementów przyszłych sprintów.

---

## Definition of Done

- Dataset jest wybrany i wpisany do `project.yaml`.
- Karta projektu w `README.md` jest kompletna.
- Pełne dane są pobierane skryptem i nie znajdują się w repozytorium.
- `data/01_raw/sample.csv` znajduje się w repozytorium i zawiera obie klasy.
- `project.yaml` zawiera decyzje zespołu dotyczące typów cech i splitu.
- `validate()` przechodzi dla danych projektu.
- `normalize_input()` jest zaimplementowane i przechodzi testy inference-safe.
- `filter_training_rows()` jest zaimplementowane, jeśli dataset tego wymaga.
- `notebooks/01_eda.ipynb` zawiera EDA oraz zapisane decyzje.
- `DummyClassifier` i `LogisticRegression` są porównane.
- `LogisticRegression` działa wewnątrz sklearn `Pipeline`.
- `predict_proba()` działa.
- `metrics.json` pochodzi z pełnych danych.
- `docs/architecture.md` zawiera diagram v0.
- CI na `main` jest zielone.
- Żaden wymagany test z `tests/test_project.py` nie jest pominięty.
- Każda osoba w zespole ma własne zadanie i zrobiła merytoryczne review pracy innej osoby.

---

## Jak sprawdzić, że Sprint 1 jest gotowy

Najpierw uruchomcie:

```bash
pytest
pre-commit run --all-files
python scripts/check_dod.py --sprint 1
```

Przed zamknięciem sprintu:

```bash
python scripts/check_dod.py --sprint 1 --strict
```

Dodatkowo osoba, która **nie tworzyła baseline'u**, wykonuje smoke test na świeżym klonie:

```text
świeży klon
→ środowisko
→ download_data.py
→ notebook 02: Restart & Run All
→ metrics.json
```

Jeśli ten proces działa bez ręcznego poprawiania plików, baseline jest odtwarzalny.

---

## Przygotowanie do Sprintu 2

Pod koniec Sprintu 1 każda osoba instaluje Kedro i sprawdza, czy działa:

```bash
python -m pip install -r requirements/preflight-s2.txt -c constraints.txt
kedro info
```

W Sprincie 1 **nie budujecie jeszcze pipeline'u Kedro**. To tylko sprawdzenie środowiska przed
kolejnym sprintem.

---

## Podział pracy w zespole

Przykładowe obszary odpowiedzialności:

- dataset, karta projektu i kontrakt danych;
- EDA;
- input normalization i training-only filtering;
- baseline i metryki;
- CI, testy i diagram architektury.

Nie musicie dzielić pracy dokładnie w ten sposób.

Każda osoba:

- ma co najmniej jeden własny obszar pracy;
- robi merytoryczne review przynajmniej jednego PR innej osoby.

Integrator Sprintu 1 pilnuje:

- kompletności Definition of Done;
- smoke testu;
- przygotowania krótkiego demo na zamknięcie sprintu.

W parach obowiązuje ten sam zakres CORE. Oznacza to większą liczbę zadań przypadającą na jedną
osobę.

---

## OPTIONAL

Jeśli zespół skończy zakres obowiązkowy wcześniej, może dodatkowo:

- rozbudować EDA;
- opisać ograniczenia datasetu, np. zakres czasowy, możliwe biasy i braki danych.

Elementy OPTIONAL nie są wymagane do zaliczenia Sprintu 1.

---

## Najczęstszy błąd w tym sprincie

Nie przenoście do `normalize_input()` operacji, które wymagają nauczenia parametrów na danych.

Przykład:

```text
uzupełnienie braków medianą
```

wymaga wyliczenia mediany na danych treningowych, więc należy do sklearn `Pipeline`, a nie do
input normalization.

Testy projektu mają wykrywać takie przypadki.
