# Sprint 6 — Wdrożenie do Cloud Run, obserwowalność i release

**Daty:** 07.01.2027 – 21.01.2027
**Spotkania:** 07.01 (start Sprintu 6), 14.01 (release candidate) oraz 21.01 (finał)
**Release candidate:** 14.01.2027
**Finał i release v1.0:** 21.01.2027

## Cel

Zespół wdraża API i UI do Cloud Run, konfiguruje sekrety i logi oraz przygotowuje
finalny release `v1.0`.


## Co zrobicie w tym sprincie

Macie już lokalny system z:

```text
Streamlit UI
    ↓
FastAPI
    ↓
PostgreSQL
```

W ostatnim sprincie wdrożycie API i UI do **Google Cloud Run**.

Na koniec kursu:

- API działa pod publicznym adresem;
- UI działa pod publicznym adresem;
- `API_KEY` jest pobierany z Secret Managera;
- aplikacja działa z jawnym trybem persistence;
- logi są widoczne w Cloud Logging;
- smoke test przechodzi na wdrożonych usługach;
- dokumentacja jest aktualna;
- projekt ma release `v1.0`;
- zespół potrafi zademonstrować cały system.

---

## Najważniejsza idea Sprintu 6

Do tej pory system działał lokalnie.

Teraz odpowiadacie na pytanie:

> Co zmienia się, gdy aplikacja działa na platformie chmurowej, może się skalować do zera i nie
> ma trwałego lokalnego dysku?

W tym sprincie nie przebudowujecie modelu ani całej aplikacji.

Wdrażacie system, który już działa lokalnie, i dostosowujecie go do ograniczeń Cloud Run.

---

## Co nowego pojawia się w tym sprincie

### Cloud Run

Cloud Run uruchamia kontenery jako usługi dostępne przez HTTP.

W tym projekcie wdrażacie osobno:

```text
API
UI
```

Każda usługa ma własny adres URL.

---

### Statelessness

Instancja Cloud Run nie powinna być traktowana jak trwały serwer z lokalnym dyskiem.

Pliki zapisane lokalnie w kontenerze nie są bezpiecznym miejscem do trwałego przechowywania
stanu.

Dlatego w obowiązkowym zakresie Sprintu 6:

```text
persistence = disabled
```

jest poprawnym i domyślnym trybem działania w chmurze, jeśli nie korzystacie z zewnętrznej bazy.

SQLite w Cloud Run ma być blokowany przy starcie usługi.

Trwała baza w chmurze jest elementem OPTIONAL.

---

### Skalowanie do zera i cold start

Cloud Run może zatrzymać wszystkie instancje usługi, kiedy nie ma ruchu.

Pierwszy request po przerwie może wtedy uruchomić nową instancję.

To jest **cold start**.

Dlatego musicie zwrócić uwagę na:

- czas startu kontenera;
- czas wczytania modelu;
- pamięć;
- minimalną liczbę instancji, jeśli ją ustawicie.

---

### `$PORT`

Cloud Run przekazuje aplikacji port przez zmienną środowiskową:

```text
PORT
```

Kontener nie powinien zakładać na stałe konkretnego portu.

Dockerfile i sposób uruchamiania usługi muszą korzystać z `$PORT`.

---

### `linux/amd64`

Obrazy wysyłane do wdrożenia mają być zgodne z architekturą używaną przez środowisko docelowe.

W tym kursie obrazy wdrażane do Cloud Run budujecie jako:

```text
linux/amd64
```

To jest szczególnie ważne, jeśli lokalnie pracujecie na komputerze z Apple Silicon.

---

### Secret Manager

Prawdziwy `API_KEY` nie powinien być wpisany:

- do kodu;
- do repozytorium;
- do Dockerfile;
- jako jawna wartość w konfiguracji deploymentu.

W Sprincie 6 przechowujecie go w:

```text
Google Secret Manager
```

i podłączacie do usług Cloud Run.

---

### Konfiguracja a sekret

Nie każda zmienna środowiskowa jest sekretem.

Przykłady zwykłej konfiguracji:

- tryb persistence;
- adres API;
- wersja modelu;
- ustawienia pamięci.

Przykład sekretu:

- `API_KEY`.

Sekrety przechowujecie w Secret Managerze.

Pozostała konfiguracja może być przekazywana zwykłymi zmiennymi środowiskowymi.

---

### Cloud Logging

Logi aplikacji uruchomionej w Cloud Run trafiają do Cloud Logging.

