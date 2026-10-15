# Sprint 3 — Eksperymenty, wybór modelu i artefakt

**Daty:** 12.11.2026 – 26.11.2026
**Spotkania:** 12.11 (start Sprintu 3), 19.11 oraz 26.11 (zamknięcie Sprintu 3 i start Sprintu 4)
**Deadline:** stan gałęzi `main` na początku zajęć 26.11.2026

## Cel

Zespół porównuje eksperymenty, wybiera model produkcyjny i zapisuje go jako pakiet,
który można wykorzystać bez ponownego treningu.


## Co zrobicie w tym sprincie

Macie już reprodukowalny pipeline treningowy.

W tym sprincie sprawdzicie kilka wariantów modeli, porównacie ich wyniki i wybierzecie model,
który rzeczywiście ma trafić dalej do aplikacji.

Nie wybieracie modelu wyłącznie na podstawie jednej metryki.

Sprawdzicie również:

- jak szybko model wykonuje predykcję;
- ile miejsca zajmuje;
- ile pamięci potrzebuje po wczytaniu.

Wybrany model zapiszecie jako **pakiet modelu**, który będzie można pobrać i wczytać bez
ponownego uruchamiania treningu.

Na koniec sprintu model produkcyjny ma być gotowy do użycia przez API w Sprincie 4.

---

## Najważniejsza idea Sprintu 3

W Sprincie 2 pipeline odpowiadał na pytanie:

> Czy potrafimy odtworzyć trening?

W Sprincie 3 odpowiadacie na dwa kolejne pytania:

> Który model wybieramy do dalszej części systemu?

oraz:

> W jakiej postaci model opuszcza środowisko treningowe?

---

## Co nowego pojawia się w tym sprincie

### W&B

Weights & Biases służy w tym sprincie do śledzenia eksperymentów.

Każdy ważny run powinien pozwolić odpowiedzieć:

- na jakich danych pracowaliśmy;
- z jakimi parametrami;
- z jaką wersją kodu;
- jaki wynik uzyskaliśmy.

W każdym runie zapisujecie co najmniej:

- parametry;
- metryki;
- Git SHA;
- identyfikator wersji danych, np. fingerprint.

Pierwszym runem powinien być baseline z poprzedniego sprintu.

### AutoGluon

AutoGluon służy do szybkiego porównania kilku sensownych konfiguracji modeli.

Nie chodzi o uruchamianie dużego, kosztownego searchu.

Wymagany zakres to:

- baseline;
- co najmniej dwie sensowne konfiguracje AutoGluona;
- limit czasu treningu.

AutoGluon **nie musi** zostać modelem produkcyjnym.

Jeżeli inny model lepiej spełnia wymagania projektu, możecie wybrać właśnie jego.

### Model produkcyjny

Model produkcyjny to model, który wybieracie do dalszej części systemu.

W tym kursie wybór nie opiera się wyłącznie na głównej metryce.

Porównujecie również:

- czas predykcji;
- rozmiar artefaktu;
- pamięć potrzebną do wczytania modelu.

### Pakiet modelu

Pakiet modelu to katalog zawierający zapisany model oraz informacje potrzebne do jego
późniejszego użycia.

Minimum:

```text
model
metadata.json
```

`metadata.json` opisuje model i jego pochodzenie.

Powinien zawierać m.in.:

- cechy używane przez model;
- target;
- klasę pozytywną;
- najważniejsze metryki;
- Git SHA;
- fingerprint danych;
- wersje bibliotek.

Dzięki temu w Sprincie 4 API nie musi wiedzieć, jak model był trenowany.

Ma tylko wiedzieć, jak go wczytać i jakiej struktury wejścia oczekiwać.

### W&B Artifact i alias `production`

Wybrany pakiet modelu zapisujecie również jako W&B Artifact.

Artefakt wybranego modelu oznaczacie aliasem:

```text
production
```

Dzięki temu dalsza część systemu nie musi znać konkretnego numeru eksperymentu.

Wystarczy wskazać artefakt oznaczony jako `production`.

---

## Co macie zrobić

### Krok 1. Sprawdźcie pre-flight ze Sprintu 2

Każda osoba powinna mieć działające:

- W&B;
- AutoGluon.

Sprawdźcie:

```bash
python scripts/check_env.py --autogluon
```

Jeżeli środowisko nie jest jeszcze przygotowane:

```bash
python -m pip install -r requirements/preflight-s3.txt -c constraints.txt
```

W&B powinno być skonfigurowane dla projektu zespołu.

---

### Krok 2. Zalogujcie baseline do W&B

Pierwszym runem w W&B powinien być baseline znany z poprzednich sprintów.

Run powinien zawierać:

- parametry;
- metryki;
- Git SHA;
- fingerprint danych.

Nie zmieniajcie baseline'u tylko po to, żeby dopasować go do W&B.

