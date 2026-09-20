"""Prerequisite checks that must not raise. The launcher prints the list and
exits 2 — an agent reading that output knows exactly what to install."""
from __future__ import annotations

import importlib.util
import ssl


def check_prerequisites() -> list[str]:
    problems: list[str] = []
    if importlib.util.find_spec("yaml") is None:
        problems.append("PyYAML is not installed. Install it with: python3 -m pip install PyYAML")
    if ssl.create_default_context().cert_store_stats()["x509_ca"] == 0:
        problems.append("Python has no CA certificates — https fetches will fail. On a python.org macOS install run "
                        "/Applications/Python 3.x/Install Certificates.command, or pip install certifi and set SSL_CERT_FILE")
    return problems
