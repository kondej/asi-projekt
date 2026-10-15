"""Tworzy próbkę CI data/01_raw/sample.csv z pełnych danych wybranego datasetu.

Próbka trafia do repozytorium: CI uruchamia na niej testy kontraktu i baseline.
- zawiera obie klasy targetu (co najmniej --min-positive rekordów klasy pozytywnej),
- zachowuje kolejność rekordów (ważne dla datasetów ze splitem time_ordered),
- nie może przekraczać 500 KB (limit hooka check-added-large-files).

Użycie:
    python scripts/make_ci_sample.py [--rows 600] [--min-positive 30] [--seed 42]
"""

import argparse
import sys

from asi_project.config import get_contract, load_project_config
from asi_project.data import encode_target, filter_training_rows, load_dataset, sample_rows
from asi_project.download import sha256_hex

MAX_SAMPLE_KB = 500


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Próbka CI z pełnych danych.")
    parser.add_argument("--rows", type=int, default=600)
    parser.add_argument("--min-positive", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    config = load_project_config()
    contract = get_contract(config)
    df = load_dataset(config, contract, mode="full")
    labelled = filter_training_rows(df, contract)
    y = encode_target(labelled[contract.target], contract.positive_class)
    sample = sample_rows(labelled, y, args.rows, args.min_positive, args.seed)

    path = config.ci_sample_path
    path.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(path, index=False)
    size_kb = path.stat().st_size / 1024
    positives = int(encode_target(sample[contract.target], contract.positive_class).sum())
    print(f"Zapisano: {path} ({len(sample)} rekordów, {size_kb:.0f} KB)")
    print(f"Klasa pozytywna w próbce: {positives} rekordów")
    print(f"SHA-256 próbki: {sha256_hex(path.read_bytes())}")
    if size_kb > MAX_SAMPLE_KB:
        print(f"Próbka przekracza {MAX_SAMPLE_KB} KB — zmniejsz --rows.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