Celem jest zapisanie punktu odniesienia do późniejszych eksperymentów.

---

### Krok 3. Dodajcie eksperymenty AutoGluona do pipeline'u

AutoGluon ma być uruchamiany jako element pipeline'u, a nie tylko z osobnego notebooka.

Przygotujcie co najmniej dwie sensowne konfiguracje AutoGluona.

Każdy eksperyment powinien mieć:

- jawne parametry;
- limit czasu;
- zapis metryk;
- run w W&B.

Nie uruchamiajcie nieograniczonego searchu.

Celem jest porównanie kilku rozsądnych wariantów, a nie maksymalizacja wyniku za wszelką cenę.

---

### Krok 4. Porównajcie modele

Przygotujcie tabelę porównawczą obejmującą co najmniej:

- główną metrykę projektu;
- czas predykcji;
- rozmiar artefaktu;
- pamięć potrzebną po wczytaniu modelu.

Porównanie powinno obejmować:

- baseline;
- co najmniej dwie konfiguracje AutoGluona.

Jeżeli analizujecie dodatkowe modele, możecie dodać je do tej samej tabeli.

---

### Krok 5. Wybierzcie model produkcyjny

Na podstawie tabeli zdecydujcie, który model trafia dalej.

Model produkcyjny **nie musi być modelem z najwyższą wartością głównej metryki**, jeżeli
pozostałe właściwości przemawiają za innym wyborem.

Przykład:

model z minimalnie niższym F1 może być lepszym wyborem, jeśli:

- działa znacznie szybciej;
- zajmuje mniej miejsca;
- zużywa mniej pamięci.

Decyzja musi być oparta na wynikach waszych eksperymentów.

---

### Krok 6. Zbudujcie pakiet modelu

Zapiszcie model w postaci, którą można później wczytać bez uruchamiania treningu.

Pakiet powinien zawierać co najmniej:

```text
model
metadata.json
```

`metadata.json` powinien zawierać informacje wymagane przez kontrakt pakietu opisany w:

```text
src/asi_project/README.md
```

Nie twórzcie własnego, równoległego formatu, jeśli scaffold już określa strukturę.

---

### Krok 7. Dodajcie wspólne funkcje zapisu i odczytu

Model powinien być zapisywany i wczytywany przez wspólne funkcje projektu.

Celem jest uniknięcie sytuacji, w której:

- trening zapisuje model w jeden sposób;
- test ładuje go inaczej;
- API w Sprincie 4 będzie wymagało trzeciej implementacji.

Jedna ścieżka zapisu i odczytu ma być używana wszędzie.

---

### Krok 8. Zapiszcie model jako W&B Artifact

Wybrany pakiet modelu zapiszcie w W&B jako Artifact.

Artefakt produkcyjny oznaczcie aliasem:

```text
production
```

To właśnie ten alias będzie wskazywał model przeznaczony do dalszego użycia.

---

### Krok 9. Zróbcie smoke test modelu

Smoke test ma odpowiedzieć na proste pytanie:

> Czy da się pobrać wybrany model, wczytać go bez uruchamiania treningu i wykonać predykcję?

Test powinien wykonać:

```text
pobranie artefaktu production
→ wczytanie modelu
→ predykcja dla 5 wierszy
→ sprawdzenie schematu odpowiedzi
```

Smoke test uruchamiamy w czystym procesie, niezależnie od procesu treningowego.

To przygotowuje model do użycia przez API w Sprincie 4.

---

### Krok 10. Uzupełnijcie Model Card

Uzupełnijcie:

```text
docs/model_card.md
```

Model Card ma być krótka i praktyczna.

Powinna opisywać co najmniej:

- do czego służy model;
- na jakich danych był trenowany;
- jaki target przewiduje;
- która klasa jest pozytywna;
- jakie metryki osiąga;
- jakie ma najważniejsze ograniczenia;
- jaki model został wybrany jako `production`.

Nie przepisujcie całej historii projektu.

Model Card ma opisywać model, który rzeczywiście trafia dalej.

---

### Krok 11. Napiszcie ADR-2

ADR-2 dokumentuje decyzję:

> Dlaczego wybraliśmy właśnie ten model produkcyjny i w jakiej postaci przekazujemy go dalej?

W ADR-2 wykorzystajcie liczby z własnych eksperymentów W&B.

Powinny znaleźć się tam:

- rozważane warianty;
- kryteria wyboru;
- najważniejsze wyniki;
- ostateczna decyzja;
- krótkie uzasadnienie.

Plik trafia do:

```text
docs/adr/
```

---

## Definition of Done

