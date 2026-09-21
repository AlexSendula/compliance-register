import os, shutil, subprocess, sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "compliance-register"


def run(*args, cwd=None, env=None):
    return subprocess.run(
        [sys.executable, str(LAUNCHER), *args],
        capture_output=True, text=True, cwd=cwd or ROOT, env=env,
    )


def _old_python():
    """First interpreter on PATH older than 3.12, as (exe, 'X.Y'); None if there is none.
    Probed, not trusted by name: a pyenv shim can exist and still not run."""
    names = ["python3.%d" % n for n in range(11, 5, -1)] + ["python3"]
    for d in os.environ.get("PATH", "").split(os.pathsep):
        for name in names:
            exe = shutil.which(name, path=d)
            if not exe:
                continue
            probe = "import sys; sys.version_info < (3, 12) and print('%d.%d' % sys.version_info[:2])"
            r = subprocess.run([exe, "-c", probe], capture_output=True, text=True)
            if r.returncode == 0 and r.stdout.strip():
                return exe, r.stdout.strip()
    return None


def test_launcher_prints_version():
    r = run("--version")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().startswith("compliance-register ")


def test_launcher_is_executable():
    assert os.access(LAUNCHER, os.X_OK)


def test_prerequisite_problems_are_listed_and_exit_2_before_cli(tmp_path):
    """sitecustomize swaps check_prerequisites for two problems and poisons the
    cli import: reaching `from compliance_register.cli import main` would traceback."""
    (tmp_path / "sitecustomize.py").write_text(
        "import sys\nfrom compliance_register import preflight\n"
        "preflight.check_prerequisites = lambda: ['one', 'two']\n"
        "sys.modules['compliance_register.cli'] = None\n"
    )
    r = run("--version", env={**os.environ, "PYTHONPATH": f"{tmp_path}{os.pathsep}{ROOT}"})
    assert r.returncode == 2 and r.stdout == ""
    assert r.stderr == "compliance-register cannot start:\n  - one\n  - two\n"


def test_old_python_exits_2_naming_the_found_version_before_any_package_import():
    old = _old_python()
    if old is None:
        pytest.skip("no Python older than 3.12 on PATH")
    exe, found = old
    r = subprocess.run([exe, "-X", "importtime", str(LAUNCHER), "--version"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 2 and r.stdout == ""
    assert f"needs Python 3.12 or newer (found {found})" in r.stderr
    assert "compliance_register" not in r.stderr  # -X importtime lists every import on stderr


def test_old_python_guard_is_deterministic_via_a_patched_version_info(tmp_path):
    """The same guard, on any host: sitecustomize makes this interpreter report 3.11
    before the launcher runs. -X importtime lists every import on stderr, so the
    'no package import' half is asserted, not assumed."""
    (tmp_path / "sitecustomize.py").write_text("import sys\nsys.version_info = (3, 11, 4, 'final', 0)\n")
    r = subprocess.run([sys.executable, "-X", "importtime", str(LAUNCHER), "--version"],
                       capture_output=True, text=True, cwd=ROOT, env={**os.environ, "PYTHONPATH": f"{tmp_path}{os.pathsep}{ROOT}"})
    assert r.returncode == 2 and r.stdout == ""
    assert "needs Python 3.12 or newer (found 3.11)" in r.stderr
    assert "compliance_register" not in r.stderr
