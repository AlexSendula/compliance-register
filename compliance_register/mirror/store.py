"""The mirror store: markdown pages with provenance frontmatter, one directory
per source, one MANIFEST.json per source. Sources whose licence forbids
redistribution live under mirror/.private/, which init gitignores."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from .. import frontmatter as fm, paths
from ..sources import Source

MANIFEST = "MANIFEST.json"


def source_dir(cdir: Path, source: Source) -> Path:
    jur = paths.safe_component(source.jurisdiction.lower())
    sid = paths.safe_component(source.id)
    base = cdir / "mirror"
    if not source.redistributable:
        base = base / ".private"
    return base / jur / sid


def content_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode("utf-8")).hexdigest()


def write_page(cdir: Path, source: Source, relpath: str, meta: dict, markdown: str, *, retrieved_at: str) -> Path:
    base = source_dir(cdir, source)
    target = paths.contained(base, Path(relpath))
    full = {
        "source": source.id,
        "source_url": meta.pop("source_url", source.url),
        "retrieved_at": retrieved_at,
        "content_hash": content_hash(markdown),
        "licence": source.licence,
        "attribution": source.licence.get("attribution"),
    }
    full.update(meta)
    fm.save(target, full, markdown)
    return target


def load_manifest(cdir: Path, source: Source) -> dict:
    p = source_dir(cdir, source) / MANIFEST
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if isinstance(v, dict)}


def save_manifest(cdir: Path, source: Source, manifest: dict) -> None:
    p = source_dir(cdir, source) / MANIFEST
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(manifest, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def needs_refresh(entry: dict | None, lastmod: str | None, hash: str | None) -> bool:
    if not isinstance(entry, dict):
        return True
    if hash is not None:
        return entry.get("hash") != hash
    if not lastmod or not entry.get("lastmod"):
        return True  # without a timestamp on both sides we cannot prove it is unchanged
    return entry["lastmod"] != lastmod
