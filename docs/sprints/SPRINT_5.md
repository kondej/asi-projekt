# Sprint 5 — System lokalny: UI, API i Postgres

**Daty:** 17.12.2026 – 07.01.2027
**Spotkania:** 17.12 (start Sprintu 5) oraz 07.01 (zamknięcie Sprintu 5 i start Sprintu 6)
**Deadline:** stan gałęzi `main` na początku zajęć 07.01.2027

## Cel

Zespół łączy Streamlit, FastAPI i PostgreSQL w lokalny system uruchamiany jedną komendą
przez Docker Compose.


## Ważne: realny czas pracy

Przerwa świąteczna trwa od 24.12.2026 do 06.01.2027 i **nie jest planowanym czasem pracy**.

Dlatego zakres Sprintu 5 został ułożony tak, żeby dało się go zamknąć przed przerwą, czyli
realnie do 23.12.

---

## Co zrobicie w tym sprincie

Macie już działające API w Dockerze.

Teraz zbudujecie pierwszy **lokalny system wielousługowy**:

```text
Streamlit UI
    ↓
FastAPI
    ↓
PostgreSQL
```

Wszystkie trzy elementy będą uruchamiane razem przez:

```bash
docker compose up --build
```

Na koniec sprintu użytkownik ma móc:

1. otworzyć Streamlit;
2. wpisać dane do formularza;
3. wysłać je do API;
4. otrzymać predykcję;
5. zapisać wynik w PostgreSQL.

---

## Najważniejsza idea Sprintu 5

W Sprincie 4 uruchamialiście pojedynczą usługę API.

W Sprincie 5 odpowiadacie na pytanie:

> Jak połączyć kilka usług tak, żeby działały razem na różnych komputerach i korzystały z tej
> samej konfiguracji?

Najważniejszą nową koncepcją jest **Docker Compose**.

Streamlit i PostgreSQL są używane w minimalnym zakresie i mają być silnie oparte na przygotowanym
scaffoldzie.

---

## Co nowego pojawia się w tym sprincie

### Docker Compose

Docker Compose pozwala uruchomić kilka powiązanych usług jedną komendą.

W tym sprincie są to:

```text
api
ui
db
```

Każda usługa działa we własnym kontenerze.

Compose opisuje:

- jakie obrazy mają zostać zbudowane;
- jakie zmienne środowiskowe otrzymują usługi;
- jak usługi się ze sobą komunikują;
- jakie wolumeny są używane;
- jakie healthchecki obowiązują.

---

### Usługi odnajdują się po nazwach

W sieci Docker Compose usługi mogą komunikować się przez swoje nazwy.

To znaczy, że UI nie powinno zakładać, że API zawsze działa pod `localhost`.

W Compose API może być dostępne pod nazwą:

```text
api
```

a baza pod nazwą:

```text
db
```

Dzięki temu konfiguracja działa niezależnie od konkretnego komputera.

---

### Streamlit

Streamlit jest prostym interfejsem użytkownika dla waszego API.

W tym kursie UI ma przede wszystkim:

- zebrać dane w formularzu;
- wysłać request do `/predict`;
- pokazać wynik;
- pokazać prawdopodobieństwo klasy pozytywnej.

UI nie powinno zawierać modelu ML.

Nie powinno też powtarzać logiki model preprocessing.

Streamlit komunikuje się z API.

---

### PostgreSQL

W Sprincie 4 używaliście lokalnego SQLite.

W Sprincie 5 przechodzicie na PostgreSQL uruchamiany jako osobna usługa:

```text
db
```

Nie zmieniacie idei persistence.

API nadal korzysta z tego samego kontraktu repository.

Zmienia się backend bazy.

---

### Zmienne środowiskowe

Ten sam obraz kontenera powinien działać z różnymi ustawieniami.

Dlatego konfigurację przekazujemy przez env.

Przykłady:

- adres API;
- `API_KEY`;
- `DATABASE_URL`;
- hasło do PostgreSQL.

Prawdziwe wartości trafiają do lokalnego:

```text
.env
```

Do repozytorium trafia:

```text
.env.example
```

bez sekretów.

---

### Healthcheck

Healthcheck odpowiada na pytanie:

> Czy dana usługa jest już gotowa do pracy?

To szczególnie ważne w systemie z kilkoma kontenerami.

Samo uruchomienie procesu nie zawsze oznacza, że usługa jest gotowa przyjmować requesty.

Healthchecki pomagają określić stan:

- API;
- bazy;
- pozostałych usług potrzebnych do startu systemu.

---

### Wolumen

Baza danych nie powinna tracić danych przy zwykłym ponownym uruchomieniu kontenera.

Dlatego PostgreSQL korzysta z nazwanego wolumenu.

Stan bazy żyje poza samym kontenerem.

---

## Co macie zrobić

### Krok 1. Sprawdźcie Docker Compose

Każda osoba powinna mieć działające:

```bash
docker compose version
```

Jeśli komenda nie działa, rozwiążcie problem przed rozpoczęciem właściwej pracy nad Compose.

---

### Krok 2. Zbudujcie Streamlit UI

