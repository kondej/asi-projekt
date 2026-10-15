"""Pobieranie zatwierdzonego datasetu ze źródła i zapis odcisku pliku (SHA-256)."""

import hashlib
import io
import json
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from asi_project.config import DatasetContract

USER_AGENT = "asi-project-downloader/1.0"


def extract_member(archive: bytes, member: str) -> bytes:
    """Zwraca zawartość pliku ``member`` z archiwum ZIP, także z zagnieżdżonych archiwów ZIP."""
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        names = zipped.namelist()
        for name in names:
            if Path(name).name == member:
                return zipped.read(name)
        for name in names:
            if name.lower().endswith(".zip"):
                try:
                    return extract_member(zipped.read(name), member)
                except FileNotFoundError:
                    continue
    raise FileNotFoundError(f"Plik {member} nie występuje w archiwum.")


def fetch_bytes(url: str, timeout: int = 120) -> bytes:
    """Pobiera zasób spod adresu URL (https:// albo file:// w testach)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def download_dataset(
    contract: DatasetContract,
    target_dir: Path,
    url: str | None = None,
) -> dict[str, Any]:
    """Pobiera archiwum, wypakowuje plik danych i zapisuje ``fingerprint.json`` obok niego."""
    source = url or contract.download_url
    content = extract_member(fetch_bytes(source), contract.download_member)
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / contract.download_member).write_bytes(content)
    fingerprint = {
        "dataset": contract.dataset_id,
        "source_url": contract.source_url,
        "download_url": source,
        "file": contract.download_member,
        "sha256": sha256_hex(content),
        "size_bytes": len(content),
        "downloaded_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    fingerprint_path = target_dir / "fingerprint.json"
    fingerprint_path.write_text(json.dumps(fingerprint, indent=2) + "\n", encoding="utf-8")
    return fingerprint
