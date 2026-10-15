# Sprint 2 — Reprodukowalny pipeline

**Daty:** 29.10.2026 – 12.11.2026
**Spotkania:** 29.10 (start Sprintu 2), 05.11 oraz 12.11 (zamknięcie Sprintu 2 i start Sprintu 3)
**Deadline:** stan gałęzi `main` na początku zajęć 12.11.2026

## Cel

Zespół przenosi proces treningowy z notebooka do Kedro, tak aby cały proces od danych
do modelu i metryk można było odtworzyć jedną komendą.


## Co zrobicie w tym sprincie

W Sprincie 1 przygotowaliście poprawny baseline głównie w notebooku.

Teraz przeniesiecie ten proces do **Kedro**, tak aby cały trening dało się odtworzyć jedną
komendą, bez ręcznego wykonywania komórek notebooka.

Na koniec sprintu:

```bash
kedro run
```

ma przejść przez cały proces:

```text
surowe dane
→ walidacja
→ input normalization
→ training-only filtering
→ split train/test
→ model preprocessing
→ trening modelu
→ ewaluacja
→ zapis modelu i metryk
```

Notebook przestaje być głównym miejscem, w którym „dzieje się” trening. Źródłem prawdy staje
się pipeline w kodzie.

---

## Najważniejsza idea Sprintu 2

Pipeline ma być **reprodukowalny**.

To znaczy, że inna osoba po sklonowaniu repozytorium powinna móc uruchomić ten sam proces i
otrzymać model oraz metryki bez ręcznego odtwarzania kolejnych kroków.

W tym sprincie odpowiadacie na pytanie:

> Gdzie powinna znajdować się logika przetwarzania, żeby działała tak samo przy każdym
> uruchomieniu i żeby później dało się jej użyć również podczas predykcji?

---

## Co nowego pojawia się w tym sprincie

### Kedro

Kedro pomaga uporządkować pipeline ML jako zestaw kroków połączonych w logiczną całość.

Nie chodzi o to, żeby „przepisać notebook do Kedro 1:1”.

Chodzi o to, żeby:

- logika była w funkcjach i kodzie;
- dane wejściowe i wyjściowe były jawne;
- parametry nie były rozsiane po notebookach;
- pipeline można było uruchomić jedną komendą;
- te same kroki działały lokalnie i w CI.

### Node

**Node** to pojedynczy krok pipeline'u.

Najlepiej myśleć o nim jak o funkcji:

```text
wejście → operacja → wyjście
```

Przykład:

```text
surowe dane → walidacja → zwalidowane dane
```

albo:

```text
train data → trening modelu → model
```

Node powinien robić jedną jasno określoną rzecz.

### Pipeline

**Pipeline** to kilka nodów połączonych w kolejności wynikającej z przepływu danych.

W tym sprincie tworzycie dwa pipeline'y:

1. `data_processing`
2. `data_science`

### Data Catalog

Kedro Data Catalog opisuje, **skąd dane są czytane i gdzie są zapisywane**.

Dzięki temu node nie musi znać konkretnej ścieżki pliku.

Zamiast pisać w kodzie:

```python
pd.read_csv("data/01_raw/sample.csv")
```

pipeline korzysta z nazwy datasetu z catalogu.

### Parameters

Wartości, które mogą się zmieniać między uruchomieniami, trzymamy w konfiguracji, a nie
w kodzie.

Przykład:

- `test_size`;
- `random_state`;
- parametry splitu.

Takie wartości trafiają do:

```text
parameters.yml
```

### Środowiska konfiguracji

W projekcie używamy trzech środowisk:

- `base` — wspólna konfiguracja;
- `local` — lokalne ustawienia zespołu;
- `ci` — konfiguracja dla CI i małej próbki danych.

Dzięki temu ten sam pipeline może działać na pełnych danych lokalnie i na małej próbce w CI.

---

## Nadal obowiązują trzy rodzaje przetwarzania

Sprint 2 **nie zmienia** zasad z poprzedniego sprintu.

### Input normalization

Operacje możliwe do wykonania dla pojedynczego nowego rekordu.

Kod pozostaje w:

```text
src/asi_project/data.py
```

i jest używany jako node w pipeline.

### Training-only filtering

Operacje wykonywane wyłącznie podczas przygotowania danych treningowych.

Przykłady:

- usunięcie rekordów bez targetu;
- deduplikacja.

Nie są wykonywane podczas predykcji pojedynczego rekordu.

### Model preprocessing

Operacje wymagające `fit()`, np.:

- imputacja;
- skalowanie;
- kodowanie kategorii.

Pozostają częścią sklearn `Pipeline`.

