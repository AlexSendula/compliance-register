"""Prerequisite checks that must not raise. The launcher prints the list and
exits 2 — an agent reading that output knows exactly what to install."""
from __future__ import annotations

import importlib.util


def check_prerequisites() -> list[str]:
    problems: list[str] = []
    if importlib.util.find_spec("yaml") is None:
        problems.append("PyYAML is not installed. Install it with: python3 -m pip install PyYAML")
    return problems
