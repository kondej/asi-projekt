"""Pobiera pełne dane wybranego datasetu do data/01_raw/<dataset_id>/ (katalog poza gitem).

Użycie:
    python scripts/download_data.py                       # dataset z project.yaml
    python scripts/download_data.py --dataset ai4i_2020   # dowolny dataset z listy

Skrypt zapisuje obok danych plik fingerprint.json (SHA-256 pliku), sprawdza kontrakt danych
i wypisuje rozkład klas targetu.
"""

import argparse
import sys

from asi_project.config import ConfigError, load_project_config, load_registry
from asi_project.data import encode_target, load_dataset, validate
from asi_project.download import download_dataset


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pobranie pełnych danych datasetu.")
    parser.add_argument("--dataset", help="id z docs/datasets.md (domyślnie z project.yaml)")
    parser.add_argument("--url", help="alternatywny adres archiwum (np. kopia lustrzana)")
    args = parser.parse_args(argv)

    config = load_project_config()
    registry = load_registry()
    dataset_id = args.dataset or config.dataset_id
    if not dataset_id:
        print("Nie wybrano datasetu: uzupełnij 'dataset' w project.yaml albo podaj --dataset.")
        return 2
    if dataset_id not in registry:
        raise ConfigError(f"Nieznany dataset '{dataset_id}'. Dozwolone: {sorted(registry)}.")
    contract = registry[dataset_id]

    target_dir = config.root / "data" / "01_raw" / contract.dataset_id
    fingerprint = download_dataset(contract, target_dir, url=args.url)
    print(f"Zapisano: {target_dir / contract.download_member}")
    print(f"SHA-256:  {fingerprint['sha256']}  (wpisz do karty projektu w README)")

    df = load_dataset(config, contract, mode="full")
    print(f"Rozmiar:  {df.shape[0]} rekordów, {df.shape[1]} kolumn")
    problems = validate(df, contract)
    if problems:
        print("Kontrakt danych NIE jest spełniony:")
        for problem in problems:
            print(f"- {problem}")
        return 1
    y = encode_target(df[contract.target].dropna(), contract.positive_class)
    positives = int(y.sum())
    print(f"Klasa pozytywna ({contract.positive_class}): {positives} z {len(y)} ({y.mean():.2%})")
    print("Kontrakt danych: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
