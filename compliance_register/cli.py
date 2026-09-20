"""Command line. Terminal I/O and exit codes only; all logic lives in the
other modules. Exit codes: 0 done · 1 failure · 2 refused."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import __version__, frontmatter as fm, paths, pending, profile, regimes, search, sources, status
from .render import printable
from . import check as checkmod, fetch as fetchmod, rescan as rescanmod

GITIGNORE_LINE = ".search-index.json"


def _cdir() -> Path:
    return paths.compliance_dir(paths.find_root())


def cmd_init(args) -> int:
    root = paths.find_root()
    cdir = paths.compliance_dir(root)
    (cdir / "regimes").mkdir(parents=True, exist_ok=True)
    (cdir / "mirror").mkdir(parents=True, exist_ok=True)
    gi = cdir / "mirror" / ".gitignore"
    if not gi.is_file():
        gi.write_text(".private/\n", encoding="utf-8")
    if not (cdir / "profile.md").is_file():
        fm.save(cdir / "profile.md", profile.empty(), "Notes for the profile go here.\n")
    src = cdir / "sources.json"
    if not src.is_file():
        src.write_text(json.dumps({"schema": 1, "sources": []}, indent=2) + "\n", encoding="utf-8")
    top = cdir / ".gitignore"
    existing = top.read_text(encoding="utf-8") if top.is_file() else ""
    if GITIGNORE_LINE not in existing.splitlines():
        top.write_text(existing + GITIGNORE_LINE + "\n", encoding="utf-8")
    print(f"initialised {cdir.relative_to(root)}")
    return 0


def cmd_status(args) -> int:
    rep = status.report(_cdir())
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        sys.stdout.write(status.render(rep))
    return 0


def cmd_pending(args) -> int:
    entries = pending.list_open(_cdir())
    if args.json:
        print(json.dumps(entries, indent=2))
        return 0
    if not entries:
        print("no pending changes")
        return 0
    for e in entries:
        print(f"{printable(str(e['id']))}  {printable(str(e['severity'])):<5}  {printable(str(e['kind'])):<18}  {printable(str(e['summary']))}")
    return 0


def cmd_resolve(args) -> int:
    try:
        e = pending.resolve(_cdir(), args.id, args.action, by=args.by, note=args.note or "")
    except KeyError:
        print(f"unknown pending id: {printable(args.id)}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(printable(str(exc)), file=sys.stderr)
        return 1
    print(f"{printable(e['id'])} {e['action']} by {printable(e['by'])}")
    return 0


def cmd_search(args) -> int:
    hits = search.search(_cdir(), args.query, k=args.k, kind=args.kind)
    if args.json:
        print(json.dumps([h.__dict__ for h in hits], indent=2))
        return 0
    if not hits:
        print("no hits — try the source's own vocabulary")
        return 0
    for h in hits:
        print(f"{h.score:6.2f}  {h.kind:<7}  {printable(h.path)}\n        {printable(h.snippet)}")
    return 0


def cmd_profile_validate(args) -> int:
    p = profile.load(_cdir())
    if p is None:
        print("no profile.md — run init", file=sys.stderr)
        return 1
    problems = profile.validate(p.meta)
    for x in problems:
        print(printable(x))
    return 1 if problems else 0


def _profile_meta_from(ref: str, cdir: Path) -> dict:
    path = Path(ref)
    if path.is_file():
        return fm.load(path)[0]
    rel = cdir.relative_to(paths.find_root()) / profile.FILENAME
    text = subprocess.run(["git", "show", f"{ref}:{rel.as_posix()}"], capture_output=True, text=True, check=True).stdout
    return fm.loads(text)[0]


def cmd_profile_diff(args) -> int:
    cdir = _cdir()
    cur = profile.load(cdir)
    if cur is None:
        print("no profile.md", file=sys.stderr)
        return 1
    try:
        old = _profile_meta_from(args.against, cdir)
    except subprocess.CalledProcessError as exc:
        print(exc.stderr.strip() or f"cannot read {args.against}", file=sys.stderr)
        return 1
    for slug in profile.diff(old, cur.meta):
        print(slug)
    return 0


def cmd_regimes_validate(args) -> int:
    rs = regimes.load_all(_cdir())
    problems = [f"{r.id}: {x}" for r in rs for x in r.problems]
    for x in problems:
        print(printable(x))
    return 1 if problems else 0


def cmd_sources_validate(args) -> int:
    problems = [x for s in sources.load(_cdir()) for x in sources.validate(s)]
    for x in problems:
        print(printable(x))
    return 1 if problems else 0


def cmd_fetch(args) -> int:
    rep = fetchmod.run(_cdir(), ids=args.source or None, force=args.force, today=args.today or _today())
    print(f"written {rep['written']} · skipped {rep['skipped']} · refused {len(rep['refused'])}")
    for sid, d in rep["details"].items():
        print(f"  {printable(sid)}: {printable(str(d))}")
    return rep["exit"]


def cmd_check(args) -> int:
    rep = checkmod.run(_cdir(), ids=args.source or None, today=args.today or _today())
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        print(f"fresh {rep['fresh']} · moved {rep['moved']} · unreachable {rep['unreachable']}")
        for sid, d in rep["details"].items():
            print(f"  {printable(sid)}: {printable(str(d))}")
        if rep["moved"] or rep["unreachable"]:
            print("see: compliance-register pending")
    return rep["exit"]


def cmd_rescan(args) -> int:
    rep = rescanmod.run(_cdir(), today=args.today or _today())
    if rep.get("error"):
        print(printable(str(rep["error"])), file=sys.stderr); return rep.get("exit", 1)
    print(f"changed: {', '.join(rep['changed']) or 'nothing'} · pending entries written: {rep['entries']}")
    return 0


def _today() -> str:
    import datetime as dt
    return dt.date.today().isoformat()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="compliance-register")
    p.add_argument("--version", action="version", version=f"compliance-register {__version__}")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("init", help="scaffold knowledge-base/compliance/").set_defaults(fn=cmd_init)

    s = sub.add_parser("status", help="counts, profile age, pending"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_status)

    s = sub.add_parser("pending", help="open pending changes"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_pending)

    s = sub.add_parser("resolve", help="record what a human did with a pending entry")
    s.add_argument("id"); s.add_argument("--action", required=True, choices=pending.ACTIONS)
    s.add_argument("--by", required=True); s.add_argument("--note"); s.set_defaults(fn=cmd_resolve)

    s = sub.add_parser("search", help="ranked keyword search")
    s.add_argument("query"); s.add_argument("-k", type=int, default=5)
    s.add_argument("--kind", choices=["regime", "mirror", "profile"]); s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_search)

    pr = sub.add_parser("profile", help="profile.md helpers").add_subparsers(dest="sub", required=True)
    pr.add_parser("validate").set_defaults(fn=cmd_profile_validate)
    d = pr.add_parser("diff"); d.add_argument("--against", required=True, help="a file path or a git ref"); d.set_defaults(fn=cmd_profile_diff)

    rg = sub.add_parser("regimes", help="regime file helpers").add_subparsers(dest="sub", required=True)
    rg.add_parser("validate").set_defaults(fn=cmd_regimes_validate)

    so = sub.add_parser("sources", help="sources.json helpers").add_subparsers(dest="sub", required=True)
    so.add_parser("validate").set_defaults(fn=cmd_sources_validate)

    s = sub.add_parser("fetch", help="acquire or refresh confirmed sources into the mirror")
    s.add_argument("--source", action="append"); s.add_argument("--force", action="store_true"); s.add_argument("--today"); s.set_defaults(fn=cmd_fetch)
    s = sub.add_parser("check", help="did any source move? writes pending entries")
    s.add_argument("--source", action="append"); s.add_argument("--json", action="store_true"); s.add_argument("--today"); s.set_defaults(fn=cmd_check)
    s = sub.add_parser("rescan", help="profile changed? which regimes does it touch")
    s.add_argument("--today"); s.set_defaults(fn=cmd_rescan)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help(sys.stderr)
        return 1
    try:
        return args.fn(args)
    except paths.NotAProject as exc:
        print(f"refused: {printable(str(exc))} — run this inside a project that has a knowledge-base/ directory", file=sys.stderr)
        return 2
    except paths.UnsafePath as exc:
        print(f"refused: {printable(str(exc))}", file=sys.stderr)
        return 2
    except (fm.FrontmatterError, sources.SourcesError) as exc:
        print(f"error: {printable(str(exc))}", file=sys.stderr)
        return 1