W Sprincie 4 przygotowaliście logi predykcji w formacie JSON.

Teraz sprawdzacie, czy można je znaleźć po wdrożeniu.

---

### Release candidate

14.01 system ma już działać w chmurze.

To jest **release candidate**.

Nie czekacie z pierwszym działającym deploymentem do finału 21.01.

Tydzień między 14.01 a 21.01 służy na:

- naprawienie problemów;
- dopracowanie dokumentacji;
- finalny smoke test;
- przygotowanie demo;
- release `v1.0`.

---

## Co macie zrobić

### Krok 1. Sprawdźcie pre-flight ze Sprintu 5

Przed właściwym deploymentem powinny już działać:

- student credentials;
- projekt GCP;
- Artifact Registry;
- push obrazu;
- prosty hello deploy do Cloud Run.

Jeżeli któryś z tych elementów nadal nie działa, rozwiążcie problem na początku sprintu.

Sprawdźcie również:

```text
docs/GCP_CREDENTIALS_PREFLIGHT.md
```

---

### Krok 2. Przygotujcie obrazy do wdrożenia

Wdrażacie:

```text
API
UI
```

jako osobne obrazy.

Sprawdźcie:

- czy obrazy budują się poprawnie;
- czy są zgodne z `linux/amd64`;
- czy API korzysta z `$PORT`;
- czy UI korzysta z właściwego portu i ustawień Streamlita;
- czy obrazy nie zawierają sekretów.

---

### Krok 3. Wypchnijcie obrazy do Artifact Registry

Zbudujcie i wypchnijcie wersje obrazów przeznaczone do deploymentu.

Używajcie nazw i tagów pozwalających rozpoznać wersję.

Nie nadpisujcie wszystkiego bez kontroli jednym nieopisanym `latest`.

Szczegóły techniczne wykonujcie zgodnie z przygotowanym scaffoldem:

```text
deploy/
```

---

### Krok 4. Wdróżcie API do Cloud Run

Wdróżcie API jako usługę Cloud Run.

Skonfigurujcie co najmniej:

- obraz;
- pamięć;
- timeout;
- port przez `$PORT`;
- potrzebne zmienne środowiskowe;
- tryb persistence;
- dostęp do `API_KEY` z Secret Managera.

API powinno uruchamiać się z:

```text
persistence = disabled
```

jeśli nie korzystacie z OPTIONAL zewnętrznej bazy.

---

### Krok 5. Zablokujcie SQLite w Cloud Run

W Cloud Run nie używamy lokalnego SQLite jako trwałej bazy.

Jeżeli konfiguracja chmurowa próbuje uruchomić:

```text
SQLite + Cloud Run
```

aplikacja powinna przerwać start albo zgłosić jednoznaczny błąd konfiguracji.

Celem jest uniknięcie pozornie działającego systemu, który zapisuje dane w nietrwałym systemie
plików kontenera.

---

### Krok 6. Dodajcie `API_KEY` do Secret Managera

Utwórzcie sekret dla:

```text
API_KEY
```

Następnie podłączcie go do usługi API przez integrację Cloud Run z Secret Managerem.

`API_KEY` nie może być wpisany ręcznie jako jawna wartość w konfiguracji deploymentu.

---

### Krok 7. Wdróżcie Streamlit UI

Wdróżcie UI jako osobną usługę Cloud Run.

UI musi znać:

- adres wdrożonego API;
- `API_KEY`.

`API_KEY` również w tej usłudze ma pochodzić z Secret Managera.

Adres API może być zwykłą zmienną środowiskową.

---

### Krok 8. Sprawdźcie ustawienia Streamlita

Po wdrożeniu sprawdźcie, czy Streamlit działa poprawnie w Cloud Run.

Zwróćcie uwagę na:

- WebSocket;
- request timeout rzędu minut;
- session affinity, jeśli okaże się potrzebna;
- poprawne działanie UI po odświeżeniu strony.

Nie włączajcie dodatkowych ustawień bez potrzeby.

Użyjcie ich wtedy, gdy są wymagane przez działanie waszej aplikacji.

---

### Krok 9. Dobierzcie zasoby usług

Wykorzystajcie wyniki testów pamięci z wcześniejszych sprintów.

Ustalcie dla API i UI:

- pamięć;
- timeout;
- minimalną liczbę instancji, jeśli jest potrzebna.

Nie ustawiajcie zasobów przypadkowo.

Sprawdźcie, czy model mieści się w przydzielonej pamięci i czy cold start jest akceptowalny.

