# Porównanie modeli — Sprint 3

Porównanie na zbiorze testowym `online_shoppers` (`n_test = 2441`, `data_mode = full`, `git_sha = 0b4d34c`).
Źródło pomiarów: `data/08_reporting/experiment_comparison.csv` oraz runy w W&B.

| Model | Format | F1 (główna) | Precision | Recall | Accuracy | Czas predykcji (2441 wierszy) | Czas ładowania | Rozmiar pakietu | Narzut RAM przy ładowaniu |
|---|---|---|---|---|---|---|---|---|---|
| `logistic_regression` | `sklearn-joblib` | `0.0728` | `0.5000` | `0.0393` | `0.8435` | `14.49 ms` | `3.39 ms` | `8.30 KB` | `0.059 MB` |
| `ag_fast` | `autogluon` | `0.4150` | `0.3073` | `0.6387` | `0.7181` | `67.78 ms` | `376.32 ms` | `3.49 MB` | `1.534 MB` |
| `ag_good` | `autogluon` | `0.4134` | `0.3208` | `0.5812` | `0.7419` | `85.87 ms` | `374.19 ms` | `82.60 MB` | `1.536 MB` |

## Wybór modelu produkcyjnego

Wybrany wariant: `ag_fast` (`autogluon`, `presets=medium_quality`, `GBM` i `CAT`, `time_limit=30s`).

Względem `logistic_regression` podnosi F1 z `0.0728` do `0.4150` i recall z `3.93%` do `63.87%` przy rozmiarze pakietu `3.49 MB`. Względem `ag_good` daje wyższe F1 i recall, zajmując ponad dwadzieścia razy mniej miejsca na dysku (`3.49 MB` vs `82.60 MB`).
