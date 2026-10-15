# Sprint 4 — API, persistence i pierwszy kontener

**Daty:** 26.11.2026 – 17.12.2026
**Spotkania:** 26.11 (start Sprintu 4), 03.12, 10.12 oraz 17.12 (zamknięcie Sprintu 4 i start Sprintu 5)
**Deadline:** stan gałęzi `main` na początku zajęć 17.12.2026

## Cel

Zespół udostępnia model przez FastAPI, dodaje walidację, persistence i prosty token dostępu,
a następnie uruchamia usługę w kontenerze.


## Co zrobicie w tym sprincie

Macie już wybrany i zapisany model produkcyjny.

W tym sprincie udostępnicie go przez **FastAPI**, tak aby inny program mógł wysłać dane wejściowe
i otrzymać predykcję.

Dodatkowo:

- dodacie walidację wejścia i odpowiedzi;
- zabezpieczycie endpoint predykcji prostym tokenem `API_KEY`;
- zapiszecie wykonane predykcje przez warstwę persistence;
- uruchomicie API w Dockerze;
- przygotujecie pierwszy wspólny smoke test.

Na koniec sprintu model ma działać jako usługa uruchomiona w kontenerze.

---

## Najważniejsza idea Sprintu 4

Do tej pory model był elementem pipeline'u ML.

Teraz staje się częścią aplikacji.

W tym sprincie odpowiadacie na pytania:

> Jak wygląda kontrakt między modelem a światem zewnętrznym?

oraz:

> Gdzie zapisujemy stan systemu?

---

## Co nowego pojawia się w tym sprincie

### API

API pozwala innym programom korzystać z modelu bez znajomości kodu treningowego.

W tym kursie tworzycie dwa podstawowe endpointy:

```text
GET /healthz
POST /predict
```

`/healthz` służy do sprawdzenia, czy usługa działa.

`/predict` przyjmuje dane wejściowe i zwraca predykcję.

---

### Kontrakt API

Kontrakt API określa:

- jakie dane można wysłać do `/predict`;
- które pola są wymagane;
- jakie mają typy;
- jak wygląda odpowiedź;
- jakie błędy może zwrócić usługa.

Schemat wejścia i odpowiedzi definiujecie przez Pydantic.

Odpowiedź `/predict` powinna zawierać co najmniej:

- etykietę predykcji;
- prawdopodobieństwo klasy pozytywnej;
- wersję modelu.

---

### Walidacja na granicy usługi

API jest granicą między waszym systemem a światem zewnętrznym.

Nie zakładamy, że każdy request jest poprawny.

Pydantic sprawdza strukturę wejścia przed wykonaniem predykcji.

Przykład:

- błędny typ danych;
- brak wymaganego pola;
- niepoprawna wartość.

W takich przypadkach klient powinien dostać poprawny błąd 4xx zamiast błędu wewnętrznego 5xx.

---

### Model ładowany raz

Model nie powinien być ładowany z dysku przy każdym requestcie.

Powinien zostać wczytany raz podczas uruchamiania usługi i później być używany do kolejnych
predykcji.

To ogranicza czas odpowiedzi i zużycie zasobów.

---

### Input normalization i model preprocessing w API

Zasady z wcześniejszych sprintów nadal obowiązują.

Przed przekazaniem rekordu do modelu API wykonuje:

```text
input normalization
```

Natomiast:

```text
model preprocessing
```

pozostaje częścią zapisanego modelu/sklearn `Pipeline`.

API nie powinno ponownie implementować skalowania, imputacji ani kodowania kategorii.

---

### Persistence

Persistence oznacza zapis stanu poza bieżącym requestem.

W tym sprincie zapisujecie informacje o wykonanych predykcjach.

Warstwa persistence ma dwa tryby:

```text
sql
disabled
```

`sql` oznacza zapis do bazy danych.

`disabled` oznacza, że predykcje działają bez zapisywania stanu.

Ten sam kod API powinien działać w obu trybach.

---

### Repository

Nie zapisujemy rekordów do bazy bezpośrednio w endpointzie.

Tworzymy warstwę repository, która odpowiada za zapis danych.

Dzięki temu endpoint:

- przyjmuje request;
- wykonuje predykcję;
- przekazuje dane do repository.

Nie musi znać szczegółów SQL.

To ułatwia również testowanie.

---

### SQLite

W Sprincie 4 używamy SQLite jako prostej lokalnej bazy.

Model tabeli definiujecie w SQLAlchemy.

Nie tworzycie tabel ręcznie przez SQL DDL.

