"""Raport Definition of Done — punkty, które da się sprawdzić automatycznie.

Użycie:
    python scripts/check_dod.py --sprint 1            # raport, kod 0 (informacyjnie w CI)
    python scripts/check_dod.py --sprint 1 --strict   # kod 1, jeśli DoD nie jest spełnione

Automatyczne punkty mają obecnie Sprinty 1 i 2. Punkty kolejnych sprintów są dopisywane do
SPRINT_CHECKS na starcie danego sprintu; do tego czasu raport kieruje do
docs/sprints/SPRINT_N.md, a --strict kończy się kodem 2 (brak automatycznych punktów).

W GitHub Actions raport trafia też do podsumowania joba (GITHUB_STEP_SUMMARY).
Punkty wymagające oceny człowieka (review, ownership, smoke na świeżym klonie) są wypisane
osobno jako lista do ręcznego odhaczenia.
"""

import argparse
import json
import os
import sys
from collections.abc import Callable
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import yaml

from asi_project.config import ConfigError, get_contract, load_project_config
from asi_project.data import (
    encode_target,
    feature_list_problems,
    load_dataset,
    normalize_input,
    validate,
)
from asi_project.metrics import load_metrics, validate_metrics_record
from asi_project.model import build_baseline_pipeline

CARD_MARKERS = ("<!-- KARTA-PROJEKTU:START -->", "<!-- KARTA-PROJEKTU:END -->")
DIAGRAM_MARKERS = ("<!-- DIAGRAM-V0:START -->", "<!-- DIAGRAM-V0:END -->")
SPRINTS = range(1, 7)

Check = tuple[str, bool, str]

MANUAL_ITEMS_S1 = (
    "Każda osoba ma owned item z merytorycznym review innej osoby.",
    "Smoke: świeży klon -> środowisko -> dane -> baseline od zera wykonała osoba inna niż autor.",
    "LogisticRegression porównana z Dummy na metryce głównej (odpowiedzi w notebooku 02).",
    "Pre-flight S2: `kedro info` działa u każdej osoby w zespole.",
)

MANUAL_ITEMS_S2 = (
    "Każda osoba ma własny obszar pracy i zrobiła merytoryczne review PR innej osoby.",
    "Smoke: świeży klon -> środowisko -> dane -> `kedro run` -> model i metryki.",
    "Metryki z `kedro run` (pełne dane) zgodne z baseline'em ze Sprintu 1.",
    "Pipeline używa logiki z data.py; model preprocessing nadal w sklearn Pipeline.",
    "ADR-1 zmergowany; CI na main zielone.",
    "Pre-flight S3: `wandb login` i `python scripts/check_env.py --autogluon` u każdej osoby.",
)

S2_CATALOG = ("raw_data", "training_data", "model", "dummy_model", "metrics")
S2_PIPELINES = ("data_processing", "data_science")


def section_filled(path: Path, markers: tuple[str, str]) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8")
    start, end = markers
    if start not in text or end not in text:
        return False, f"brak znaczników sekcji w {path.name}"
    section = text.split(start, 1)[1].split(end, 1)[0]
    if "TODO" in section:
        return False, f"sekcja w {path.name} zawiera jeszcze TODO"
    return True, "uzupełniona"


def notebooks_clean(root: Path) -> tuple[bool, str]:
    dirty = []
    for path in sorted((root / "notebooks").glob("*.ipynb")):
        notebook = json.loads(path.read_text(encoding="utf-8"))
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code" and (cell.get("outputs") or cell.get("execution_count")):
                dirty.append(path.name)
                break
    return not dirty, "bez outputów" if not dirty else f"outputy w: {dirty}"


