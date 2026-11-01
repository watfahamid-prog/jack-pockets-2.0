#!/usr/bin/env python3
"""Commit selected task changes to a unique branch and verify an ordinary GitHub push.

An orchestrator should run project checks first, record the task-start commit, and pass
only paths created or changed by that task. The helper refuses other work in the tree,
stages only selected paths, requests explicit interactive approval for deletions and
sensitive files, never force-pushes, and verifies the remote branch SHA.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import os
import re
import shlex
import subprocess
import sys
import uuid
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SENSITIVE_NAMES = {
    ".env", ".env.local", ".env.production", "credentials.json", "secrets.json",
    "id_rsa", "id_ed25519", "known_hosts", "gha-creds.json",
}
SENSITIVE_GLOBS = ("*.pem", "*.key", "*.p12", "*.pfx", "*secret*", "*credential*", "*token*")


def run(args: list[str], *, check: bool = True) -> str:
    proc = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    if check and proc.returncode:
        raise RuntimeError(f"{' '.join(args)} failed ({proc.returncode}):\n{proc.stdout.strip()}")
    return proc.stdout.strip()


def git(*args: str, check: bool = True) -> str:
    return run(["git", *args], check=check)


def normalize_slug(value: str) -> str:
    slug = value.lower().strip().replace(" ", "-")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", slug):
        raise ValueError("branch slug may contain lowercase letters, digits, hyphens and underscores")
    return slug


def changed_paths(base: str) -> set[str]:
    tracked = git("diff", "--name-only", "--no-renames", base, "--").splitlines()
    untracked = git("ls-files", "--others", "--exclude-standard").splitlines()
    return {path for path in (*tracked, *untracked) if path}


def path_is_sensitive(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    return name in SENSITIVE_NAMES or any(fnmatch.fnmatch(name, pattern) for pattern in SENSITIVE_GLOBS)


def validate_path(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or not path.parts or ".." in path.parts or "." in path.parts:
        raise ValueError(f"path must be repository-relative and must not contain '..': {value}")
    normalized = path.as_posix()
    if not (ROOT / Path(*path.parts)).exists() and normalized not in changed_paths("HEAD"):
        raise ValueError(f"selected path does not exist and is not a tracked deletion: {value}")
    return normalized


def is_deletion(path: str, base: str) -> bool:
    deleted = git("diff", "--name-only", "--diff-filter=D", base, "--", path)
    return bool(deleted)


def require_review(paths: list[str], base: str) -> None:
    flagged = [(path, "deletion" if is_deletion(path, base) else "sensitive filename")
               for path in paths if is_deletion(path, base) or path_is_sensitive(path)]
    if not flagged:
        return
    print("Explicit review required for potentially destructive/sensitive changes:")
    for path, reason in flagged:
        print(f"  {path}: {reason}")
    if not sys.stdin.isatty():
        raise RuntimeError("Interactive review is required; no commit or push made.")
    if input("Review the complete staged diff and type REVIEWED to continue: ") != "REVIEWED":
        raise RuntimeError("Review not confirmed; no commit or push made.")


def default_branch() -> str:
    symbolic = git("symbolic-ref", "refs/remotes/origin/HEAD", check=False)
    if symbolic.startswith("refs/remotes/origin/"):
        return symbolic.removeprefix("refs/remotes/origin/")
    if git("show-ref", "--verify", "--quiet", "refs/remotes/origin/main", check=False) == "":
        return "main"
    raise RuntimeError("Cannot determine origin default branch; refusing to guess.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--branch-slug", required=True)
    parser.add_argument("--check", required=True, help="Required project verification command")
    parser.add_argument("--base", default="HEAD", help="Task-start commit, default current HEAD")
    parser.add_argument("--message", help="Commit subject")
    parser.add_argument("paths", nargs="+", help="Exact files changed by this task")
    args = parser.parse_args(argv)
    try:
        slug = normalize_slug(args.branch_slug)
    except ValueError as exc:
        parser.error(str(exc))

    base = git("rev-parse", "--verify", f"{args.base}^{{commit}}")
    if git("diff", "--cached", "--name-only"):
        raise RuntimeError("Refusing to proceed with pre-staged changes; no index changes made.")
    paths = [validate_path(path) for path in args.paths]
    if len(set(paths)) != len(paths):
        raise RuntimeError("Duplicate file paths are not allowed.")
    selected = set(paths)
    changed = changed_paths(base)
    if changed - selected:
        raise RuntimeError("Refusing unrelated changes outside task selection:\n" + "\n".join(sorted(changed - selected)))
    if selected - changed:
        raise RuntimeError("Selected files have no changes relative to task baseline:\n" + "\n".join(sorted(selected - changed)))

    print(f"Running verification: {args.check}", flush=True)
    check = subprocess.run(shlex.split(args.check), cwd=ROOT, shell=False)
    if check.returncode:
        raise RuntimeError(f"Verification failed ({check.returncode}); no branch or commit created.")

    origin = git("remote", "get-url", "origin")
    if "github.com/watfahamid-prog/jack-pockets-2.0" not in origin:
        raise RuntimeError(f"Unexpected origin; refusing to push: {origin}")
    trunk = default_branch()
    current = git("branch", "--show-current")
    if current != trunk and not current.startswith("codex/"):
        raise RuntimeError(f"Current branch {current!r} is not a task branch or {trunk!r}.")
    branch = f"codex/{slug}-{dt.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
    exists = subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=ROOT)
    if exists.returncode == 0:
        raise RuntimeError(f"Generated branch already exists; refusing to reuse: {branch}")
    if current == trunk:
        git("switch", "-c", branch)

    git("add", "--", *paths)
    staged = set(git("diff", "--cached", "--name-only").splitlines())
    if staged != selected:
        raise RuntimeError("Staged set differs from task selection; stopping before commit.")
    require_review(paths, base)
    print("Staged patch:\n" + git("diff", "--cached", "--"), flush=True)
    name = os.environ.get("GIT_AUTHOR_NAME") or git("log", "-1", "--format=%an")
    email = os.environ.get("GIT_AUTHOR_EMAIL") or git("log", "-1", "--format=%ae")
    git("-c", f"user.name={name}", "-c", f"user.email={email}", "commit", "-m",
        args.message or slug.replace("-", " ").replace("_", " ").capitalize())
    git("push", "--set-upstream", "origin", branch)
    commit = git("rev-parse", "HEAD")
    remote = git("ls-remote", "--heads", "origin", f"refs/heads/{branch}")
    if not remote or remote.split()[0] != commit:
        raise RuntimeError("Remote SHA verification failed.")
    print(f"Verified push: {branch} at {commit}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