---

### Krok 10. Sprawdźcie `/healthz`

Po wdrożeniu API:

```text
GET /healthz
```

powinno potwierdzić co najmniej:

- że usługa działa;
- wersję modelu;
- aktualny tryb persistence.

W obowiązkowym wariancie chmurowym oczekujecie:

```text
persistence = disabled
```

chyba że zespół realizuje OPTIONAL z zewnętrzną bazą.

---

### Krok 11. Uruchomcie smoke test na adresie Cloud Run

Użyjcie tego samego skryptu smoke, który rozwijacie od Sprintu 4.

Nie twórzcie osobnego testu tylko dla chmury.

Smoke powinien sprawdzić:

1. `/healthz`;
2. raportowany tryb persistence;
3. `/predict` z poprawnym tokenem;
4. etykietę;
5. prawdopodobieństwo klasy pozytywnej;
6. wersję modelu.

Jeśli:

```text
persistence = disabled
```

brak zapisu do bazy jest poprawnym zachowaniem.

Jeśli zespół realizuje OPTIONAL z bazą chmurową i działa:

```text
persistence = sql
```

smoke powinien potwierdzić zapis rekordu.

---

### Krok 12. Sprawdźcie Cloud Logging

Wykonajcie kilka predykcji.

Następnie sprawdźcie, czy logi predykcji są widoczne w Cloud Logging.

Powinniście umieć znaleźć log po wykonaniu requestu.

Nie logujcie:

- `API_KEY`;
- haseł;
- innych sekretów.

---

### Krok 13. Wykonajcie manualny UI check

Tak jak w Sprincie 5:

1. otwórzcie wdrożony Streamlit;
2. sprawdźcie formularz;
3. wykonajcie co najmniej jedną predykcję;
4. sprawdźcie wynik;
5. potwierdźcie, że UI komunikuje się z wdrożonym API.

Manualny UI check wykonujecie:

- przy release candidate 14.01;
- ponownie przy finale 21.01.

---

### Krok 14. Uzupełnijcie `deploy.sh`

Rozwijajcie przygotowany scaffold:

```text
deploy/deploy.sh
```

Skrypt ma odtwarzać deployment w sposób zgodny z ustalonymi parametrami projektu.

Nie zapisujcie w nim prawdziwych sekretów.

---

### Krok 15. Zaktualizujcie dokumentację

Przed release zaktualizujcie:

- `README.md`;
- `docs/model_card.md`;
- ADR-3.

README powinno jasno mówić:

- jak uruchomić projekt lokalnie;
- jak wygląda architektura;
- jakie są adresy wdrożonych usług lub gdzie je znaleźć;
- jaki jest tryb persistence w chmurze;
- jak wykonać smoke test.

Model Card ma odpowiadać modelowi, który rzeczywiście jest wdrożony.

---

### Krok 16. Sfinalizujcie ADR-3

ADR-3 był rozwijany od Sprintu 4.

W Sprintach 4 i 5 opisaliście m.in.:

- sposób przekazania modelu do usługi;
- persistence;
- konfigurację systemu lokalnego.

Teraz dodajcie decyzje dotyczące:

- Secret Managera;
- konfiguracji Cloud Run;
- persistence w chmurze;
- deploymentu API i UI.

Po Sprincie 6 ADR-3 jest finalny.

---

### Krok 17. Przygotujcie release candidate — 14.01

Do 14.01 muszą działać:

- API w Cloud Run;
- UI w Cloud Run;
- Secret Manager;
- smoke test;
- manualny UI check.

To nie jest próbny termin.

14.01 system ma być już działającym kandydatem do wydania.

---

### Krok 18. Przygotujcie release `v1.0` — 21.01

Na finał:

- wykonajcie finalny smoke test;
- wykonajcie finalny UI check;
- poprawcie dokumentację;
- upewnijcie się, że ADR-3 jest finalny;
- przygotujcie release notes;
- utwórzcie release `v1.0`;
- przygotujcie demo.

---

## Definition of Done

### Release candidate — 14.01

- API jest wdrożone do Cloud Run.
- UI jest wdrożone do Cloud Run.
- Obrazy są zgodne z `linux/amd64`.
- API korzysta z `$PORT`.
- `API_KEY` znajduje się w Secret Managerze.
- API otrzymuje `API_KEY` przez integrację z Secret Managerem.
- UI otrzymuje `API_KEY` przez integrację z Secret Managerem.
- Persistence w chmurze jest ustawione jawnie.
- Przy braku zewnętrznej bazy działa `persistence = disabled`.
- SQLite w Cloud Run jest zablokowany.
- `/healthz` działa.
- Smoke test na publicznym URL API przechodzi.
- Manualny UI check przechodzi.
- Logi predykcji są widoczne w Cloud Logging.