Plik SQLite ma znajdować się poza obrazem kontenera i być podłączony przez wolumen.

W Sprincie 5 ten sam kontrakt persistence zostanie użyty z PostgreSQL.

---

### Konfiguracja i sekret

Nie wpisujemy ustawień na stałe do kodu.

Konfiguracja jest pobierana ze zmiennych środowiskowych przez `pydantic-settings`.

Przykładowe ustawienia:

- `DATABASE_URL`;
- tryb persistence;
- adres modelu;
- `API_KEY`.

Lokalnie wartości mogą znajdować się w `.env`.

Do repozytorium trafia tylko:

```text
.env.example
```

bez prawdziwych sekretów.

---

### `API_KEY`

`API_KEY` jest prostym tokenem chroniącym endpoint `/predict`.

To **nie jest system logowania użytkowników**.

W tym kursie chodzi tylko o pokazanie, że sekret:

- nie powinien być hardcodowany w kodzie;
- nie powinien trafić do Git;
- powinien być dostarczany przez konfigurację.

`/healthz` pozostaje dostępne bez tokenu.

---

### Logi

Każda predykcja powinna wygenerować jedną linię logu JSON.

Log ma być ustrukturyzowany, żeby później dało się go łatwo przeglądać w Cloud Logging.

Nie logujcie sekretów.

---

### Docker

Na koniec sprintu API uruchamiacie w kontenerze.

Dockerfile powinien zawierać tylko to, czego potrzebuje usługa.

W obrazie API nie używamy Condy.

Wersje bibliotek potrzebnych do wczytania modelu muszą być zgodne z tymi, z których korzystał
model podczas treningu.

---

## Co macie zrobić

### Krok 1. Przygotujcie strukturę API

Rozwijajcie scaffold:

```text
src/asi_project/api/
tests/api/
```

Nie twórzcie drugiej, równoległej aplikacji poza przygotowaną strukturą.

---

### Krok 2. Zaimplementujcie `/healthz`

Endpoint:

```text
GET /healthz
```

powinien zwracać co najmniej:

- status usługi;
- wersję modelu;
- aktualny tryb persistence.

Przykładowa odpowiedź może mieć postać:

```json
{
  "status": "ok",
  "model_version": "...",
  "persistence": "sql"
}
```

Dokładny format może wynikać ze scaffoldingu projektu.

---

### Krok 3. Zdefiniujcie schemat wejścia `/predict`

Przygotujcie model Pydantic odpowiadający cechom wymaganym przez wasz model.

Schemat musi być zgodny z kontraktem danych z wcześniejszych sprintów.

Nie dodawajcie EXCLUDED FEATURES tylko dlatego, że znajdują się w oryginalnym CSV.

---

### Krok 4. Zaimplementujcie `/predict`

Endpoint:

```text
POST /predict
```

powinien wykonywać:

```text
walidacja requestu
→ input normalization
→ model.predict()
→ model.predict_proba()
→ przygotowanie odpowiedzi
→ opcjonalny zapis przez repository
```

Odpowiedź powinna zawierać:

- etykietę;
- prawdopodobieństwo klasy pozytywnej;
- wersję modelu.

---

### Krok 5. Ładujcie model tylko raz

Model produkcyjny ze Sprintu 3 powinien zostać wczytany podczas uruchamiania aplikacji.

Nie ładujcie artefaktu ponownie wewnątrz każdego requestu.

Sprawdźcie również, że API korzysta z tej samej funkcji wczytywania modelu, która była używana
w smoke teście Sprintu 3.

---

### Krok 6. Dodajcie konfigurację przez `pydantic-settings`

Przygotujcie ustawienia aplikacji pobierane ze zmiennych środowiskowych.

Lokalnie można używać:

```text
.env
```

Do repozytorium dodajcie:

```text
.env.example
```

z nazwami zmiennych, ale bez prawdziwych sekretów.

---

### Krok 7. Dodajcie `API_KEY`

`/predict` ma wymagać poprawnego tokenu.

Token przekazujcie w nagłówku zgodnie z kontraktem projektu.

Oczekiwane zachowanie:

```text
poprawny token → predykcja
brak tokenu → 401
błędny token → 401
```

`/healthz` pozostaje otwarte.

---

### Krok 8. Zbudujcie warstwę persistence

Przygotujcie repository z dwoma trybami:

```text
sql
disabled
```

W trybie `sql` każda poprawna predykcja powinna zostać zapisana.

W trybie `disabled` predykcja działa normalnie, ale nic nie jest zapisywane.

Endpoint `/predict` nie powinien zawierać szczegółowej logiki SQL.

---

