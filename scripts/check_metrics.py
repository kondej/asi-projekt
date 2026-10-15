"""Sprawdza plik metrics.json względem kontraktu (schemat, zakresy, dataset, cechy).

Użycie:
    python scripts/check_metrics.py metrics.json [--data-mode full|sample]
"""

import argparse
import sys
from pathlib import Path

from asi_project.config import get_contract, load_project_config
from asi_project.metrics import load_metrics, validate_metrics_record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Walidacja metrics.json.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--data-mode", choices=["full", "sample"])
    args = parser.parse_args(argv)

    config = load_project_config()
    contract = get_contract(config)
    record = load_metrics(args.path)
    problems = validate_metrics_record(record, contract)
    if args.data_mode and record.get("data_mode") != args.data_mode:
        problems.append(f"data_mode: oczekiwano {args.data_mode!r}.")
    if problems:
        print(f"{args.path}: NIEZGODNY z kontraktem")
        for problem in problems:
            print(f"- {problem}")
        return 1
    models = record["models"]
    for name, values in models.items():
        print(f"{name:<20} f1={values['f1']:.3f} recall={values['recall']:.3f}")
    print(f"{args.path}: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
