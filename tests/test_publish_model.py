"""Testy scripts/publish_model.py (Sprint 3) bez dostępu do W&B: ``wandb`` jest atrapą."""

import importlib.util
import json
import sys
from types import ModuleType

import pytest

from asi_project import model_metadata, model_package
from asi_project.data import filter_training_rows, make_xy, normalize_input
from asi_project.metrics import compute_metrics
from asi_project.model import build_baseline_pipeline


def _load_publish_script(repo_root):
    path = repo_root / "scripts" / "publish_model.py"
    spec = importlib.util.spec_from_file_location("publish_model", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def publish_script(repo_root):
    return _load_publish_script(repo_root)


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


@pytest.fixture
def fake_wandb(monkeypatch):
    """Atrapa modułu ``wandb``: zapisuje wywołania zamiast wysyłać cokolwiek do sieci."""
    calls = {}

    class FakeArtifact:
        def __init__(self, name, type, description=None, metadata=None):
            calls["artifact"] = {"name": name, "type": type, "metadata": metadata}
            self.dirs = []

        def add_dir(self, path):
            self.dirs.append(path)
            calls["add_dir"] = path

    class FakeLogged:
        entity, project, name = "team", "asi", "online_shoppers-model:v0"

        def wait(self):
            calls["waited"] = True

    class FakeRun:
        def log_artifact(self, artifact, aliases=None):
            calls["aliases"] = aliases
            return FakeLogged()

        def finish(self):
            calls["finished"] = True

    def init(**kwargs):
        calls["init"] = kwargs
        return FakeRun()

    module = ModuleType("wandb")
    module.Artifact = FakeArtifact
    module.init = init
    monkeypatch.setitem(sys.modules, "wandb", module)
    return calls


def test_publish_logs_model_artifact_with_production_alias(
    publish_script, package_dir, fake_wandb, monkeypatch, capsys
):
    monkeypatch.setenv("WANDB_PROJECT", "asi")
    monkeypatch.setenv("WANDB_ENTITY", "team")

    assert publish_script.main(["--package", str(package_dir)]) == 0

    metadata = json.loads((package_dir / "metadata.json").read_text(encoding="utf-8"))
    assert fake_wandb["init"]["project"] == "asi"
    assert fake_wandb["init"]["entity"] == "team"
    assert fake_wandb["init"]["job_type"] == "publish-model"
    assert fake_wandb["artifact"] == {
        "name": "online_shoppers-model",
        "type": "model",
        "metadata": metadata,
    }
    assert fake_wandb["add_dir"] == str(package_dir)
    assert fake_wandb["aliases"] == ["production"]
    assert fake_wandb["waited"] and fake_wandb["finished"]
    assert "team/asi/online_shoppers-model:v0" in capsys.readouterr().out


def test_dry_run_validates_without_wandb(publish_script, package_dir, monkeypatch):
    monkeypatch.setitem(sys.modules, "wandb", None)
    assert publish_script.main(["--package", str(package_dir), "--dry-run"]) == 0


def test_refuses_broken_package(publish_script, package_dir, fake_wandb, monkeypatch, capsys):
    monkeypatch.setenv("WANDB_PROJECT", "asi")
    metadata_path = package_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    del metadata["git_sha"]
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    assert publish_script.main(["--package", str(package_dir)]) == 1
    assert "git_sha" in capsys.readouterr().err
    assert "init" not in fake_wandb


def test_refuses_missing_package(publish_script, tmp_path, fake_wandb, capsys):
    assert publish_script.main(["--package", str(tmp_path / "missing")]) == 1
    assert "Brak katalogu pakietu" in capsys.readouterr().err
    assert "init" not in fake_wandb


def test_requires_wandb_project(publish_script, package_dir, fake_wandb, monkeypatch, capsys):
    monkeypatch.delenv("WANDB_PROJECT", raising=False)
    assert publish_script.main(["--package", str(package_dir)]) == 1
    assert "WANDB_PROJECT" in capsys.readouterr().err
    assert "init" not in fake_wandb
