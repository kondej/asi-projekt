"""Spójność środowiska: przypięte wersje, kanały conda, mechanizm pre-flightów S2/S3."""

import re

import yaml

PIN = re.compile(r"^([A-Za-z0-9_.\-]+)(\[[^\]]*\])?==([^\s#]+)$")


def _requirements(path):
    pins = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            match = PIN.match(line)
            assert match, f"{path.name}: niepoprawnie przypięta linia: {line!r}"
            pins[match.group(1).lower()] = match.group(3)
    return pins


def _conda_pins(repo_root):
    environment = yaml.safe_load((repo_root / "environment.yml").read_text(encoding="utf-8"))
    return environment, dict(dep.split("=", 1) for dep in environment["dependencies"])


def test_environment_uses_conda_forge_and_pins_everything(repo_root):
    environment, pins = _conda_pins(repo_root)
    assert environment["channels"] == ["conda-forge", "nodefaults"]
    assert pins["python"] == "3.11"
    assert all(re.fullmatch(r"\d+(\.\d+)*", version) for version in pins.values())
    assert "black" not in pins
    assert not any(name.startswith("autogluon") or name == "wandb" for name in pins)


def test_constraints_match_environment(repo_root):
    _, conda = _conda_pins(repo_root)
    constraints = _requirements(repo_root / "constraints.txt")
    for package in ("numpy", "pandas", "scikit-learn", "scipy"):
        assert constraints[package] == conda[package], f"{package}: niespójna wersja"
    for package, version in constraints.items():
        assert conda.get(package) == version, f"{package}: constraints.txt != environment.yml"


def test_preflight_requirements_are_pinned(repo_root):
    s2 = _requirements(repo_root / "requirements" / "preflight-s2.txt")
    s3 = _requirements(repo_root / "requirements" / "preflight-s3.txt")
    assert set(s2) == {"kedro"}
    assert set(s3) == {"wandb", "autogluon.tabular"}
    assert "latest" not in (repo_root / "requirements" / "preflight-s3.txt").read_text()


def test_pre_commit_config_name_and_pinned_revs(repo_root):
    assert not (repo_root / ".pre-commit-config.yml").exists()
    config = yaml.safe_load((repo_root / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    for repo in config["repos"]:
        assert repo["rev"] not in {"main", "master", "HEAD"}
        assert re.fullmatch(r"v?\d+(\.\d+)+", repo["rev"]), repo["rev"]
