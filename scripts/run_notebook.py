"""Wykonuje notebook od początku do końca w nowym kernelu (Restart & Run All) — używane w CI.

Użycie:
    python scripts/run_notebook.py notebooks/02_baseline.ipynb

Zmienne środowiskowe (np. ASI_DATA_MODE=sample, ASI_METRICS_PATH=...) trafiają do kernela.
Wykonany notebook nie jest zapisywany w repozytorium.
"""

import argparse
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Wykonanie notebooka w czystym kernelu.")
    parser.add_argument("notebook", type=Path)
    parser.add_argument("--timeout", type=int, default=600, help="limit na komórkę [s]")
    args = parser.parse_args(argv)

    notebook = nbformat.read(args.notebook, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=args.timeout,
        kernel_name="python3",
        resources={"metadata": {"path": str(args.notebook.resolve().parent)}},
    )
    try:
        client.execute()
    except CellExecutionError as error:
        print(error)
        return 1
    print(f"OK: {args.notebook} wykonany od początku do końca.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
