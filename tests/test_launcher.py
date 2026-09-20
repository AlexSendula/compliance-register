import os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "compliance-register"


def run(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(LAUNCHER), *args],
        capture_output=True, text=True, cwd=cwd or ROOT,
    )


def test_launcher_prints_version():
    r = run("--version")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().startswith("compliance-register ")


def test_launcher_is_executable():
    assert os.access(LAUNCHER, os.X_OK)