Rozwijajcie przygotowany scaffold:

```text
ui/
```

UI ma zawierać formularz zgodny z kontraktem `/predict`.

Formularz powinien zbierać cechy wymagane przez model.

Po wysłaniu danych Streamlit:

```text
formularz
→ request do API
→ odpowiedź API
→ wynik w UI
```

Pokażcie użytkownikowi co najmniej:

- etykietę predykcji;
- prawdopodobieństwo klasy pozytywnej.

---

### Krok 3. Pobierajcie adres API i token z env

Streamlit nie powinien mieć na stałe wpisanych:

- adresu API;
- `API_KEY`.

Obie wartości pobierajcie ze zmiennych środowiskowych.

Dzięki temu ten sam obraz UI może działać lokalnie i później w chmurze.

---

### Krok 4. Przygotujcie Dockerfile UI

Rozwijajcie:

```text
docker/ui.Dockerfile
```

Obraz UI powinien zawierać tylko zależności potrzebne Streamlitowi.

Nie instalujcie w nim bibliotek ML, jeśli UI ich nie potrzebuje.

Model znajduje się po stronie API.

---

### Krok 5. Przygotujcie usługę PostgreSQL

W `docker-compose.yml` dodajcie usługę:

```text
db
```

opartą na PostgreSQL.

Skonfigurujcie:

- bazę;
- użytkownika;
- hasło;
- nazwany wolumen.

Hasło nie może być wpisane bezpośrednio do `docker-compose.yml`.

Powinno pochodzić z env.

---

### Krok 6. Podłączcie API do PostgreSQL

API powinno korzystać z:

```text
DATABASE_URL
```

wskazującego bazę PostgreSQL uruchomioną przez Compose.

Nie twórzcie osobnego mechanizmu persistence tylko dla Postgresa.

Ten sam kontrakt repository ze Sprintu 4 ma działać z nowym backendem.

W obrazie API musi znajdować się sterownik PostgreSQL.

---

### Krok 7. Zbudujcie `docker-compose.yml`

Compose ma uruchamiać trzy usługi:

```text
api
ui
db
```

Po:

```bash
docker compose up --build
```

system powinien uruchomić się jako całość.

Compose powinien zawierać konfigurację potrzebną do komunikacji między usługami, ale bez
prawdziwych sekretów zapisanych bezpośrednio w pliku.

---

### Krok 8. Dodajcie healthchecki

Skonfigurujcie healthchecki potrzebne do uruchomienia systemu.

Celem jest uniknięcie sytuacji, w której np. API próbuje korzystać z bazy, zanim PostgreSQL jest
gotowy.

Healthchecki mają pomagać określić, czy system rzeczywiście działa.

---

### Krok 9. Uzupełnijcie `.env.example`

` .env.example` powinien pokazywać, jakie zmienne są potrzebne do uruchomienia systemu.

Powinny być tam nazwy wymaganych zmiennych, ale nie prawdziwe sekrety.

Lokalny `.env` może zawierać rzeczywiste wartości i **nie trafia do repozytorium**.

---

### Krok 10. Uruchomcie cały system

Na świeżym środowisku lokalnym sprawdźcie:

```bash
docker compose up --build
```

Powinny uruchomić się:

```text
api
ui
db
```

API ma działać w trybie:

```text
persistence = sql
```

z PostgreSQL.

---

### Krok 11. Uruchomcie automatyczny smoke test

Używacie tego samego skryptu smoke, który powstał w Sprincie 4.

Smoke testuje warstwę API.

Powinien sprawdzić:

1. `/healthz`;
2. tryb persistence;
3. `/predict` z poprawnym tokenem;
4. schemat odpowiedzi;
5. zapis rekordu w PostgreSQL.

W Sprincie 5 oczekiwany tryb to:

```text
sql
```

---

### Krok 12. Wykonajcie manualny UI check

Automatyczny smoke **nie testuje Streamlita**.

Dlatego UI sprawdzacie ręcznie.

Minimum:

1. Streamlit uruchamia się;
2. formularz jest widoczny;
3. można wprowadzić dane;
4. można wykonać co najmniej jedną predykcję;
5. wynik widoczny w UI jest zgodny z odpowiedzią API.

Nie używamy Selenium, Playwright ani podobnych frameworków.

---

### Krok 13. Uzupełnijcie README

Dodajcie sekcję:

```text
Docker quickstart
```

Powinna wyjaśniać co najmniej:

- jak przygotować `.env`;
- jak uruchomić system;
- gdzie otworzyć UI;
- jak zatrzymać system.

Podstawową komendą jest:

```bash
docker compose up --build
```

---

### Krok 14. Uzupełnijcie ADR-3

W Sprincie 4 powstał szkic ADR-3.

Teraz rozszerzcie go o decyzje dotyczące:

- stanu;
- persistence;
- konfiguracji;
- lokalnego systemu wielousługowego.

Nie finalizujecie jeszcze części dotyczącej wdrożenia w chmurze.

To nastąpi w Sprincie 6.

---

## Definition of Done

