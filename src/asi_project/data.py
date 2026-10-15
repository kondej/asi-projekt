"""Dane: wczytywanie, kontrakt danych i przygotowanie X/y.

Projekt rozróżnia trzy typy przetwarzania:

1. input normalization (``normalize_input``) — bezpieczna przy predykcji: działa na pojedynczym
   rekordzie, nie używa targetu ani statystyk zbioru. Ta sama funkcja trafi później do API.
2. training-only filtering (``filter_training_rows``) — wyłącznie przy przygotowaniu danych
   treningowych (np. rekordy bez targetu, duplikaty). Nigdy nie działa przy predykcji.
3. model preprocessing — wszystko, co wymaga ``fit`` (imputacja, skalowanie, kodowanie).
   Żyje wewnątrz sklearn Pipeline w ``asi_project.model``, a nie w tym module.
"""

import math
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from asi_project.config import DatasetContract, ProjectConfig

DATA_MODES = ("full", "sample")


class DataContractError(ValueError):
    """Dane albo deklaracje zespołu nie spełniają kontraktu datasetu."""


# --- wczytywanie -----------------------------------------------------------------------------


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Ujednolica białe znaki w nazwach kolumn (np. podwójne spacje w pliku źródłowym)."""
    renamed = {column: " ".join(str(column).split()) for column in df.columns}
    return df.rename(columns=renamed)


def raw_data_path(config: ProjectConfig, contract: DatasetContract) -> Path:
    """Ścieżka pełnych danych (poza gitem): ``data/01_raw/<dataset_id>/<plik źródłowy>``."""
    return config.root / "data" / "01_raw" / contract.dataset_id / contract.download_member


def load_dataset(
    config: ProjectConfig,
    contract: DatasetContract,
    mode: str = "full",
) -> pd.DataFrame:
    """Wczytuje pełne dane (``mode="full"``) albo próbkę CI (``mode="sample"``)."""
    if mode == "full":
        path = raw_data_path(config, contract)
        read_kwargs = contract.read_csv_kwargs
        hint = "Uruchom: python scripts/download_data.py"
    elif mode == "sample":
        path = config.ci_sample_path
        read_kwargs = {}
        hint = "Uruchom: python scripts/make_ci_sample.py"
    else:
        raise ValueError(f"Nieznany tryb danych {mode!r}; dozwolone: {DATA_MODES}.")
    if not path.is_file():
        raise FileNotFoundError(f"Brak pliku {path}. {hint}")
    return normalize_column_names(pd.read_csv(path, **read_kwargs))


# --- target ----------------------------------------------------------------------------------


def label_text(value: object) -> str | None:
    """Tekstowa postać etykiety do porównań (``True`` -> ``"true"``, ``1.0`` -> ``"1"``)."""
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    if isinstance(value, bool | np.bool_):
        return "true" if value else "false"
    if isinstance(value, int | np.integer):
        return str(int(value))
    if isinstance(value, float | np.floating) and float(value).is_integer():
        return str(int(value))
    return str(value).strip().lower()


def target_classes(target: pd.Series) -> list[str]:
    """Posortowane, unikalne klasy targetu (w postaci ``label_text``), bez braków."""
    labels = {label for label in target.map(label_text) if isinstance(label, str)}
    return sorted(labels)


def encode_target(target: pd.Series, positive_class: str) -> pd.Series:
    """Koduje binarny target: klasa pozytywna -> 1, druga klasa -> 0."""
    labels = target.map(label_text)
    if labels.isna().any():
        raise DataContractError("Target zawiera braki — usuń takie rekordy w filter_training_rows.")
    classes = sorted(set(labels))
    if len(classes) > 2:
        raise DataContractError(f"Target nie jest binarny: {classes}.")
    return (labels == label_text(positive_class)).astype(int).rename(target.name)


# --- kontrakt danych ---------------------------------------------------------------------------


def feature_list_problems(contract: DatasetContract, features: Sequence[str]) -> list[str]:
    """Problemy z listą cech modelu względem ALLOWED / EXCLUDED FEATURES (pusta lista = OK)."""
    problems: list[str] = []
    if not features:
        problems.append("Lista cech modelu jest pusta — zadeklaruj cechy w project.yaml.")
    duplicates = sorted({name for name in features if list(features).count(name) > 1})
    if duplicates:
        problems.append(f"Cechy zadeklarowane więcej niż raz: {duplicates}.")
    for name in features:
        if name == contract.target:
            problems.append(f"Target '{name}' nie może być cechą modelu.")
        elif name in contract.excluded_features:
            reason = contract.excluded_features[name]
            problems.append(f"Kolumna '{name}' jest EXCLUDED: {reason}")
        elif name not in contract.allowed_features:
            problems.append(f"Kolumna '{name}' nie jest na liście ALLOWED FEATURES.")
    return problems


def validate(
    df: pd.DataFrame,
    contract: DatasetContract,
    config: ProjectConfig | None = None,
) -> list[str]:
    """Kontrakt danych jako kod. Zwraca listę problemów (pusta lista = dane zgodne).

    Sprawdza obecność targetu i ALLOWED FEATURES, binarność targetu i obecność klasy
    pozytywnej. Jeśli podano ``config``, sprawdza też deklaracje typów cech zespołu.
    """
    problems: list[str] = []
    missing = [column for column in contract.required_columns if column not in df.columns]
    if missing:
        problems.append(f"Brak wymaganych kolumn: {missing}.")
    if contract.target in df.columns:
        classes = target_classes(df[contract.target])
        if len(classes) != 2:
            problems.append(f"Target musi mieć dokładnie 2 klasy, a ma: {classes}.")
        if label_text(contract.positive_class) not in classes:
            problems.append(f"Klasa pozytywna '{contract.positive_class}' nie występuje w danych.")
    if config is not None:
        problems.extend(feature_list_problems(contract, config.model_features))
        overlap = set(config.numeric_features) & set(config.categorical_features)
        if overlap:
            problems.append(f"Cechy jednocześnie numeryczne i kategoryczne: {sorted(overlap)}.")
        for column in config.numeric_features:
            if column in df.columns and not pd.api.types.is_numeric_dtype(df[column]):
                problems.append(f"Cecha numeryczna '{column}' ma typ {df[column].dtype}.")
    return problems


def assert_valid(
    df: pd.DataFrame,
    contract: DatasetContract,
    config: ProjectConfig | None = None,
) -> None:
    """Jak ``validate``, ale zgłasza ``DataContractError`` przy pierwszym naruszeniu kontraktu."""
    problems = validate(df, contract, config)
    if problems:
        raise DataContractError("\n".join(problems))


# --- input normalization i training-only filtering ---------------------------------------------


def is_text_column(column: pd.Series) -> bool:
    """Czy kolumna przechowuje tekst (dtype object albo string)."""
    return pd.api.types.is_object_dtype(column) or pd.api.types.is_string_dtype(column)


def _strip_text(value: object) -> object:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else np.nan
    return value


def normalize_input(df: pd.DataFrame) -> pd.DataFrame:
    """Input normalization — bezpieczne ujednolicenie wejścia (trening i później API).

    Zasady sprawdzane testami (tests/test_project.py):
    - wynik dla rekordu nie zależy od innych rekordów (działa na pojedynczym rekordzie),
    - nie używa targetu ani statystyk zbioru (żadnych median, średnich ani ``fit``),
    - jest idempotentna: ponowne wywołanie nie zmienia wyniku.

    Domyślnie przycina białe znaki w wartościach tekstowych i zamienia puste napisy na brak.

    TODO (S1): po EDA dopisz reguły dla swojego datasetu, np. oczywiste reprezentacje braków
    albo konwersję typów. Każdą regułę uzasadnij w notebooku 01.
    """
    normalized = df.copy()
    for column in normalized.columns:
        if is_text_column(normalized[column]):
            normalized[column] = normalized[column].map(_strip_text)
    return normalized


def filter_training_rows(df: pd.DataFrame, contract: DatasetContract) -> pd.DataFrame:
    """Training-only filtering — tylko przy przygotowaniu danych treningowych.

    Domyślnie usuwa rekordy bez targetu (nie da się na nich uczyć ani oceniać modelu).
    Funkcja może tylko usuwać rekordy; nie dodaje ich i nie zmienia wartości.

    TODO (S1): po EDA zdecyduj, czy potrzebne są inne reguły (np. dokładne duplikaty).
    Decyzję i jej powód zapisz w notebooku 01.
    """
    keep = df[contract.target].map(label_text).notna()
    return df.loc[keep].copy()


# --- X / y i split -----------------------------------------------------------------------------


def make_xy(
    df: pd.DataFrame,
    contract: DatasetContract,
    features: Sequence[str],
) -> tuple[pd.DataFrame, pd.Series]:
    """Buduje X (wyłącznie zadeklarowane ALLOWED FEATURES) i y (klasa pozytywna = 1)."""
    problems = feature_list_problems(contract, features)
    if problems:
        raise DataContractError("\n".join(problems))
    X = df.loc[:, list(features)].copy()
    y = encode_target(df[contract.target], contract.positive_class)
    return X, y


def split_train_test(
    X: pd.DataFrame,
    y: pd.Series,
    contract: DatasetContract,
    test_size: float,
    random_state: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split zgodny ze strategią z kontraktu datasetu.

    - ``stratified_random``: losowy podział z zachowaniem proporcji klas,
    - ``time_ordered``: rekordy są uporządkowane w czasie; test to ostatnie rekordy (bez tasowania).
    """
    if contract.split_strategy == "stratified_random":
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state,
            stratify=y,
        )
    elif contract.split_strategy == "time_ordered":
        n_test = math.ceil(len(X) * test_size)
        cut = len(X) - n_test
        X_train, X_test = X.iloc[:cut], X.iloc[cut:]
        y_train, y_test = y.iloc[:cut], y.iloc[cut:]
    else:
        raise DataContractError(f"Nieznana strategia splitu: {contract.split_strategy}.")
    for name, part in (("treningowy", y_train), ("testowy", y_test)):
        if part.nunique() != 2:
            raise DataContractError(f"Zbiór {name} nie zawiera obu klas — sprawdź dane i próbkę.")
    return X_train, X_test, y_train, y_test


# --- próbka CI ---------------------------------------------------------------------------------


def sample_rows(
    df: pd.DataFrame,
    y: pd.Series,
    n_rows: int,
    min_positive: int,
    seed: int,
) -> pd.DataFrame:
    """Losuje próbkę z obiema klasami i zachowuje oryginalną kolejność rekordów.

    Klasa pozytywna (y == 1) ma co najmniej ``min_positive`` rekordów, jeśli tyle ich istnieje.
    Kolejność ma znaczenie dla datasetów ze splitem ``time_ordered``.
    """
    rng = np.random.default_rng(seed)
    positions = np.arange(len(df))
    positive = positions[y.to_numpy() == 1]
    negative = positions[y.to_numpy() == 0]
    n_rows = min(n_rows, len(df))
    n_positive = round(n_rows * len(positive) / len(df))
    n_positive = min(len(positive), max(n_positive, min_positive))
    n_negative = min(len(negative), n_rows - n_positive)
    chosen = np.concatenate(
        [
            rng.choice(positive, size=n_positive, replace=False),
            rng.choice(negative, size=n_negative, replace=False),
        ],
    )
    return df.iloc[np.sort(chosen)]