### Krok 9. Dodajcie SQLite przez SQLAlchemy

W trybie `sql` użyjcie SQLite.

Model tabeli predykcji zdefiniujcie w SQLAlchemy.

Rekord powinien przechowywać co najmniej informacje potrzebne do identyfikacji wykonanej
predykcji, np.:

- timestamp;
- payload wejściowy;
- wynik;
- wersję modelu.

Dokładny schemat ustalcie jako zespół zgodnie ze scaffoldem.

Plik SQLite nie może być zapisany wewnątrz obrazu jako trwałe miejsce danych.

---

### Krok 10. Dodajcie logowanie JSON

Każda wykonana predykcja powinna tworzyć jedną linię logu JSON.

Log powinien zawierać informacje techniczne potrzebne do obserwacji działania usługi.

Nie logujcie:

- `API_KEY`;
- haseł;
- innych sekretów.

---

### Krok 11. Dodajcie testy API

Uzupełnijcie:

```text
tests/api/
```

Testy powinny obejmować co najmniej:

- poprawny request;
- błędny request zwracający 422;
- brak tokenu zwracający 401;
- zły token zwracający 401;
- zapis przez repository do tymczasowej bazy;
- działanie trybu `disabled`.

W testach nie musicie używać prawdziwej produkcyjnej bazy.

---

### Krok 12. Przygotujcie Dockerfile API

Rozwijajcie:

```text
docker/api.Dockerfile
```

Dockerfile powinien:

- uruchamiać FastAPI;
- nie używać Condy;
- korzystać z portu przekazanego przez `$PORT`;
- zawierać biblioteki potrzebne do wczytania modelu;
- być zgodny z `.dockerignore`.

Zbudujcie obraz i uruchomcie go lokalnie.

---

### Krok 13. Podłączcie SQLite przez wolumen

Jeśli API działa w trybie `sql`, plik SQLite powinien być zapisany na wolumenie.

Dzięki temu usunięcie i ponowne uruchomienie kontenera nie musi usuwać bazy.

To jest rozwiązanie lokalne dla Sprintu 4.

Nie traktujemy SQLite jako docelowej bazy dla Cloud Run.

---

### Krok 14. Sprawdźcie limit pamięci

Uruchomcie kontener z limitem pamięci przez:

```text
--memory
```

Celem jest sprawdzenie, ile pamięci potrzebuje usługa z wczytanym modelem.

Ten wynik przyda się później przy konfiguracji Cloud Run.

---

### Krok 15. Przygotujcie wspólny smoke test

Od tego sprintu do końca kursu używacie jednego skryptu smoke dla API.

Smoke powinien sprawdzić:

1. `/healthz`;
2. tryb persistence;
3. `/predict` z poprawnym tokenem;
4. schemat odpowiedzi;
5. zapis rekordu, jeśli persistence = `sql`.

Jeśli persistence = `disabled`, brak zapisu jest poprawnym zachowaniem.

W Sprincie 4 smoke uruchamiacie na lokalnym kontenerze w trybie `sql`.

---

### Krok 16. Przygotujcie szkic ADR-3

ADR-3 będzie rozwijany aż do Sprintu 6.

W tym sprincie zapisujecie pierwszą decyzję:

> Jak model trafia do usługi i obrazu?

Nie musicie jeszcze finalizować decyzji dotyczących całej architektury chmurowej.

To jest tylko pierwsza wersja ADR-3.

Plik trafia do:

```text
docs/adr/
```

---

## Definition of Done

- `/healthz` działa i zwraca status, wersję modelu i tryb persistence.
- `/predict` ma schemat Pydantic zgodny z kontraktem modelu.
- `/predict` zwraca etykietę, prawdopodobieństwo klasy pozytywnej i wersję modelu.
- Model jest ładowany raz przy starcie aplikacji.
- API wykonuje input normalization przed modelem.
- Model preprocessing pozostaje wewnątrz zapisanego modelu.
- Konfiguracja działa przez `pydantic-settings`.
- `.env.example` znajduje się w repozytorium i nie zawiera sekretów.
- `/predict` wymaga poprawnego `API_KEY`.
- Brak lub zły token zwraca 401.
- `/healthz` nie wymaga tokenu.
- Repository obsługuje tryby `sql` i `disabled`.
- SQLite działa przez SQLAlchemy.
- Predykcje są zapisywane w trybie `sql`.
- Każda predykcja generuje log JSON.
- Testy API przechodzą.
- Dockerfile API działa lokalnie.
- Port usługi jest pobierany z `$PORT`.
- SQLite jest podłączone przez wolumen.
- Kontener został sprawdzony z limitem pamięci.
- Wspólny smoke test API przechodzi.
- Szkic ADR-3 jest zmergowany.
- W repozytorium nie ma sekretów.
- CI na `main` jest zielone.
- Każda osoba w zespole ma własny obszar pracy i zrobiła merytoryczne review pracy innej osoby.

