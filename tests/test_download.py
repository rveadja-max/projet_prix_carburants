"""Tests du téléchargement des archives XML (sans accès réseau)."""
import io
import json
import zipfile

import pytest

from backend import download


def make_zip_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("PrixCarburants_annuel_2025.xml", "<pdv_liste></pdv_liste>")
    return buffer.getvalue()


def fake_opener(payload: bytes, calls: list):
    def open_url(url, timeout):
        calls.append(url)
        return io.BytesIO(payload)

    return open_url


def test_archive_url_contains_year():
    assert download.archive_url(2025).endswith("/opendata/annee/2025")


def test_download_writes_valid_zip_with_checksum(tmp_path):
    payload = make_zip_bytes()
    calls = []

    entry = download.download_archive(2025, tmp_path, open_url=fake_opener(payload, calls))

    target = tmp_path / "PrixCarburants_annuel_2025.zip"
    assert target.read_bytes() == payload
    assert entry["sha256"] == download.sha256_of(target)
    assert entry["size_bytes"] == len(payload)
    assert entry["url"] == calls[0]


def test_existing_archive_is_not_downloaded_again(tmp_path):
    (tmp_path / "PrixCarburants_annuel_2025.zip").write_bytes(make_zip_bytes())
    calls = []

    entry = download.download_archive(2025, tmp_path, open_url=fake_opener(b"", calls))

    assert entry is None
    assert calls == []


def test_force_downloads_again(tmp_path):
    (tmp_path / "PrixCarburants_annuel_2025.zip").write_bytes(b"ancien")
    calls = []

    entry = download.download_archive(
        2025, tmp_path, force=True, open_url=fake_opener(make_zip_bytes(), calls)
    )

    assert entry is not None
    assert len(calls) == 1


def test_invalid_archive_is_rejected_and_not_kept(tmp_path):
    with pytest.raises(ValueError):
        download.download_archive(
            2025, tmp_path, open_url=fake_opener(b"<html>erreur</html>", [])
        )

    assert list(tmp_path.iterdir()) == []


def test_manifest_keeps_previous_entries(tmp_path):
    manifest = tmp_path / "manifest.json"
    download.update_manifest([{"file": "a.zip", "sha256": "1"}], manifest)
    download.update_manifest([{"file": "b.zip", "sha256": "2"}], manifest)

    content = json.loads(manifest.read_text(encoding="utf-8"))

    assert set(content) == {"a.zip", "b.zip"}