- Baseline jest zapisany jako run W&B.
- Runy W&B zawierają parametry, metryki, Git SHA i identyfikator wersji danych.
- AutoGluon działa jako część pipeline'u.
- Wykonano co najmniej dwie sensowne konfiguracje AutoGluona z limitem czasu.
- Przygotowano tabelę porównującą modele.
- Porównanie obejmuje główną metrykę, czas predykcji, rozmiar artefaktu i pamięć przy ładowaniu.
- Zespół wybrał model produkcyjny.
- Pakiet modelu zawiera model i `metadata.json`.
- Model jest zapisywany i wczytywany wspólnymi funkcjami.
- Pakiet modelu jest zapisany w W&B jako Artifact.
- Artefakt produkcyjny ma alias `production`.
- Smoke test pobiera `production`, wczytuje model i wykonuje predykcję.
- `docs/model_card.md` jest uzupełniony.
- ADR-2 jest napisany i zmergowany.
- CI na `main` jest zielone.
- Każda osoba w zespole ma własny obszar pracy i zrobiła merytoryczne review pracy innej osoby.

---

## Jak sprawdzić, że Sprint 3 jest gotowy

Najważniejszy test nie polega na ponownym treningu modelu.

Sprawdźcie ścieżkę:

```text
W&B Artifact: production
→ pobranie
→ wczytanie modelu
→ predykcja 5 wierszy
→ sprawdzenie schematu wyniku
```

Ten proces ma działać niezależnie od pipeline'u treningowego.

Uruchomcie również:

```bash
pytest
pre-commit run --all-files
```

CI powinno działać bez wykonywania pełnych eksperymentów online.

W CI:

- W&B działa w trybie `WANDB_MODE=disabled`;
- AutoGluon jest wyłączony parametrem albo uruchamiany z bardzo krótkim limitem;
- testowana jest możliwość zapisu i ponownego wczytania pakietu modelu.

---

## Co trafia do Sprintu 4

Sprint 4 zacznie się od modelu, który już:

- został wybrany;
- ma opisane metadane;
- ma alias `production`;
- daje się pobrać;
- daje się wczytać poza procesem treningowym;
- zwraca predykcje.

Dzięki temu w Sprincie 4 nie wracacie do eksperymentów.

Budujecie usługę API wokół gotowego modelu.

Jeżeli prowadząca przekaże dane dostępowe do GCP po swoim pre-flighcie, powinny być już dostępne
przed rozpoczęciem Sprintu 4.

---

## Podział pracy w zespole

Przykładowe obszary odpowiedzialności:

- eksperymenty AutoGluona;
- tracking W&B;
- tabela porównawcza i pomiary;
- pakiet modelu i `metadata.json`;
- smoke test;
- Model Card;
- ADR-2.

Nie musicie dzielić pracy dokładnie w ten sposób.

Każda osoba:

- ma co najmniej jeden własny obszar pracy;
- robi merytoryczne review przynajmniej jednego PR innej osoby.

Integrator Sprintu 3 pilnuje:

- kompletności eksperymentów;
- wyboru modelu;
- gotowości artefaktu `production`;
- smoke testu przed zamknięciem sprintu.

---

## OPTIONAL

Jeśli zespół skończy zakres obowiązkowy wcześniej, może dodatkowo:

- użyć W&B Sweeps;
- przygotować feature importance;
- przetestować preset `optimize_for_deployment`;
- wersjonować dataset przez W&B Data Artifacts;
- wybrać AutoGluon jako model produkcyjny.

Elementy OPTIONAL nie są wymagane do zaliczenia Sprintu 3.

---

## Najczęstsze błędy w tym sprincie

### 1. Wybór modelu tylko na podstawie F1

Model produkcyjny ma działać jako część systemu.

Dlatego patrzycie również na:

- czas predykcji;
- rozmiar artefaktu;
- zużycie pamięci.

### 2. Brak informacji o pochodzeniu modelu

Sam plik modelu nie wystarcza.

Bez informacji o:

- danych;
- wersji kodu;
- metrykach;
- wersjach bibliotek

trudno później ustalić, co właściwie zostało wdrożone.

Dlatego wymagany jest `metadata.json`.

### 3. Model działa tylko w procesie treningowym

Jeżeli model można wykorzystać wyłącznie bezpośrednio po `fit()`, nie jest jeszcze gotowym
artefaktem.

Musi dać się zapisać, zamknąć proces, ponownie wczytać i wykorzystać do predykcji.

### 4. AutoGluon staje się celem samym w sobie

AutoGluon jest narzędziem do eksperymentów.

Nie musicie wybierać go jako modelu produkcyjnego.

---

## Najważniejszy rezultat Sprintu 3

Po tym sprincie powinniście móc odpowiedzieć:

> Który model wdrażamy, dlaczego właśnie ten i czy inna część systemu może go pobrać oraz
> użyć bez ponownego treningu?

Jeżeli odpowiedź brzmi „tak”, model jest gotowy do wykorzystania w API w Sprincie 4.