---

## Jak sprawdzić, że Sprint 4 jest gotowy

Uruchomcie API w kontenerze w trybie:

```text
persistence = sql
```

z lokalnym `.env`.

Następnie wykonajcie smoke test.

Oczekiwany przebieg:

```text
docker run
→ /healthz
→ persistence = sql
→ /predict z poprawnym API_KEY
→ poprawna odpowiedź
→ rekord zapisany w SQLite
```

Dodatkowo sprawdźcie ręcznie:

```text
/predict bez tokenu → 401
/predict ze złym tokenem → 401
```

Uruchomcie również:

```bash
pytest
pre-commit run --all-files
```

---

## Pre-flight GCP

Do końca Sprintu 4 zespół ma sprawdzić, czy dostęp do GCP działa.

Zakres pre-flightu zależy od wyniku testów przeprowadzonych wcześniej przez prowadzącą.

Sprawdźcie instrukcję:

```text
docs/GCP_CREDENTIALS_PREFLIGHT.md
```

Minimum:

- działające student credentials;
- dostęp do projektu GCP;
- billing lub kredyty, jeśli są wymagane;
- wymagane API są włączone;
- dostęp do Artifact Registry;
- prosty test techniczny.

Rola Viewer dla prowadzącej jest warunkowa.

Jej brak nie blokuje zaliczenia sprintu, jeśli uprawnienia studenckie nie pozwalają na jej
dodanie.

---

## Przygotowanie do Sprintu 5

Każda osoba powinna sprawdzić:

```bash
docker compose version
```

W Sprincie 5 połączycie:

```text
API + UI + Postgres
```

w jeden lokalny system uruchamiany przez Docker Compose.

---

## Podział pracy w zespole

Przykładowe obszary odpowiedzialności:

- kontrakt API i schematy Pydantic;
- wczytywanie modelu i endpoint `/predict`;
- persistence i SQLite;
- konfiguracja i `API_KEY`;
- testy API;
- Dockerfile i test pamięci;
- smoke test;
- szkic ADR-3.

Nie musicie dzielić pracy dokładnie w ten sposób.

Każda osoba:

- ma co najmniej jeden własny obszar pracy;
- robi merytoryczne review przynajmniej jednego PR innej osoby.

Integrator Sprintu 4 pilnuje:

- kompletności checklisty;
- smoke testu;
- braku sekretów w repozytorium;
- wykonania pre-flightu GCP.

---

## OPTIONAL

Jeśli zespół skończy zakres obowiązkowy wcześniej, może dodatkowo:

- dodać endpoint `GET /predictions`;
- dodać Alembic do migracji bazy;
- budować obraz API w CI.

Elementy OPTIONAL nie są wymagane do zaliczenia Sprintu 4.

---

## Najczęstsze błędy w tym sprincie

### 1. Ładowanie modelu przy każdym requestcie

Model powinien zostać wczytany raz przy starcie aplikacji.

---

### 2. Powtarzanie preprocessing w API

API wykonuje input normalization.

Skalowanie, imputacja i kodowanie wymagające `fit()` pozostają wewnątrz modelu.

---

### 3. SQL bezpośrednio w endpointzie

Endpoint nie powinien sam wykonywać szczegółowych operacji bazodanowych.

Od tego jest repository.

---

### 4. Sekret zapisany w kodzie lub repozytorium

`API_KEY` nie może znaleźć się:

- w kodzie;
- w commitowanym `.env`;
- w Dockerfile.

Do repo trafia tylko `.env.example` bez prawdziwej wartości.

---

### 5. Traktowanie SQLite jako docelowej bazy chmurowej

SQLite jest lokalnym rozwiązaniem Sprintu 4.

W Sprincie 5 przejdziecie lokalnie na Postgresa, a w Cloud Run domyślnie będziecie mogli
uruchomić system bez persistence.

---

## Najważniejszy rezultat Sprintu 4

Po tym sprincie powinniście móc odpowiedzieć:

> Czy możemy uruchomić kontener z naszym API, wysłać poprawny request i otrzymać predykcję,
> a w trybie `sql` również zapisać jej wynik?

Jeżeli odpowiedź brzmi „tak”, model przestał być tylko artefaktem ML i stał się działającą
usługą.
