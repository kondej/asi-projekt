# Datasety projektu zespołowego

Ten dokument opisuje datasety zatwierdzone do projektu zespołowego ASI w edycji 2026/2027.
Kontrakt w wersji dla kodu znajduje się w `src/asi_project/datasets.yaml`. Oba pliki muszą być
spójne — pilnuje tego test `tests/test_registry.py`. Zespół nie edytuje żadnego z nich.

## Zasady wyboru

- Wszystkie projekty dotyczą **binary classification**. Regresja i multiclass są poza zakresem
  tej edycji kursu.
- Wybieracie dataset wyłącznie z listy poniżej i wpisujecie jego identyfikator w `project.yaml`
  (pole `dataset`).
- Kilka zespołów może wybrać ten sam dataset. Oceniamy architekturę, reprodukowalność i decyzje
  projektowe, a nie unikalność danych. Jeżeli rozkład wyborów stanie się bardzo nierówny,
  prowadząca może poprosić część zespołów o wybór innego datasetu.
- Do X modelu mogą trafić **wyłącznie** kolumny z listy ALLOWED FEATURES. Każda inna kolumna
  (wymieniona w EXCLUDED FEATURES albo nieopisana w ogóle) jest niedozwolona. Pilnuje tego
  funkcja `make_xy` i testy w `tests/test_project.py`.
- Klasa pozytywna jest kodowana jako `1`. Metryki precision, recall i F1 liczymy dla niej.
- Wszystkie datasety są na licencji CC BY 4.0: w karcie projektu (README) podajcie źródło
  i cytowanie (DOI).

## Przegląd

| Id | Dataset | Domena | Rekordy | Target (klasa pozytywna) | Udział klasy pozytywnej | Split |
|---|---|---|---|---|---|---|
| `ai4i_2020` | AI4I 2020 Predictive Maintenance | proces przemysłowy | 10 000 | `Machine failure` (`1`) | 3,39% | `stratified_random` |
| `bank_marketing` | Bank Marketing (`bank-full`) | marketing usług | 45 211 | `y` (`yes`) | 11,7% | `time_ordered` |
| `iranian_churn` | Iranian Churn | klient / usługa | 3 150 | `Churn` (`1`) | 495 / 3150 = 15,71% | `stratified_random` |
| `online_shoppers` | Online Shoppers Purchasing Intention | e-commerce | 12 330 | `Revenue` (`true`) | 15,5% | `stratified_random` |

Dane pobiera skrypt `python scripts/download_data.py`. Zapisuje on plik do `data/01_raw/<id>/`
(poza gitem) razem z `fingerprint.json` (SHA-256 pliku) i wypisuje rozkład klas.

Strategie splitu:

- `stratified_random` — losowy podział z zachowaniem proporcji klas;
- `time_ordered` — rekordy są uporządkowane w czasie; zbiór testowy to ostatnie rekordy,
  bez tasowania.

---

## `ai4i_2020` — AI4I 2020 Predictive Maintenance

- **Problem:** czy w danym punkcie procesu produkcyjnego wystąpi awaria maszyny.
- **Źródło:** UCI Machine Learning Repository,
  https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset,
  DOI https://doi.org/10.24432/C5HS5C.
- **Licencja:** CC BY 4.0 (wymagane uznanie autorstwa).
- **Pobieranie:** archiwum
  https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip,
  plik `ai4i2020.csv` (ok. 510 KB). Alternatywnie pakiet `ucimlrepo`, id 601.
- **Target:** `Machine failure`. **Klasa pozytywna:** `1` (awaria).
- **Moment predykcji:** predykcja dla pojedynczego punktu procesu na podstawie parametrów
  zmierzonych w tym punkcie, zanim wiadomo, czy wystąpiła awaria i który tryb awarii zaszedł.
- **Udział klasy pozytywnej:** 339 awarii na 10 000 rekordów (3,39%).

ALLOWED FEATURES:

| Kolumna | Typ wejścia | Uwagi |
|---|---|---|
| `Type` | kategoryczna: `L`, `M`, `H` | wariant jakości produktu |
| `Air temperature [K]` | liczba rzeczywista, kelwiny | |
| `Process temperature [K]` | liczba rzeczywista, kelwiny | |
| `Rotational speed [rpm]` | liczba całkowita, obr./min | |
| `Torque [Nm]` | liczba rzeczywista, Nm | |
| `Tool wear [min]` | liczba całkowita, minuty | |

EXCLUDED FEATURES:

| Kolumna | Powód |
|---|---|
| `UDI` | identyfikator rekordu (nazwa kolumny w pliku CSV) |
| `UID` | identyfikator rekordu (nazwa używana w metadanych UCI) |
| `Product ID` | identyfikator produktu |
| `TWF` | flaga trybu awarii (tool wear failure) — składowa targetu, target leakage |
| `HDF` | flaga trybu awarii (heat dissipation failure) — składowa targetu, target leakage |
| `PWF` | flaga trybu awarii (power failure) — składowa targetu, target leakage |
| `OSF` | flaga trybu awarii (overstrain failure) — składowa targetu, target leakage |
| `RNF` | flaga trybu awarii (random failure) — składowa targetu, target leakage |

Pięć flag trybów awarii nie może trafić do X: `Machine failure` ma wartość `1` właśnie wtedy,
gdy zachodzi któryś z tych trybów, więc flagi zdradzają target.

**Istotne ograniczenia:**

- Dane są syntetyczne (odwzorowują typowy proces, ale nie pochodzą z prawdziwej maszyny).
- Silny imbalance: DummyClassifier osiąga ok. 96,6% accuracy, więc sama accuracy nie mówi
  nic o jakości modelu.
- Awarie wynikają z reguł progowych na kombinacjach cech (np. różnica temperatur i prędkość,
  iloczyn zużycia narzędzia i momentu). Modele liniowe radzą sobie z tym gorzej niż drzewa.
- Tryb RNF jest losowy, więc część błędów jest nieusuwalna.

**Ryzyka splitu / leakage:**

- UCI opisuje zbiór także jako szereg czasowy: temperatury powstały z procesu random walk,
  a rekordy mają kolejny numer `UDI`. Etykieta zależy jednak od parametrów bieżącego rekordu,
  dlatego kurs używa splitu `stratified_random`.
- Próbka CI musi zawierać rekordy z awarią — skrypt `make_ci_sample.py` dobiera ich
  co najmniej 30.
- W kontrakcie wykluczamy zarówno `UDI`, jak i `UID`, bo nazwa identyfikatora różni się między
  plikiem CSV a metadanymi UCI. Rzeczywiste nazwy kolumn sprawdza skrypt pobierania.

---

## `bank_marketing` — Bank Marketing (`bank-full`)

- **Problem:** czy klient założy lokatę terminową w wyniku telefonicznej kampanii marketingowej.
- **Źródło:** UCI Machine Learning Repository,
  https://archive.ics.uci.edu/dataset/222/bank+marketing, DOI https://doi.org/10.24432/C5K306.
- **Licencja:** CC BY 4.0 (wymagane uznanie autorstwa).
- **Pobieranie:** archiwum https://archive.ics.uci.edu/static/public/222/bank+marketing.zip.
  W środku są dwa archiwa; używamy pliku `bank-full.csv` z archiwum `bank.zip`
  (separator `;`). Skrypt pobierania obsługuje zagnieżdżone archiwa. Alternatywnie OpenML,
  id 1461, albo `ucimlrepo`, id 222.
- **Target:** `y`. **Klasa pozytywna:** `yes` (klient założył lokatę).
- **Moment predykcji:** predykcja wykonywana jest przed poznaniem rezultatu bieżącego kontaktu
  telefonicznego.
- **Udział klasy pozytywnej:** 5 289 na 45 211 rekordów (11,7%).

ALLOWED FEATURES:

| Kolumna | Typ wejścia | Uwagi |
|---|---|---|
| `age` | liczba całkowita | |
| `job` | kategoryczna | zawiera wartość `unknown` |
| `marital` | kategoryczna | |
| `education` | kategoryczna | zawiera wartość `unknown` |
| `default` | kategoryczna `yes`/`no` | czy klient ma zaległy kredyt |
| `balance` | liczba całkowita | średnie roczne saldo |
| `housing` | kategoryczna `yes`/`no` | kredyt mieszkaniowy |
| `loan` | kategoryczna `yes`/`no` | kredyt gotówkowy |
| `contact` | kategoryczna | zawiera wartość `unknown` |
| `day` | liczba całkowita | dzień miesiąca ostatniego kontaktu |
| `month` | kategoryczna | miesiąc ostatniego kontaktu |
| `campaign` | liczba całkowita | liczba kontaktów w tej kampanii, z bieżącym włącznie |
| `pdays` | liczba całkowita | dni od kontaktu w poprzedniej kampanii; `-1` = brak kontaktu |
| `previous` | liczba całkowita | liczba kontaktów przed tą kampanią |
| `poutcome` | kategoryczna | wynik poprzedniej kampanii; zawiera `unknown` |

EXCLUDED FEATURES:

| Kolumna | Powód |
|---|---|
| `duration` | prediction-time availability / temporal leakage: czas trwania rozmowy jest znany dopiero po jej zakończeniu, czyli po momencie predykcji |

**Istotne ograniczenia:**

- Wartości `unknown` i `pdays = -1` to umowne oznaczenia braku informacji, a nie zwykłe
  kategorie i liczby. To materiał na decyzje w input normalization (decyzja zespołu).
- Zbiór zawiera atrybuty finansowe klienta. Problem nie jest decyzją kredytową, ale w demo
  i formularzu używamy wyłącznie danych fikcyjnych.
- To największy zbiór na liście (wciąż odpowiedni dla laptopa).

**Ryzyka splitu / leakage:**

- Rekordy są uporządkowane chronologicznie (maj 2008 – listopad 2010), a moment predykcji
  dotyczy przyszłych kontaktów, dlatego kontrakt wymaga splitu `time_ordered`. Udział klasy
  pozytywnej w zbiorze testowym może różnić się od treningowego — to realny dryf, nie błąd.
- Ten sam klient mógł być kontaktowany w kilku kampaniach, a zbiór nie ma identyfikatora
  klienta (skala zjawiska: NIEZWERYFIKOWANE). Split `time_ordered` ogranicza ryzyko, że
  informacja o tym samym kliencie trafi jednocześnie do treningu i testu z przyszłości.
- Próbka CI zachowuje kolejność rekordów (`make_ci_sample.py`).

---

## `iranian_churn` — Iranian Churn

- **Problem:** czy klient operatora telekomunikacyjnego odejdzie.
- **Źródło:** UCI Machine Learning Repository,
  https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset,
  DOI https://doi.org/10.24432/C5JW3Z.
- **Licencja:** CC BY 4.0 (wymagane uznanie autorstwa).
- **Pobieranie:** archiwum https://archive.ics.uci.edu/static/public/563/iranian+churn+dataset.zip,
  plik `Customer Churn.csv`. Alternatywnie `ucimlrepo`, id 563.
- **Target:** `Churn`. **Klasa pozytywna:** `1` (klient odszedł).
- **Moment predykcji:** predykcja na koniec 9. miesiąca na podstawie agregatów z miesięcy 1–9;
  etykieta opisuje stan klienta na koniec 12. miesiąca (3 miesiące odstępu planistycznego).
- **Udział klasy pozytywnej:** ** 495 na 3 150 rekordów (15,71%). Źródło pierwotne nie podaje
  tego rozkładu; wartość została zweryfikowana po pobraniu danych przez skrypt projektu.

ALLOWED FEATURES:

| Kolumna | Typ wejścia | Uwagi |
|---|---|---|
| `Call Failure` | liczba całkowita | liczba nieudanych połączeń |
| `Complains` | binarna `0`/`1` | czy klient składał reklamację |
| `Subscription Length` | liczba całkowita | miesiące abonamentu |
| `Charge Amount` | porządkowa `0`–`9` | zakodowana liczbami |
| `Seconds of Use` | liczba całkowita | łączny czas rozmów |
| `Frequency of use` | liczba całkowita | liczba połączeń |
| `Frequency of SMS` | liczba całkowita | liczba SMS-ów |
| `Distinct Called Numbers` | liczba całkowita | liczba różnych numerów |
| `Age Group` | porządkowa `1`–`5` | zakodowana liczbami |
| `Tariff Plan` | binarna `1`/`2` | 1 = pay as you go, 2 = abonament |
| `Status` | binarna `1`/`2` | 1 = aktywny, 2 = nieaktywny (w okresie miesięcy 1–9) |
| `Age` | liczba całkowita | dubluje informację z `Age Group` |

EXCLUDED FEATURES:

| Kolumna | Powód |
|---|---|
| `Customer Value` | Excluded by course policy because availability at the intended prediction moment is ambiguous (dokumentacja opisuje ją tylko jako wyliczoną wartość klienta, bez sposobu i okresu wyliczenia) |

**Istotne ograniczenia:**

- Ten sam typ problemu (churn) co w onboardingu na innym zbiorze. Dane i kontrakt są inne,
  ale łatwo o mechaniczne powielenie decyzji z onboardingu — każdą decyzję uzasadnijcie
  dla tego zbioru.
- Część kolumn to kategorie zakodowane liczbami (`Charge Amount`, `Age Group`, `Tariff Plan`,
  `Status`). Typ cechy w `project.yaml` to decyzja zespołu.
- Mały zbiór (3 150 rekordów): metryki na zbiorze testowym mają dużą wariancję.

**Ryzyka splitu / leakage:**

- Każdy rekord to inny klient wylosowany z bazy operatora — split `stratified_random`.
- Nazwy kolumn w pliku źródłowym mogą zawierać podwójne spacje; funkcje wczytujące ujednolicają
  białe znaki w nazwach kolumn.

---

## `online_shoppers` — Online Shoppers Purchasing Intention

- **Problem:** czy sesja w sklepie internetowym zakończy się zakupem.
- **Źródło:** UCI Machine Learning Repository,
  https://archive.ics.uci.edu/dataset/468/online+shoppers+purchasing+intention+dataset,
  DOI https://doi.org/10.24432/C5F88Q.
- **Licencja:** CC BY 4.0 (wymagane uznanie autorstwa).
- **Pobieranie:** archiwum
  https://archive.ics.uci.edu/static/public/468/online+shoppers+purchasing+intention+dataset.zip,
  plik `online_shoppers_intention.csv` (ok. 1 MB). Alternatywnie `ucimlrepo`, id 468.
- **Target:** `Revenue`. **Klasa pozytywna:** `true` (sesja zakończona zakupem).
- **Moment predykcji:** predykcja dla sesji na podstawie jej zagregowanych statystyk (liczby
  i czasy stron, metryki analityczne, kontekst wizyty), zanim wiadomo, czy sesja zakończy się
  zakupem.
- **Udział klasy pozytywnej:** 1 908 na 12 330 sesji (15,5%).

ALLOWED FEATURES:

| Kolumna | Typ wejścia | Uwagi |
|---|---|---|
| `Administrative` | liczba całkowita | liczba stron administracyjnych w sesji |
| `Administrative_Duration` | liczba | czas na tych stronach |
| `Informational` | liczba całkowita | |
| `Informational_Duration` | liczba | |
| `ProductRelated` | liczba całkowita | liczba stron produktowych |
| `ProductRelated_Duration` | liczba | czas na stronach produktowych |
| `BounceRates` | liczba z zakresu 0–1 | metryka Google Analytics dla odwiedzonych stron |
| `ExitRates` | liczba z zakresu 0–1 | metryka Google Analytics dla odwiedzonych stron |
| `SpecialDay` | liczba z zakresu 0–1 | bliskość szczególnego dnia (np. walentynki) |
| `Month` | kategoryczna | skróty nazw miesięcy |
| `OperatingSystems` | kategoria zakodowana liczbą | kody bez słownika w dokumentacji |
| `Browser` | kategoria zakodowana liczbą | kody bez słownika w dokumentacji |
| `Region` | kategoria zakodowana liczbą | kody bez słownika w dokumentacji |
| `TrafficType` | kategoria zakodowana liczbą | kody bez słownika w dokumentacji |
| `VisitorType` | kategoryczna | nowy / powracający / inny |
| `Weekend` | logiczna | wizyta w weekend |

EXCLUDED FEATURES:

| Kolumna | Powód |
|---|---|
| `PageValues` | Excluded by course policy because availability at the intended prediction moment is ambiguous. |

`PageValues` nie jest potwierdzonym leakage. Dokumentacja opisuje ją jako średnią wartość stron
odwiedzonych przed transakcją, ale nie mówi, czy obejmuje transakcję z bieżącej sesji.

**Istotne ograniczenia:**

- Część cech to metryki analityczne, których użytkownik formularza nie zna. Realnym klientem
  API byłby system analityczny; formularz Streamlit pełni rolę symulatora sesji.
- Kategorie zakodowane liczbami (`OperatingSystems`, `Browser`, `Region`, `TrafficType`)
  wymagają świadomej decyzji o typie cechy.

**Ryzyka splitu / leakage:**

- Zbiór utworzono tak, by każda sesja pochodziła od innego użytkownika w okresie jednego roku,
  więc split `stratified_random` nie miesza tych samych osób między treningiem i testem.

---

## Rezerwowe (nie są na liście dla studentów)

- **In-Vehicle Coupon Recommendation** (UCI, id 603, CC BY 4.0) — powtarzane obserwacje tych
  samych respondentów bez respondent ID, przez co nie można odtworzyć group-aware splitu.
- **Hotel Booking Demand** (Data in Brief 2019, CC BY 4.0) — kilka kolumn znanych dopiero po
  zameldowaniu lub anulowaniu rezerwacji (m.in. status rezerwacji i liczba zmian) wymaga kuracji
  danych; zbiór ma ponad 119 tys. rekordów.

## Odrzucone po weryfikacji

- **Rice (Cammeo and Osmancik)** (UCI, id 545, CC BY 4.0) — 3 810 rekordów i 7 cech
  morfologicznych wyliczonych z obrazów ziaren (np. pole w pikselach). Modelowanie jest zbyt
  banalne (regresja logistyczna ok. 93% accuracy w pracy źródłowej), preprocessing ogranicza
  się do skalowania, a cech nie da się sensownie wpisać w formularz: realnym wejściem byłby
  obraz i potok przetwarzania obrazu, więc kontrakt API byłby sztuczny.
- **Electrical Grid Stability Simulated Data** (UCI, id 471) — kolumna `stab` jednoznacznie
  wyznacza target `stabf`; pozostałe cechy to abstrakcyjne parametry symulacji.
- **Occupancy Detection** (UCI, id 357) — szereg czasowy z jednego pomieszczenia; sam czujnik
  światła daje ok. 97–99% accuracy.
- **Airline Passenger Satisfaction** (Kaggle) — licencja i pochodzenie niezweryfikowane,
  pobieranie wymaga tokenu Kaggle, a oceny usług i target pochodzą z tej samej ankiety.
- **Airlines** (OpenML, id 1169) — licencja opisana tylko jako „publicly available”,
  nieudokumentowana definicja targetu i słaby sygnał.
- Odrzucone z założenia (ryzyko etyczne): Adult (dochód z cech demograficznych),
  Default of Credit Card Clients (decyzje kredytowe), zbiory Heart Disease (diagnozowanie
  chorób), Predict Students' Dropout (decyzje o studentach).