---

### Finał — 21.01

- Finalny smoke test przechodzi.
- Finalny manualny UI check przechodzi.
- README jest aktualne.
- Model Card jest aktualna.
- ADR-3 jest finalny.
- `deploy.sh` odpowiada rzeczywistemu deploymentowi.
- W repozytorium nie ma sekretów.
- Release notes są przygotowane.
- Release `v1.0` jest utworzony.
- Zespół jest gotowy do demo.

---

## Jak sprawdzić, że Sprint 6 jest gotowy

### API

Uruchomcie smoke test na publicznym adresie Cloud Run.

Oczekiwany wariant obowiązkowy:

```text
/healthz
→ persistence = disabled
→ /predict z API_KEY
→ poprawna odpowiedź
→ brak wymagania zapisu stanu
```

Jeżeli korzystacie z OPTIONAL zewnętrznej bazy:

```text
/healthz
→ persistence = sql
→ /predict
→ rekord zapisany w bazie
```

### UI

Otwórzcie publiczny adres Streamlita i wykonajcie predykcję ręcznie.

### Logi

Po wykonaniu predykcji znajdźcie odpowiadający jej log w Cloud Logging.

### Sekret

Sprawdźcie, że `API_KEY`:

- nie jest w repozytorium;
- nie jest hardcodowany;
- nie jest wpisany jawnie do deploymentu;
- pochodzi z Secret Managera.

---

## Podział pracy w zespole

Przykładowe obszary odpowiedzialności:

- deployment API;
- deployment UI;
- Secret Manager i konfiguracja;
- smoke test i Cloud Logging;
- `deploy.sh`;
- dokumentacja;
- finalizacja ADR-3;
- release i demo.

Nie musicie dzielić pracy dokładnie w ten sposób.

Każda osoba:

- ma co najmniej jeden własny obszar pracy;
- robi merytoryczne review przynajmniej jednego PR innej osoby.

Na finalnym demo pytanie może trafić do dowolnej osoby z zespołu.

---

## OPTIONAL

Jeśli zespół skończy zakres obowiązkowy wcześniej, może dodatkowo:

- podłączyć Cloud SQL albo zewnętrzny PostgreSQL;
- ustawić `DATABASE_URL` jako sekret;
- wdrażać z CI;
- przygotować alerty i dashboard;
- pobierać model z W&B przy starcie usługi.

Elementy OPTIONAL nie są wymagane do zaliczenia Sprintu 6.

---

## Najczęstsze błędy w tym sprincie

### 1. Pierwszy działający deployment dopiero 21.01

Pierwszy działający deployment ma być gotowy na release candidate:

```text
14.01
```

21.01 jest dniem finalnego release i demo.

---

### 2. SQLite jako trwała baza w Cloud Run

Lokalny system plików kontenera nie jest trwałym storage.

W obowiązkowym wariancie chmurowym bez zewnętrznej bazy używacie:

```text
persistence = disabled
```

---

### 3. Sekret jako zwykła zmienna wpisana ręcznie

`API_KEY` ma pochodzić z Secret Managera.

Nie traktujcie sekretu tak samo jak zwykłego parametru konfiguracyjnego.

---

### 4. Inny smoke test dla każdego środowiska

Od Sprintu 4 rozwijacie jeden smoke test API.

Ten sam kontrakt powinien działać:

```text
lokalny Docker
→ Docker Compose
→ Cloud Run
```

Zmienia się adres i konfiguracja, nie sens testu.

---

### 5. Brak sprawdzenia cold startu i pamięci

Usługa może działać lokalnie, ale nie mieścić się w źle dobranych zasobach Cloud Run.

Użyjcie wyników pomiarów z wcześniejszych sprintów.

---

## Najważniejszy rezultat Sprintu 6

Po tym sprincie powinniście móc odpowiedzieć:

> Czy osoba spoza zespołu może otworzyć nasze UI, wykonać predykcję przez wdrożone API, a my
> potrafimy wskazać użyty model, konfigurację, sekret, logi i wersję release?

Jeżeli odpowiedź brzmi „tak”, macie kompletny system ML od danych do działającego deploymentu
w chmurze.