Nie przenosimy ich do osobnego node'a tylko dlatego, że używamy Kedro.

---

## Co macie zrobić

### Krok 1. Sprawdźcie Kedro

Na początku sprintu upewnijcie się, że pre-flight ze Sprintu 1 działa:

```bash
kedro info
```

Jeśli Kedro nie jest zainstalowane:

```bash
python -m pip install -r requirements/preflight-s2.txt -c constraints.txt
```

---

### Krok 2. Uruchomcie przygotowany scaffold

W repozytorium od początku znajdują się katalogi przygotowane pod Sprint 2.

Najważniejsze miejsca:

```text
conf/
src/asi_project/pipelines/
tests/pipelines/
docs/adr/
```

Nie twórzcie równoległej struktury obok scaffoldingu.

Rozwijajcie istniejące katalogi.

---

### Krok 3. Zbudujcie pipeline `data_processing`

Pipeline:

```text
src/asi_project/pipelines/data_processing/
```

ma odpowiadać za przygotowanie danych przed modelowaniem.

Kolejność:

```text
walidacja kontraktu
→ input normalization
→ training-only filtering
```

Wykorzystajcie istniejącą logikę z:

```text
src/asi_project/data.py
```

Nie kopiujcie tej samej logiki do nowych funkcji bez potrzeby.

Celem jest ponowne użycie kodu ze Sprintu 1.

---

### Krok 4. Zbudujcie pipeline `data_science`

Pipeline:

```text
src/asi_project/pipelines/data_science/
```

ma odpowiadać za:

```text
split train/test
→ trening sklearn Pipeline
→ ewaluację
```

Split musi być zgodny z kontraktem wybranego datasetu.

Sklearn `Pipeline` nadal zawiera:

```text
model preprocessing
+ model
```

Po uruchomieniu pipeline'u mają powstać:

- model;
- metryki.

---

### Krok 5. Przenieście parametry do konfiguracji

Parametry, które nie powinny być wpisane na stałe w kodzie, przenieście do konfiguracji.

Przykłady:

```text
test_size
random_state
parametry splitu
```

Umieśćcie je w odpowiednim:

```text
parameters.yml
```

Kod powinien otrzymywać te wartości z konfiguracji.

---

### Krok 6. Uzupełnijcie Data Catalog

Skonfigurujcie catalog tak, żeby pipeline korzystał z nazw datasetów, a nie z wpisanych na
sztywno ścieżek do plików.

Używajcie klas Kedro kończących się na:

```text
...Dataset
```

zgodnie z wersją Kedro używaną w kursie.

W catalogu powinny znaleźć się co najmniej dane potrzebne przez pipeline oraz jego ważne
wyjścia.

---

### Krok 7. Skonfigurujcie środowisko `ci`

Pipeline musi działać również na małej próbce danych w CI.

Przygotujcie konfigurację:

```text
conf/ci/
```

Środowisko `ci` ma korzystać z próbki:

```text
data/01_raw/sample.csv
```

Pełne dane pozostają lokalne i poza Gitem.

---

### Krok 8. Dodajcie testy nodów

Uzupełnijcie:

```text
tests/pipelines/
```

Testujcie najważniejsze funkcje używane jako nody.

Nie chodzi o testowanie samego Kedro.

Testujcie waszą logikę, np.:

- czy przygotowanie danych zwraca oczekiwany wynik;
- czy split ma poprawną strukturę;
- czy node treningowy zwraca model;
- czy node ewaluacyjny zwraca oczekiwane metryki.

---

### Krok 9. Napiszcie ADR-1

W Sprincie 2 powstaje pierwszy **Architecture Decision Record**.

ADR to krótki zapis ważnej decyzji architektonicznej.

Nie jest to esej.

Ma odpowiedzieć na pytanie:

> Gdzie w naszym systemie żyją różne rodzaje przetwarzania i dlaczego?

W ADR-1 zapiszcie, że:

- input normalization jest wspólne dla treningu i późniejszego API;
- training-only filtering działa tylko podczas przygotowania danych treningowych;
- model preprocessing jest częścią modelu/sklearn `Pipeline`.

ADR powinien też krótko wyjaśniać, **dlaczego** taki podział został wybrany.

Plik trafia do:

```text
docs/adr/
```

---

### Krok 10. Dodajcie Kedro quickstart do README

W `README.md` dopiszcie krótką instrukcję, jak uruchomić pipeline.

Powinna wystarczyć osobie, która pierwszy raz klonuje repozytorium.

Minimum:

```bash
kedro run
```

oraz informacja:

- skąd pobrać dane;
- jakiego środowiska użyć;
- gdzie znaleźć wynik.

