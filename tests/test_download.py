"""Pobieranie danych: rozpakowanie (także zagnieżdżonych ZIP-ów) i odcisk SHA-256."""

import hashlib
import io
import json
import zipfile

import pytest

from asi_project.download import download_dataset, extract_member


def _zip(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def test_extract_member_from_nested_archive():
    inner = _zip({"bank-full.csv": b"a;b\n1;2\n", "bank.csv": b"x\n"})
    outer = _zip({"bank.zip": inner, "bank-additional.zip": _zip({"other.csv": b"y\n"})})
    assert extract_member(outer, "bank-full.csv") == b"a;b\n1;2\n"
    with pytest.raises(FileNotFoundError):
        extract_member(outer, "missing.csv")


def test_download_dataset_writes_data_and_fingerprint(toy_contract, tmp_path):
    content = b"num,cat,leak,label\n1,a,0,yes\n"
    archive_path = tmp_path / "toy.zip"
    archive_path.write_bytes(_zip({"folder/toy.csv": content}))
    fingerprint = download_dataset(toy_contract, tmp_path / "raw", url=archive_path.as_uri())
    assert (tmp_path / "raw" / "toy.csv").read_bytes() == content
    assert fingerprint["sha256"] == hashlib.sha256(content).hexdigest()
    saved = json.loads((tmp_path / "raw" / "fingerprint.json").read_text(encoding="utf-8"))
    assert saved["sha256"] == fingerprint["sha256"]
