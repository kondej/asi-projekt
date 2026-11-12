# ADR-1: Lokalizacja przetwarzania danych

- **Status:** przyjęty
- **Sprint:** S2
- **Autor:** @kondej
- **Recenzent:** @l33ft

## Kontekst

W Sprincie 1 przygotowaliśmy dane i wytrenowaliśmy model bazowy dla zbioru `online_shoppers` w notebooku `02_baseline.ipynb`. W Sprincie 2 przenosimy ten proces do pipeline'u Kedro uruchamianego komendą `kedro run` na pełnym zbiorze oraz `kedro run --env ci` na próbce `sample.csv`. W późniejszych sprintach model zostanie wystawiony w API przyjmującym pojedyncze rekordy bez kolumny `Revenue`. Musimy rozdzielić przetwarzanie danych tak, aby czyszczenie wejścia było wspólne dla treningu i predykcji, a operacje uczone na zbiorze treningowym nie korzystały z danych testowych.

## Rozważone opcje

1. Opcja A — podział na trzy części: `input normalization` w `data.py`, `training-only filtering` jako osobny node Kedro przed podziałem zbioru oraz `model preprocessing` wewnątrz `sklearn Pipeline` w `model.py`.
2. Opcja B — przeniesienie uzupełniania braków, skalowania oraz kodowania zmiennych kategorycznych do osobnych nodów Kedro przed treningiem modelu.
3. Opcja C — połączenie `input normalization` oraz `training-only filtering` w jedną funkcję uruchamianą dla każdego zbioru wejściowego.

## Decyzja

Wybieramy Opcję A. Za `input normalization` odpowiada funkcja `normalize_input` w `data.py`, która czyści tekst i zamienia nazwę miesiąca `June` na `Jun`. Wywołujemy ją w nodzie `normalize_input_data` w pipeline `data_processing`, a w późniejszych sprintach użyjemy jej w API przed predykcją. Za `training-only filtering` odpowiada funkcja w nodzie `filter_training_data`. Działa ona wyłącznie przy przygotowaniu zbioru treningowego i usuwa wiersze bez wartości `Revenue` oraz duplikaty. `Model preprocessing` oraz `OneHotEncoder`, zostaje wewnątrz `sklearn Pipeline` w `model.py` i zapisuje się razem z modelem w `06_models/`.

| Wielkość | Wartość | Skąd pochodzi |
|---|---|---|
| Liczba usuniętych duplikatów | `125` | `filter_training_rows` na zbiorze `12330` wierszy |
| Rozmiar zbioru treningowego `n_train` | `9764` | `metrics.json` |
| Rozmiar zbioru testowego `n_test` | `2441` | `metrics.json` przy `test_size = 0.2` |
| Liczba cech wejściowych | `16` | `project.yaml` |

## Odrzucone alternatywy

Opcję B odrzuciliśmy, bo wyliczenie średnich, median i kategorii w nodzie Kedro przed podziałem na `train` i `test` spowodowałoby wyciek danych testowych i zawyżyłoby metryki. Z kolei dopasowywanie tych kroków w osobnych nodach po splicie wymagałoby zapisywania i wczytywania kilku plików zamiast jednego gotowego modelu.

Opcję C odrzuciliśmy, bo dane przesyłane do predykcji w przyszłym API nie mają kolumny `Revenue`. Funkcja sprawdzająca braki w kolumnie docelowej i usuwająca duplikaty kończyłaby się błędem na pojedynczym rekordzie wejściowym.

## Konsekwencje

Nody w Kedro wywołują gotowe funkcje z `data.py` i `model.py`. W późniejszych sprintach API wczyta model z `06_models/` i przed predykcją przepuści dane wejściowe przez `normalize_input`. Nowe operacje bezstanowe dopisujemy do `normalize_input`, a wszystkie przekształcenia wymagające `.fit()` dodajemy wyłącznie do `sklearn Pipeline` w `model.py`.

## Historia

| Data | Zmiana |
|---|---|
| 2026-11-07 | utworzenie |
