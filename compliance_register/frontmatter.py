"""Markdown with a YAML frontmatter block. This is the only module that reads
or writes the block; every other module gets a dict and a body string."""
from __future__ import annotations

import datetime as dt
import os
import tempfile
from pathlib import Path

import yaml

_FENCE = "---"


class FrontmatterError(Exception):
    pass


def loads(text: str) -> tuple[dict, str]:
    if not text.startswith(_FENCE + "\n"):
        return {}, text
    end = text.find("\n" + _FENCE + "\n", len(_FENCE))
    if end < 0:
        # allow a file that ends right after the closing fence
        if text.rstrip("\n").endswith("\n" + _FENCE):
            end = text.rstrip("\n").rfind("\n" + _FENCE)
            block, body = text[len(_FENCE) + 1 : end], ""
        else:
            raise FrontmatterError("frontmatter block is not terminated")
    else:
        block, body = text[len(_FENCE) + 1 : end], text[end + len(_FENCE) + 2 :]
    try:
        meta = yaml.safe_load(block) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - message passthrough
        raise FrontmatterError(f"invalid YAML in frontmatter: {exc}") from exc
    if not isinstance(meta, dict):
        raise FrontmatterError("frontmatter must be a mapping")
    if body.startswith("\n"):
        body = body[1:]
    return _dates_to_str(meta), body


def _dates_to_str(value):
    """PyYAML resolves unquoted `2026-09-20` to a date; everything downstream
    compares and json-dumps strings, so normalise here, once."""
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _dates_to_str(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_dates_to_str(v) for v in value]
    return value


def load(path: Path) -> tuple[dict, str]:
    return loads(path.read_text(encoding="utf-8"))


def dump(meta: dict, body: str) -> str:
    block = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, default_flow_style=False)
    return f"{_FENCE}\n{block}{_FENCE}\n\n{body}"


def save(path: Path, meta: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(dump(meta, body))
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
