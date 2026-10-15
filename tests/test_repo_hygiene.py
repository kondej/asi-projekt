"""Higiena repozytorium: notebooki bez outputów, reguły .gitignore, aktualne github_issues/."""

import ast
import importlib.util
import json
import shutil
import subprocess

import pytest

FUTURE_PACKAGES = {
    "autogluon",
    "fastapi",
    "google",
    "kedro",
    "kedro_datasets",
    "psycopg",
    "pydantic",
    "pydantic_settings",
    "sqlalchemy",
    "streamlit",
    "wandb",
}
S1_MODULES = (
    "src/asi_project/__init__.py",
    "src/asi_project/config.py",
    "src/asi_project/data.py",
    "src/asi_project/download.py",
    "src/asi_project/metrics.py",
    "src/asi_project/model.py",
)


def _load_script(repo_root, name):
    spec = importlib.util.spec_from_file_location(name, repo_root / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_notebooks_are_valid_and_without_outputs(repo_root):
    for path in sorted((repo_root / "notebooks").glob("*.ipynb")):
        notebook = json.loads(path.read_text(encoding="utf-8"))
        assert notebook["nbformat"] == 4
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                assert cell["outputs"] == [], f"{path.name}: outputy w notebooku"
                assert cell["execution_count"] is None, f"{path.name}: execution_count"


def test_gitignore_rules(repo_root):
    if shutil.which("git") is None or not (repo_root / ".git").exists():
        pytest.skip("Brak repozytorium git — reguły .gitignore sprawdzane tylko w repo.")
    expected = {
        "data/01_raw/ai4i_2020/ai4i2020.csv": True,
        "data/01_raw/sample.csv": False,
        "data/01_raw/README.md": False,
        "data/01_raw/.gitkeep": False,
        "data/02_intermediate/.gitkeep": False,
        "data/06_models/model.pkl": True,
        ".env": True,
        ".env.example": False,
        "metrics.json": False,
        "notebooks/teacher/01_eda_solution.ipynb": True,
        "notebooks/01_eda_teacher.ipynb": True,
        "data/README.md": False,
        "data/02_intermediate/README.md": False,
        "data/02_intermediate/clean.parquet": True,
        "data/08_reporting/metrics.json": True,
        "conf/local/README.md": False,
        "conf/local/credentials.yml": True,
        "conf/base/README.md": False,
    }
    for path, should_be_ignored in expected.items():
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "-q", path],
            cwd=repo_root,
            check=False,
        )
        assert (result.returncode == 0) == should_be_ignored, f".gitignore: {path}"


def test_github_issues_are_generated_from_sprint_docs(repo_root):
    module = _load_script(repo_root, "build_issues")
    assert module.main(["--check"]) == 0, "Uruchom: python scripts/build_issues.py"


def test_sprint1_code_does_not_import_future_dependencies(repo_root):
    paths = [repo_root / name for name in S1_MODULES]
    paths += sorted((repo_root / "scripts").glob("*.py"))
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            roots = {name.split(".")[0] for name in names}
            assert not roots & FUTURE_PACKAGES, f"{path.name}: import {roots & FUTURE_PACKAGES}"


def test_dod_report_has_placeholders_for_future_sprints(repo_root):
    module = _load_script(repo_root, "check_dod")
    for sprint in range(2, 7):
        assert module.main(["--sprint", str(sprint)]) == 0
        assert module.main(["--sprint", str(sprint), "--strict"]) == 2