- Streamlit zawiera formularz zgodny z kontraktem API.
- UI pokazuje etykietę i prawdopodobieństwo klasy pozytywnej.
- Adres API jest pobierany z env.
- `API_KEY` jest pobierany z env.
- Dockerfile UI działa.
- Obraz UI nie zawiera niepotrzebnych zależności ML.
- `docker-compose.yml` uruchamia `api`, `ui` i `db`.
- `db` działa na PostgreSQL.
- PostgreSQL korzysta z nazwanego wolumenu.
- API ma sterownik PostgreSQL.
- API korzysta z PostgreSQL przez istniejącą warstwę repository.
- Hasła i tokeny nie są wpisane bezpośrednio do Compose.
- `.env.example` jest uzupełniony.
- Healthchecki są skonfigurowane.
- `docker compose up --build` uruchamia cały system.
- Automatyczny smoke przechodzi w trybie `sql`.
- Rekord predykcji jest zapisany w PostgreSQL.
- Manualny UI check został wykonany.
- README zawiera „Docker quickstart”.
- ADR-3 jest uzupełniony.
- W repozytorium nie ma sekretów.
- CI na `main` jest zielone.
- Każda osoba w zespole ma własny obszar pracy i zrobiła merytoryczne review pracy innej osoby.

---

## Jak sprawdzić, że Sprint 5 jest gotowy

Najważniejszy test zaczyna się od świeżego klonu.

Przygotujcie lokalny `.env` na podstawie:

```text
.env.example
```

Następnie uruchomcie:

```bash
docker compose up --build
```

Oczekiwany system:

```text
Streamlit
   ↓
FastAPI
   ↓
PostgreSQL
```

Potem:

1. uruchomcie automatyczny smoke test;
2. sprawdźcie, że `/healthz` raportuje `sql`;
3. wykonajcie `/predict`;
4. potwierdźcie zapis rekordu w PostgreSQL;
5. otwórzcie Streamlit;
6. wykonajcie co najmniej jedną predykcję przez UI.

Jeśli wszystko działa po jednym `docker compose up --build`, główny cel sprintu jest spełniony.

---

## Przygotowanie do Sprintu 6

Do 07.01, najlepiej jeszcze przed 23.12, wykonajcie pre-flight chmury.

### Artifact Registry

Wypchnijcie obraz API do Artifact Registry jako:

```text
linux/amd64
```

### Hello deploy

Wykonajcie prosty test wdrożenia w Cloud Run.

To nie jest jeszcze właściwy deployment projektu.

Chodzi tylko o potwierdzenie, że:

- obraz można wypchnąć;
- dane dostępowe działają;
- Cloud Run działa;
- zespół nie zacznie Sprintu 6 od rozwiązywania problemów z samym dostępem do chmury.

---

## Podział pracy w zespole

Przykładowe obszary odpowiedzialności:

- Streamlit UI;
- Dockerfile UI;
- Compose;
- PostgreSQL i persistence;
- healthchecki i konfiguracja;
- smoke test i README;
- pre-flight chmury;
- uzupełnienie ADR-3.

Nie musicie dzielić pracy dokładnie w ten sposób.

Każda osoba:

- ma co najmniej jeden własny obszar pracy;
- robi merytoryczne review przynajmniej jednego PR innej osoby.

Integrator Sprintu 5 pilnuje:

- kompletności checklisty;
- działania całego Compose;
- manualnego UI checku;
- wykonania pre-flightu chmury przed Sprintem 6.

---

## OPTIONAL

Jeśli zespół skończy zakres obowiązkowy wcześniej, może dodatkowo:

- dodać historię predykcji w UI;
- uruchamiać `docker compose config` w CI.

Elementy OPTIONAL nie są wymagane do zaliczenia Sprintu 5.

---

## Najczęstsze błędy w tym sprincie

### 1. UI próbuje korzystać z modelu bezpośrednio

Streamlit komunikuje się z API.

Model i preprocessing ML pozostają po stronie API.

---

### 2. Używanie `localhost` między kontenerami

W Docker Compose usługi komunikują się przez nazwy usług.

Nie zakładajcie, że `localhost` oznacza inny kontener.

---

### 3. Hasła wpisane do `docker-compose.yml`

Sekrety powinny pochodzić z `.env`.

Do repozytorium nie trafiają prawdziwe wartości.

---

### 4. Tworzenie nowej warstwy persistence tylko dla PostgreSQL

Zmienia się backend bazy, nie kontrakt aplikacji.

API nadal powinno korzystać z istniejącego repository.

---

### 5. Brak trwałego wolumenu dla bazy

PostgreSQL powinien korzystać z nazwanego wolumenu.

Stan bazy nie powinien zależeć od życia pojedynczego kontenera.

---

## Najważniejszy rezultat Sprintu 5

Po tym sprincie powinniście móc odpowiedzieć:

> Czy nowa osoba może sklonować repozytorium, przygotować `.env`, uruchomić
> `docker compose up --build` i otrzymać działający system z UI, API i PostgreSQL?

Jeżeli odpowiedź brzmi „tak”, lokalna wersja systemu jest gotowa do przejścia do wdrożenia
w chmurze.
