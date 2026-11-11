"""Spójność conf/ z project.yaml i kontraktem datasetu."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def test_parameters_match_project_yaml():
    params = _load("conf/base/parameters.yml")
    project = _load("project.yaml")
    assert params["dataset"] == project["dataset"]
    assert params["features"] == project["features"]
    assert params["split"] == project["split"]


def test_features_allowed_by_contract():
    params = _load("conf/base/parameters.yml")
    contract = _load("src/asi_project/datasets.yaml")[params["dataset"]]
    features = [*params["features"]["numeric"], *params["features"]["categorical"]]
    assert len(features) == len(set(features))
    assert set(features) <= set(contract["allowed_features"])
    assert params["split"]["strategy"] == contract["split"]


def test_ci_env_uses_sample():
    project = _load("project.yaml")
    ci_catalog = _load("conf/ci/catalog.yml")
    assert ci_catalog["raw_data"]["filepath"] == project["paths"]["ci_sample"]
    assert _load("conf/ci/parameters.yml")["data_mode"] == "sample"
    assert _load("conf/base/parameters.yml")["data_mode"] == "full"
