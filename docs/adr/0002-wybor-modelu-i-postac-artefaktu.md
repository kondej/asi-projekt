# ADR-2: Wybór modelu produkcyjnego i postać artefaktu

- **Status:** przyjęty
- **Sprint:** S3
- **Autor:** @<autor>
- **Recenzent:** @<recenzent>

## Kontekst

Po Sprincie 2 mamy w Kedro pipeline `LogisticRegression` dla zbioru `online_shoppers`. W Sprincie 4 model trafi do API w kontenerze, które musi robić predykcje bez uruchamiania treningu i Kedro. Musimy wybrać docelowy model spośród baseline'u oraz konfiguracji AutoGluona i ustalić, w jakiej postaci przekazujemy go dalej.

## Rozważone opcje

1. Opcja A — model AutoGluona `ag_fast` (`medium_quality`, `GBM` i `CAT`, limit 30 s) zapisany jako katalog pakietu z `metadata.json` i opublikowany w W&B pod aliasem `production`.
2. Opcja B — rozbudowany preset AutoGluona `ag_good` (`good_quality`, limit 60 s) w tym samym formacie pakietu.
3. Opcja C — pozostawienie bazowego `LogisticRegression` albo przekazywanie samego pliku modelu z Kedro bez metadanych i W&B.

## Decyzja

Wybieramy Opcję A, czyli model `ag_fast` przekazywany jako pakiet z metadanymi. Poprawia on F1 z `0.0728` do `0.4150` i wykrywa 64% sesji zakupowych przy rozmiarze ok. 3.5 MB. Pakiet budujemy przez `model_package.py` (zapisany model + `metadata.json`) i wysyłamy do W&B pod aliasem `production`. Ten sam moduł obsługuje AutoGluona i `scikit-learn`, więc ewentualna podmiana modelu w W&B nie wymaga zmian w API.

| Wielkość | Wartość | Skąd pochodzi |
|---|---|---|
| F1 na zbiorze testowym (`n_test = 2441`) | `ag_fast`: `0.4150`, `ag_good`: `0.4134`, `LogisticRegression`: `0.0728` | W&B i `experiment_comparison.csv` |
| Recall klasy pozytywnej | `ag_fast`: `0.6387`, `ag_good`: `0.5812`, `LogisticRegression`: `0.0393` | W&B i `experiment_comparison.csv` |
| Czas predykcji (`2441` wierszy) | `LogisticRegression`: `14.5 ms`, `ag_fast`: `67.8 ms`, `ag_good`: `85.9 ms` | pomiar lokalny na pakiecie |
| Rozmiar pakietu i pamięć przy ładowaniu | `LogisticRegression`: `8.3 KB` / `0.06 MB`, `ag_fast`: `3.5 MB` / `1.5 MB`, `ag_good`: `82.6 MB` / `1.5 MB` | katalog pakietu, pomiar przy odczycie |

## Odrzucone alternatywy

Opcję B odrzuciliśmy, bo `ag_good` uzyskał niższe F1 (`0.4134`) i słabszy recall niż `ag_fast`, a jego pakiet waży aż 82.6 MB zamiast 3.5 MB.

Opcję C odrzuciliśmy, bo `LogisticRegression` wykrywa niespełna 4% zakupów (`F1 = 0.0728`) i słabo nadaje się do decyzji o wyświetleniu rabatu. Z kolei przekazywanie surowego pliku modelu bez `metadata.json` wymuszałoby ręczne pilnowanie cech i klasy pozytywnej w API.

## Konsekwencje

Trening, smoke test oraz przyszłe API korzystają z tych samych funkcji zapisu, odczytu i predykcji w `model_package.py`. W Sprincie 4 usługa pobierze gotowy artefakt `production` z W&B bez zależności od Kedro, ale obraz Docker dla API będzie musiał zawierać AutoGluona z `LightGBM` i `CatBoost`.

## Historia

| Data | Zmiana |
|---|---|
| 2026-11-26 | utworzenie |