def sprint1_checks() -> list[Check]:
    config = load_project_config()
    checks: list[Check] = []
    try:
        contract = get_contract(config)
    except ConfigError as error:
        return [("Dataset wybrany w project.yaml", False, str(error))]
    checks.append(("Dataset wybrany w project.yaml", True, contract.dataset_id))
    readme = config.root / "README.md"
    checks.append(("Karta projektu w README", *section_filled(readme, CARD_MARKERS)))

    sample = None
    if config.ci_sample_path.is_file():
        sample = normalize_input(load_dataset(config, contract, mode="sample"))
        size_kb = config.ci_sample_path.stat().st_size / 1024
        y = encode_target(sample[contract.target].dropna(), contract.positive_class)
        both = y.nunique() == 2
        checks.append(("Próbka CI z obiema klasami", both and size_kb <= 500, f"{size_kb:.0f} KB"))
    else:
        checks.append(("Próbka CI z obiema klasami", False, "brak data/01_raw/sample.csv"))

    feature_problems = feature_list_problems(contract, config.model_features)
    checks.append(("Typy cech w project.yaml", not feature_problems, "; ".join(feature_problems)))
    if sample is not None:
        problems = validate(sample, contract, config)
        checks.append(("Kontrakt danych na próbce", not problems, "; ".join(problems) or "OK"))

    try:
        build_baseline_pipeline(list(config.numeric_features), list(config.categorical_features))
        checks.append(("build_baseline_pipeline zaimplementowany", True, "OK"))
    except NotImplementedError:
        checks.append(("build_baseline_pipeline zaimplementowany", False, "TODO w model.py"))

    if config.metrics_path.is_file():
        record = load_metrics(config.metrics_path)
        problems = validate_metrics_record(record, contract)
        if record.get("data_mode") != "full":
            problems.append("metrics.json musi pochodzić z pełnych danych (data_mode=full)")
        detail = "; ".join(problems) or "OK"
        checks.append(("metrics.json zgodny z kontraktem", not problems, detail))
    else:
        checks.append(("metrics.json zgodny z kontraktem", False, "brak metrics.json"))

    architecture = config.root / "docs" / "architecture.md"
    diagram = section_filled(architecture, DIAGRAM_MARKERS)
    checks.append(("Diagram v0 w docs/architecture.md", *diagram))
    checks.append(("Notebooki bez outputów", *notebooks_clean(config.root)))
    return checks


def read_yaml(path: Path) -> dict:
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def pinned_version(root: Path, package: str) -> str | None:
    requirements = root / "requirements" / "preflight-s2.txt"
    for line in requirements.read_text(encoding="utf-8").splitlines():
        name, sep, pinned = line.split("#")[0].strip().partition("==")
        if sep and name.split("[")[0] == package:
            return pinned
    return None


def sprint2_checks() -> list[Check]:
    config = load_project_config()
    root = config.root
    checks: list[Check] = []

    for package in ("kedro", "kedro-datasets"):
        pinned = pinned_version(root, package)
        try:
            installed = version(package)
        except PackageNotFoundError:
            installed = None
        detail = f"{installed} (wymagane {pinned})"
        checks.append((f"{package} w przypiętej wersji", installed == pinned, detail))

    for name in S2_PIPELINES:
        path = root / "src" / "asi_project" / "pipelines" / name / "pipeline.py"
        ok = path.is_file() and "def create_pipeline" in path.read_text(encoding="utf-8")
        detail = "create_pipeline()" if ok else f"brak create_pipeline() w {name}/pipeline.py"
        checks.append((f"Pipeline {name}", ok, detail))

    catalog = read_yaml(root / "conf" / "base" / "catalog.yml")
    missing = [name for name in S2_CATALOG if name not in catalog]
    detail = f"brak: {', '.join(missing)}" if missing else "OK"
    checks.append(("Data Catalog w conf/base", not missing, detail))

    split = read_yaml(root / "conf" / "base" / "parameters.yml").get("split", {})
    ok = {"test_size", "random_state"} <= set(split)
    detail = "OK" if ok else "brak split.test_size / split.random_state"
    checks.append(("Parametry w conf/base/parameters.yml", ok, detail))

    ci_raw = read_yaml(root / "conf" / "ci" / "catalog.yml").get("raw_data", {})
    ci_mode = read_yaml(root / "conf" / "ci" / "parameters.yml").get("data_mode")
    ci_path = ci_raw.get("filepath")
    ok = bool(ci_path) and (root / ci_path).resolve() == config.ci_sample_path.resolve()
    ok = ok and ci_mode == "sample"
    checks.append(("conf/ci na próbce CI", ok, f"{ci_path}, data_mode={ci_mode}"))

    node_tests = sorted((root / "tests" / "pipelines").glob("test_*.py"))
    detail = ", ".join(p.name for p in node_tests) or "brak tests/pipelines/test_*.py"
    checks.append(("Testy nodów", bool(node_tests), detail))

    adrs = [
        p.name
        for p in sorted((root / "docs" / "adr").glob("*.md"))
        if p.name.lower() != "readme.md" and "template" not in p.name.lower()
    ]
    checks.append(("ADR-1 w docs/adr/", bool(adrs), ", ".join(adrs) or "brak ADR"))

    readme = (root / "README.md").read_text(encoding="utf-8").lower()
    ok = "kedro quickstart" in readme
    checks.append(("Kedro quickstart w README", ok, "OK" if ok else "brak sekcji"))

    kedro_metrics = root / "data" / "08_reporting" / "metrics.json"
    if kedro_metrics.is_file():
        contract = get_contract(config)
        record = load_metrics(kedro_metrics)
        problems = validate_metrics_record(record, contract)
        detail = "; ".join(problems) or f"OK (data_mode={record.get('data_mode')})"
        checks.append(("Metryki z kedro run", not problems, detail))
    else:
        checks.append(("Metryki z kedro run", False, "brak — uruchom `kedro run`"))

    checks.append(("Notebooki bez outputów", *notebooks_clean(root)))
    return checks


