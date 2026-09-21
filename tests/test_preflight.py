import importlib.util
import ssl

from compliance_register import preflight


class _Ctx:
    def __init__(self, n):
        self.n = n

    def cert_store_stats(self):
        return {"x509_ca": self.n, "crl": 0, "x509": self.n}


def test_empty_trust_store_is_named(monkeypatch):
    monkeypatch.setattr(ssl, "create_default_context", lambda: _Ctx(0))
    problems = preflight.check_prerequisites()
    assert any("no CA certificates" in p and "SSL_CERT_FILE" in p for p in problems)
    monkeypatch.setattr(ssl, "create_default_context", lambda: _Ctx(140))
    assert not any("CA certificates" in p for p in preflight.check_prerequisites())


def test_missing_yaml_names_the_pip_command(monkeypatch):
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: None)
    problems = preflight.check_prerequisites()
    assert any("PyYAML" in p and "pip install PyYAML" in p for p in problems)
    monkeypatch.undo()
    assert not any("PyYAML" in p for p in preflight.check_prerequisites())
