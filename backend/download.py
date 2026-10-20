"""Téléchargement des archives annuelles XML des prix des carburants.

Usage : python -m backend.download [--years 2025 2026] [--force]

Les fichiers vont dans data/raw/historique_xml/ et ne sont jamais modifiés ensuite.
Chaque téléchargement est noté dans manifest.json (URL, date, taille, SHA-256).
Un fichier déjà présent n'est pas retéléchargé, sauf avec --force (utile pour
rafraîchir l'année en cours, qui est mise à jour chaque jour par la source).
"""
import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from backend.config import (
    ANNUAL_ARCHIVE_URL,
    DOWNLOAD_TIMEOUT_SECONDS,
    HISTORY_DIR,
    MANIFEST_FILE,
    SOURCE_PAGE_URL,
    YEARS,
)

USER_AGENT = "projet-prix-carburants (usage pedagogique)"


def archive_url(year: int) -> str:
    return ANNUAL_ARCHIVE_URL.format(year=year)


def archive_path(year: int, dest_dir: Path) -> Path:
    return dest_dir / f"PrixCarburants_annuel_{year}.zip"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def open_remote(url: str, timeout: int):
    return urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=timeout)


def download_archive(year: int, dest_dir: Path = HISTORY_DIR, force: bool = False,
                     open_url=open_remote) -> dict | None:
    """Télécharge l'archive d'une année. Renvoie l'entrée du manifeste, ou None si déjà présente."""
    target = archive_path(year, dest_dir)
    if target.exists() and not force:
        return None

    dest_dir.mkdir(parents=True, exist_ok=True)
    url = archive_url(year)
    partial = target.with_name(target.name + ".part")
    try:
        with open_url(url, DOWNLOAD_TIMEOUT_SECONDS) as response, partial.open("wb") as out:
            shutil.copyfileobj(response, out)
        if not zipfile.is_zipfile(partial):
            raise ValueError(f"Le fichier reçu pour {year} n'est pas une archive ZIP : {url}")
        with zipfile.ZipFile(partial) as archive:
            broken_member = archive.testzip()
        if broken_member is not None:
            raise ValueError(f"Archive {year} corrompue (membre {broken_member}) : {url}")
    except BaseException:
        partial.unlink(missing_ok=True)
        raise

    partial.replace(target)
    return {
        "file": target.name,
        "year": year,
        "url": url,
        "source_page": SOURCE_PAGE_URL,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "size_bytes": target.stat().st_size,
        "sha256": sha256_of(target),
    }


def update_manifest(entries: list[dict], manifest: Path = MANIFEST_FILE) -> None:
    """Ajoute ou remplace les entrées du manifeste, indexées par nom de fichier."""
    content = {}
    if manifest.exists():
        content = json.loads(manifest.read_text(encoding="utf-8"))
    for entry in entries:
        content[entry["file"]] = entry
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(content, indent=2, ensure_ascii=False, sort_keys=True),
                        encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    parser.add_argument("--force", action="store_true", help="retélécharge même si le fichier existe")
    args = parser.parse_args(argv)

    entries = []
    for year in args.years:
        entry = download_archive(year, force=args.force)
        if entry is None:
            print(f"{year} : déjà présent, ignoré ({archive_path(year, HISTORY_DIR)})")
            continue
        print(f"{year} : {entry['size_bytes']:,} octets, sha256 {entry['sha256'][:12]}…")
        entries.append(entry)
    if entries:
        update_manifest(entries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