---

## Definition of Done

- Kedro działa w przypiętej wersji z `requirements/preflight-s2.txt`.
- Pipeline `data_processing` wykonuje walidację, input normalization i training-only filtering.
- Pipeline `data_science` wykonuje split, trening i ewaluację.
- Pipeline korzysta z logiki przygotowanej w Sprincie 1 zamiast ją duplikować.
- Model preprocessing nadal znajduje się wewnątrz sklearn `Pipeline`.
- Parametry są przeniesione do konfiguracji.
- Data Catalog opisuje wejścia i wyjścia pipeline'u.
- `conf/ci/` pozwala uruchomić pipeline na próbce CI.
- Testy nodów przechodzą.
- `kedro run` na pełnych danych tworzy model i metryki.
- `kedro run --env ci` działa w CI.
- Notebook nie jest już wymagany do trenowania baseline'u.
- ADR-1 jest napisany i zmergowany.
- README zawiera sekcję „Kedro quickstart”.
- CI na `main` jest zielone.
- Każda osoba w zespole ma własny obszar pracy i zrobiła merytoryczne review pracy innej osoby.

---

## Jak sprawdzić, że Sprint 2 jest gotowy

Lokalnie na pełnych danych uruchomcie:

```bash
kedro run
```

Pipeline ma zakończyć się modelem i metrykami.

Następnie sprawdźcie wersję CI:

```bash
kedro run --env ci
```

Powinna działać na próbce danych.

Uruchomcie również:

```bash
pytest
pre-commit run --all-files
```

Na koniec wykonajcie smoke test na świeżym klonie:

```text
świeży klon
→ środowisko
→ pobranie danych
→ kedro run
→ model i metryki
```

Metryki powinny być zgodne z baseline'em ze Sprintu 1 w granicach rozsądnej tolerancji.

---

## Przygotowanie do Sprintu 3

Pod koniec Sprintu 2 każda osoba przygotowuje środowisko do eksperymentów.

### W&B

Każda osoba:

- ma konto W&B;
- loguje się przez:

```bash
wandb login
```

- dołącza do projektu zespołu.

W tym momencie nie musicie jeszcze wykonywać pełnego zestawu eksperymentów.

### AutoGluon

Zainstalujcie środowisko Sprintu 3:

```bash
python -m pip install -r requirements/preflight-s3.txt -c constraints.txt
```

Następnie uruchomcie:

```bash
python scripts/check_env.py --autogluon
```

Test ma wykonać mini-trening i potwierdzić, że AutoGluon działa na waszym komputerze.

---

## Podział pracy w zespole

Przykładowe obszary odpowiedzialności:

- pipeline `data_processing`;
- pipeline `data_science`;
- Data Catalog i konfiguracja;
- testy i CI;
- ADR-1 i README.

Nie musicie dzielić pracy dokładnie w ten sposób.

Każda osoba:

- ma co najmniej jeden własny obszar pracy;
- robi merytoryczne review przynajmniej jednego PR innej osoby.

Integrator Sprintu 2 pilnuje:

- kompletności checklisty;
- smoke testu na świeżym klonie;
- przygotowania pre-flightu Sprintu 3.

---

## OPTIONAL

Jeśli zespół skończy zakres obowiązkowy wcześniej, może dodatkowo:

- uruchomić Kedro-Viz;
- dodać hooki Kedro.

Elementy OPTIONAL nie są wymagane do zaliczenia Sprintu 2.

---

## Najczęstsze błędy w tym sprincie

### 1. Przepisywanie notebooka 1:1 do jednego wielkiego node'a

Pipeline ma rozdzielać logiczne kroki.

Nie twórzcie jednego node'a typu:

```text
load_clean_split_train_evaluate_everything()
```

### 2. Duplikowanie logiki ze Sprintu 1

Jeśli input normalization istnieje już w:

```text
src/asi_project/data.py
```

pipeline powinien używać tej logiki, a nie jej drugiej kopii.

### 3. Przenoszenie model preprocessing poza sklearn Pipeline

Imputacja, skalowanie i kodowanie wymagające `fit()` nadal należą do modelu.

### 4. Ścieżki i parametry wpisane na stałe w kodzie

Jeśli wartość należy do konfiguracji, nie wpisujcie jej bezpośrednio w node.

---

## Najważniejszy rezultat Sprintu 2

Po tym sprincie powinniście móc odpowiedzieć:

> Czy osoba, która nie zna naszego notebooka, może sklonować repozytorium, uruchomić
> `kedro run` i odtworzyć trening modelu?

Jeżeli odpowiedź brzmi „tak”, pipeline spełnia swój podstawowy cel.
