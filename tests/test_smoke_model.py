"""Testy scripts/smoke_model.py bez dostępu do W&B: ``wandb`` jest atrapą.

Prawdziwy smoke na artefakcie ``production`` uruchamiamy poza CI (scripts/README.md).
"""

import ast
import importlib.util
import shutil
import sys
from types import ModuleType

import pytest

from asi_project import model_metadata, model_package
from asi_project.data import filter_training_rows, make_xy, normalize_input
from asi_project.metrics import compute_metrics
from asi_project.model import build_baseline_pipeline

SCRIPT = "smoke_model"


def _load_script(repo_root):
    spec = importlib.util.spec_from_file_location(SCRIPT, repo_root / "scripts" / f"{SCRIPT}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def smoke_script(repo_root):
    return _load_script(repo_root)


@pytest.fixture
def package_dir(tmp_path, project):
    config, contract = project.config, project.contract
    features = {
        "numeric": list(config.numeric_features),
        "categorical": list(config.categorical_features),
    }
    df_train = filter_training_rows(normalize_input(project.sample), contract)
    X, y = make_xy(df_train, contract, config.model_features)
    model = build_baseline_pipeline(features["numeric"], features["categorical"])
    model.fit(X, y)
    metadata = model_metadata.build_metadata(
        contract=contract,
        features=features,
        metrics=compute_metrics(y, model.predict(X)),
        model_format="sklearn-joblib",
        model_name="logistic_regression",
        data_fingerprint="sample",
        git_sha="deadbeef",
        library_versions={"python": "3.11"},
    )
    return model_package.save_model_package(model, metadata, tmp_path / "pkg", contract=contract)


def _install_fake_wandb(monkeypatch, package_dir=None, error=None):
    calls = {}

    class FakeArtifact:
        name = "online_shoppers-model:production"
        version = "v3"
        aliases = ["production", "latest"]

        def download(self, root):
            calls["root"] = root
            shutil.copytree(package_dir, root, dirs_exist_ok=True)
            return root

    class FakeApi:
        def artifact(self, path, type=None):
            calls["path"], calls["type"] = path, type
            if error is not None:
                raise error
            return FakeArtifact()

    module = ModuleType("wandb")
    module.Api = FakeApi
    monkeypatch.setitem(sys.modules, "wandb", module)
    return calls


def test_smoke_downloads_production_and_predicts(smoke_script, package_dir, monkeypatch, capsys):
    monkeypatch.setenv("WANDB_ENTITY", "team")
    monkeypatch.setenv("WANDB_PROJECT", "asi")
    calls = _install_fake_wandb(monkeypatch, package_dir)

    assert smoke_script.main([]) == 0

    assert calls["path"] == "team/asi/online_shoppers-model:production"
    assert calls["type"] == "model"
    out = capsys.readouterr().out
    assert "online_shoppers-model:v3" in out
    assert "deadbeef" in out
    assert "SMOKE OK" in out


def test_smoke_reports_missing_access(smoke_script, monkeypatch, capsys):
    monkeypatch.setenv("WANDB_PROJECT", "asi")
    _install_fake_wandb(monkeypatch, error=RuntimeError("permission denied"))

    assert smoke_script.main([]) == smoke_script.EXIT_NO_ACCESS
    err = capsys.readouterr().err
    assert "BRAK DOSTĘPU DO W&B" in err
    assert "wandb login" in err


def test_smoke_fails_on_broken_package(smoke_script, package_dir, monkeypatch, capsys):
    monkeypatch.setenv("WANDB_PROJECT", "asi")
    (package_dir / "model.joblib").unlink()
    _install_fake_wandb(monkeypatch, package_dir)

    assert smoke_script.main([]) == smoke_script.EXIT_FAILED
    assert "SMOKE NIEUDANY" in capsys.readouterr().err


def test_smoke_requires_project(smoke_script, monkeypatch, capsys):
    monkeypatch.delenv("WANDB_PROJECT", raising=False)
    assert smoke_script.main([]) == smoke_script.EXIT_FAILED
    assert "WANDB_PROJECT" in capsys.readouterr().err


def test_smoke_does_not_import_training_code(repo_root):
    """Smoke ma działać bez pipeline'u treningowego i bez Kedro."""
    tree = ast.parse((repo_root / "scripts" / f"{SCRIPT}.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    banned = {"kedro", "autogluon", "asi_project.pipelines", "asi_project.model"}
    assert not {name for name in imported if name.split(".")[0] in banned or name in banned}
