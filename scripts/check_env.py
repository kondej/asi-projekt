"""Sprawdza środowisko projektu i (opcjonalnie) instalację AutoGluona.

Użycie:
    python scripts/check_env.py               # Python 3.11 i wersje bazowe z constraints.txt
    python scripts/check_env.py --autogluon   # dodatkowo: wersja, pip check, mini-trening

Część --autogluon to techniczny test środowiska (prowadząca, przed zamrożeniem wersji)
i pre-flight gotowości do Sprintu 3 (zespoły, koniec Sprintu 2).
"""

import argparse
import importlib
import re
import subprocess
import sys
import tempfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTOGLUON_BACKENDS = {"lightgbm": "LightGBM", "catboost": "CatBoost"}
PIN = re.compile(r"^\s*([A-Za-z0-9_.\-]+)(\[[^\]]*\])?==([^\s#]+)")


def read_pins(path: Path) -> dict[str, str]:
    """Pakiety przypięte w pliku wymagań (format ``nazwa==wersja``)."""
    pins = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = PIN.match(line)
        if match:
            pins[match.group(1).lower()] = match.group(3)
    return pins


def check_versions(pins: dict[str, str]) -> list[str]:
    problems = []
    for package, expected in pins.items():
        try:
            installed = version(package)
        except PackageNotFoundError:
            problems.append(f"{package}: brak (oczekiwano {expected})")
            continue
        status = "OK" if installed == expected else f"NIEZGODNE (oczekiwano {expected})"
        print(f"  {package:<20} {installed:<12} {status}")
        if installed != expected:
            problems.append(f"{package}: {installed} zamiast {expected}")
    return problems


def check_autogluon() -> list[str]:
    """Import, zgodność wersji, pip check, mini-trening, predict/predict_proba, zapis i odczyt."""
    expected = read_pins(ROOT / "requirements" / "preflight-s3.txt").get("autogluon.tabular")
    try:
        import numpy as np
        import pandas as pd
        from autogluon.tabular import TabularPredictor
    except ImportError as error:
        return [f"Import AutoGluona nie powiódł się: {error}"]

    problems = check_versions({"autogluon.tabular": expected}) if expected else []
    for module in AUTOGLUON_BACKENDS:
        try:
            importlib.import_module(module)
        except (ImportError, OSError) as error:
            hint = " (macOS: brew install libomp)" if module == "lightgbm" else ""
            problems.append(f"Backend {module} nie działa: {error}{hint}")
    pip_check = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        capture_output=True,
        text=True,
        check=False,
    )
    print("  pip check:", "OK" if pip_check.returncode == 0 else pip_check.stdout.strip())
    if pip_check.returncode != 0:
        problems.append("pip check zgłasza konflikty zależności.")

    rng = np.random.default_rng(0)
    frame = pd.DataFrame(
        {
            "num_a": rng.normal(size=400),
            "num_b": rng.normal(size=400),
            "cat": rng.choice(["L", "M", "H"], size=400),
        },
    )
    signal = frame["num_a"] + 0.5 * (frame["cat"] == "H") + rng.normal(scale=0.5, size=400)
    frame["label"] = np.where(signal > 0.3, "yes", "no")
    train, test = frame.iloc[:300], frame.iloc[300:].drop(columns="label")

    with tempfile.TemporaryDirectory() as tmp:
        predictor = TabularPredictor(
            label="label",
            problem_type="binary",
            eval_metric="f1",
            path=str(Path(tmp) / "predictor"),
            verbosity=0,
        )
        predictor.fit(
            train,
            time_limit=120,
            hyperparameters={"GBM": {}, "CAT": {}},
        )
        predictions = predictor.predict(test)
        proba = predictor.predict_proba(test)
        reloaded = TabularPredictor.load(str(Path(tmp) / "predictor"))
        same = reloaded.predict(test).equals(predictions)
    print(f"  mini-trening: modele {predictor.model_names()}")
    print(f"  predict: {len(predictions)} | predict_proba: {proba.shape} | zapis/odczyt: {same}")
    if len(predictions) != len(test) or proba.shape != (len(test), 2):
        problems.append("Nieoczekiwany kształt wyników predict / predict_proba.")
    if not np.allclose(proba.sum(axis=1), 1.0):
        problems.append("predict_proba: wiersze nie sumują się do 1.")
    if not same:
        problems.append("Predyktor po zapisie i odczycie daje inne predykcje.")
    trained = " ".join(predictor.model_names())
    for module, model_name in AUTOGLUON_BACKENDS.items():
        if model_name not in trained:
            problems.append(f"Mini-trening nie wytrenował modelu {model_name} (backend {module}).")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kontrola środowiska projektu ASI.")
    parser.add_argument("--autogluon", action="store_true", help="test instalacji AutoGluona")
    args = parser.parse_args(argv)

    problems = []
    python = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"Python {sys.version.split()[0]}", "OK" if python == "3.11" else "(oczekiwano 3.11)")
    if python != "3.11":
        problems.append(f"Python {python} zamiast 3.11 — aktywuj środowisko asi-ml.")
    print("Wersje bazowe (constraints.txt):")
    problems.extend(check_versions(read_pins(ROOT / "constraints.txt")))
    if args.autogluon:
        print("AutoGluon:")
        problems.extend(check_autogluon())

    if problems:
        print("PROBLEMY:")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print("Środowisko: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
