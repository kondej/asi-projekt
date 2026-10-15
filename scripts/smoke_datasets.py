"""Smoke test prawdziwych źródeł wszystkich zatwierdzonych datasetów (narzędzie prowadzącej).

Dla każdego datasetu z rejestru:
1. pobranie archiwum ze źródła i wypakowanie pliku (jak scripts/download_data.py),
2. odczyt pliku zgodnie z kontraktem (separator, nazwy kolumn),
3. walidacja kontraktu danych,
4. rozkład klas targetu,
5. próbka CI (jak scripts/make_ci_sample.py),
6. walidacja próbki,
7. split zgodny z kontraktem — obie klasy w zbiorze treningowym i testowym
   (na pełnych danych i na próbce).

Wszystko dzieje się w katalogu tymczasowym — do repozytorium nic nie jest zapisywane.

Użycie:
    python scripts/smoke_datasets.py                      # wszystkie datasety z rejestru
    python scripts/smoke_datasets.py --dataset ai4i_2020  # jeden dataset
    python scripts/smoke_datasets.py --archive ai4i_2020=/sciezka/archiwum.zip   # bez sieci
"""

import argparse
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any

import pandas as pd

from asi_project.config import DatasetContract, load_registry
from asi_project.data import (
    encode_target,
    filter_training_rows,
    make_xy,
    normalize_column_names,
    normalize_input,
    sample_rows,
    split_train_test,
    validate,
)
from asi_project.download import download_dataset


def _split_report(frame: pd.DataFrame, contract: DatasetContract) -> str:
    """Split zgodny z kontraktem na wszystkich ALLOWED FEATURES; zgłasza błąd przy jednej klasie."""
    X, y = make_xy(frame, contract, contract.allowed_features)
    _, _, y_train, y_test = split_train_test(X, y, contract, test_size=0.2, random_state=42)
    train = f"train {len(y_train)} ({int(y_train.sum())} poz.)"
    test = f"test {len(y_test)} ({int(y_test.sum())} poz.)"
    return f"{train}, {test}"


def smoke_dataset(contract: DatasetContract, workdir: Path, archive: str | None) -> dict[str, Any]:
    url = Path(archive).resolve().as_uri() if archive else None
    fingerprint = download_dataset(contract, workdir, url=url)
    raw = pd.read_csv(workdir / contract.download_member, **contract.read_csv_kwargs)
    raw = normalize_column_names(raw)
    problems = validate(raw, contract)
    if problems:
        raise AssertionError("Kontrakt danych niespełniony: " + "; ".join(problems))

    known = {contract.target, *contract.allowed_features, *contract.excluded_features}
    excluded_present = [name for name in contract.excluded_features if name in raw.columns]
    undocumented = [name for name in raw.columns if name not in known]

    labelled = filter_training_rows(normalize_input(raw), contract)
    y = encode_target(labelled[contract.target], contract.positive_class)
    split_full = _split_report(labelled, contract)

    sample = sample_rows(labelled, y, n_rows=600, min_positive=30, seed=42)
    sample_path = workdir / "sample.csv"
    sample.to_csv(sample_path, index=False)
    sample_back = normalize_input(normalize_column_names(pd.read_csv(sample_path)))
    sample_problems = validate(sample_back, contract)
    if sample_problems:
        raise AssertionError("Próbka nie spełnia kontraktu: " + "; ".join(sample_problems))
    split_sample = _split_report(filter_training_rows(sample_back, contract), contract)

    return {
        "rows": len(raw),
        "columns": raw.shape[1],
        "sha256": fingerprint["sha256"],
        "positive": f"{int(y.sum())} z {len(y)} ({y.mean():.2%})",
        "sample": f"{len(sample)} rekordów, {sample_path.stat().st_size / 1024:.0f} KB",
        "split_full": split_full,
        "split_sample": split_sample,
        "excluded_present": excluded_present,
        "undocumented": undocumented,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke test źródeł zatwierdzonych datasetów.")
    parser.add_argument("--dataset", action="append", help="id datasetu (można powtórzyć)")
    parser.add_argument("--archive", action="append", default=[], help="id=ścieżka do archiwum")
    args = parser.parse_args(argv)

    registry = load_registry()
    archives = dict(item.split("=", 1) for item in args.archive)
    selected = args.dataset or list(registry)
    failures = 0
    for dataset_id in selected:
        contract = registry[dataset_id]
        source = "lokalne archiwum" if dataset_id in archives else contract.download_url
        print(f"=== {dataset_id} ({source})")
        with tempfile.TemporaryDirectory() as tmp:
            try:
                report = smoke_dataset(contract, Path(tmp), archives.get(dataset_id))
            except Exception:
                failures += 1
                print("BŁĄD:")
                print(traceback.format_exc())
                continue
        for key, value in report.items():
            print(f"  {key:<17} {value}")
        print("  wynik             OK")
    print(f"\nPodsumowanie: {len(selected) - failures} OK, {failures} z błędem.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