# Rejestr automatycznych punktów DoD: numer sprintu -> (funkcja zbierająca punkty, lista ręczna).
# Sprinty 2–6: punkty dopisywane na starcie danego sprintu (checks added when Sprint N starts).
SPRINT_CHECKS: dict[int, tuple[Callable[[], list[Check]], tuple[str, ...]]] = {
    1: (sprint1_checks, MANUAL_ITEMS_S1),
    2: (sprint2_checks, MANUAL_ITEMS_S2),
}


def write_summary(sprint: int, checks: list[Check], manual_items: tuple[str, ...]) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    lines = [f"## Sprint {sprint} — Definition of Done", ""]
    lines += ["| Punkt | Stan | Szczegóły |", "|---|---|---|"]
    for name, ok, detail in checks:
        lines.append(f"| {name} | {'OK' if ok else 'BRAK'} | {detail} |")
    lines += ["", "Do sprawdzenia ręcznie:", ""]
    lines += [f"- [ ] {item}" for item in manual_items]
    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Raport Definition of Done sprintu.")
    parser.add_argument("--sprint", type=int, choices=SPRINTS, default=1, help="numer sprintu")
    parser.add_argument("--strict", action="store_true", help="kod 1, jeśli DoD niespełnione")
    args = parser.parse_args(argv)

    if args.sprint not in SPRINT_CHECKS:
        print(f"Sprint {args.sprint}: automatyczne punkty DoD zostaną dodane na starcie sprintu")
        print(f"(checks added when Sprint {args.sprint} starts).")
        print(f"Pełna Definition of Done: docs/sprints/SPRINT_{args.sprint}.md")
        return 2 if args.strict else 0

    collect, manual_items = SPRINT_CHECKS[args.sprint]
    checks = collect()
    in_actions = os.environ.get("GITHUB_ACTIONS") == "true"
    print(f"Sprint {args.sprint} — Definition of Done (automatycznie sprawdzalne punkty):")
    for name, ok, detail in checks:
        print(f"  [{'OK' if ok else 'BRAK'}] {name}: {detail}")
        if in_actions and not ok:
            print(f"::warning::DoD S{args.sprint}: {name} — {detail}")
    print("Do sprawdzenia ręcznie:")
    for item in manual_items:
        print(f"  [ ] {item}")
    write_summary(args.sprint, checks, manual_items)
    complete = all(ok for _, ok, _ in checks)
    return 1 if args.strict and not complete else 0


if __name__ == "__main__":
    sys.exit(main())
