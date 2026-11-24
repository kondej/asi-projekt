"""Metadane pakietu modelu: pochodzenie modelu (Git SHA, fingerprint danych, wersje bibliotek)."""

import hashlib
import importlib.metadata
import json
import subprocess
from types import SimpleNamespace

import pytest

from asi_project import model_metadata


def _fake_git(returncode, stdout=""):
    def run(*args, **kwargs):
        return subprocess.CompletedProcess(args, returncode, stdout=stdout, stderr="")

    return run


def _git_missing(*args, **kwargs):
    raise FileNotFoundError("git")


def test_git_sha_comes_from_git(monkeypatch):
    monkeypatch.setattr(model_metadata.subprocess, "run", _fake_git(0, "abc123\n"))
    monkeypatch.setenv("GITHUB_SHA", "from-env")
    assert model_metadata.get_git_sha() == "abc123"


def test_git_sha_falls_back_to_github_sha_when_git_fails(monkeypatch):
    monkeypatch.setattr(model_metadata.subprocess, "run", _fake_git(128))
    monkeypatch.setenv("GITHUB_SHA", "from-env")
    assert model_metadata.get_git_sha() == "from-env"


def test_git_sha_falls_back_to_github_sha_when_git_is_missing(monkeypatch):
    monkeypatch.setattr(model_metadata.subprocess, "run", _git_missing)
    monkeypatch.setenv("GITHUB_SHA", "from-env")
    assert model_metadata.get_git_sha() == "from-env"


def test_git_sha_is_unknown_without_git_and_github_sha(monkeypatch):
    monkeypatch.setattr(model_metadata.subprocess, "run", _git_missing)
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    assert model_metadata.get_git_sha() == model_metadata.UNKNOWN == "unknown"


def _config(tmp_path):
    return SimpleNamespace(root=tmp_path, ci_sample_path=tmp_path / "sample.csv")


def _write_fingerprint(tmp_path, text):
    directory = tmp_path / "data" / "01_raw" / "toy"
    directory.mkdir(parents=True)
    (directory / "fingerprint.json").write_text(text, encoding="utf-8")


def test_data_fingerprint_full_reads_sha256_from_fingerprint_file(tmp_path, toy_contract):
    _write_fingerprint(tmp_path, json.dumps({"sha256": "abc"}))
    result = model_metadata.get_data_fingerprint(_config(tmp_path), toy_contract, "full")
    assert result == "abc"


@pytest.mark.parametrize("content", ["not json", '{"file": "toy.csv"}', "[]"])
def test_data_fingerprint_full_is_unknown_for_broken_file(tmp_path, toy_contract, content):
    _write_fingerprint(tmp_path, content)
    result = model_metadata.get_data_fingerprint(_config(tmp_path), toy_contract, "full")
    assert result == model_metadata.UNKNOWN


def test_data_fingerprint_full_is_unknown_without_file(tmp_path, toy_contract):
    result = model_metadata.get_data_fingerprint(_config(tmp_path), toy_contract, "full")
    assert result == model_metadata.UNKNOWN


def test_data_fingerprint_sample_hashes_ci_sample(tmp_path, toy_contract):
    content = b"num,cat,label\n1,a,yes\n"
    (tmp_path / "sample.csv").write_bytes(content)
    result = model_metadata.get_data_fingerprint(_config(tmp_path), toy_contract, "sample")
    assert result == hashlib.sha256(content).hexdigest()


def test_data_fingerprint_sample_is_unknown_without_file(tmp_path, toy_contract):
    result = model_metadata.get_data_fingerprint(_config(tmp_path), toy_contract, "sample")
    assert result == model_metadata.UNKNOWN


def test_data_fingerprint_rejects_unknown_data_mode(tmp_path, toy_contract):
    with pytest.raises(ValueError, match="Nieznany tryb danych"):
        model_metadata.get_data_fingerprint(_config(tmp_path), toy_contract, "xyz")


def _fake_versions(missing):
    def version(name):
        if name in missing:
            raise importlib.metadata.PackageNotFoundError(name)
        return "1.2.3"

    return version


def test_library_versions_in_current_environment():
    versions = model_metadata.get_library_versions()
    assert {"python", *model_metadata.REQUIRED_LIBRARIES} <= set(versions)
    assert all(isinstance(value, str) and value for value in versions.values())
    json.dumps(versions)


def test_library_versions_skip_missing_optional_libraries(monkeypatch):
    fake = _fake_versions({"autogluon.tabular", "wandb"})
    monkeypatch.setattr(model_metadata.importlib.metadata, "version", fake)
    versions = model_metadata.get_library_versions()
    assert "autogluon.tabular" not in versions
    assert "wandb" not in versions
    assert versions["pandas"] == "1.2.3"


def test_library_versions_mark_missing_required_library_as_unknown(monkeypatch):
    fake = _fake_versions({"pandas"})
    monkeypatch.setattr(model_metadata.importlib.metadata, "version", fake)
    versions = model_metadata.get_library_versions()
    assert versions["pandas"] == model_metadata.UNKNOWN
    assert versions["numpy"] == "1.2.3"
