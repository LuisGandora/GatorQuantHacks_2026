#!/usr/bin/env python3
"""Check Git's index for common publication leaks without printing their contents.

Run from any directory. Stage the intended publication first; by default unstaged
files are excluded so the check describes exactly what a commit would contain.
Use --worktree to inspect tracked and unignored new working files before staging.
No network calls or research stages are run. Exit 1 on findings, 0 on success.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRETS = (
    re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"(?i)(?:apikey|api_key|api-key|token|password|secret)\s*[=:]\s*[\"']?[A-Za-z0-9_\-]{24,}"),
)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def inspect(name, content):
    """Return reasons only; never return matched secret values."""
    reasons = []
    path = Path(name)
    if (path.name.startswith(".env") and path.name != ".env.example") or (
        any(part.startswith((".massive_cache", ".polygon_cache")) for part in path.parts)
        or name.startswith(("data/raw/", "exports/", "runs/audit/", "submission_judge_outputs/"))
        or any(part in {".opencode", ".codex", ".agents"} for part in path.parts)
        or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}
    ):
        reasons.append("private credential/cache/export path")
    if any(pattern.search(content) for pattern in SECRETS):
        reasons.append("possible credential")
    if len(content) > 2_000_000:
        reasons.append("large artifact requires explicit publication review (>2 MB)")
    if re.search(rb"/" + rb"Users/[^/\s]+/|/" + rb"tmp/[^\s]+", content):
        reasons.append("machine-specific absolute path")
    if path.suffix == ".ipynb":
        try:
            notebook = json.loads(content)
            if any(cell.get("outputs") for cell in notebook["cells"]):
                reasons.append("saved notebook outputs")
            if any(cell.get("execution_count") is not None for cell in notebook["cells"]):
                reasons.append("saved notebook execution state")
            if notebook.get("metadata", {}).get("widgets"):
                reasons.append("saved widget state")
        except (ValueError, KeyError, TypeError):
            reasons.append("invalid notebook")
    if path.suffix in {".json", ".jsonl", ".csv", ".md", ".log"}:
        if re.search(rb'"supporting_text"\s*:\s*"', content):
            reasons.append("embedded filing/provider record")
        if path.suffix == ".csv" and b"supporting_text" in content.split(b"\n", 1)[0]:
            reasons.append("filing excerpt CSV")
    return reasons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worktree", action="store_true",
                        help="Check tracked and unignored new working files instead of Git's index.")
    args = parser.parse_args()
    flags = ("--cached", "--others", "--exclude-standard") if args.worktree else ()
    names = git("ls-files", *flags, "-z").decode().split("\0")
    findings = []
    count = 0
    for name in sorted(set(filter(None, names))):
        path = ROOT / name
        if args.worktree and not path.is_file():
            continue
        count += 1
        content = path.read_bytes() if args.worktree else git("show", ":" + name)
        for reason in inspect(name, content):
            findings.append(f"{name}: {reason}")
    if findings:
        print("Publication check FAILED:\n" + "\n".join(findings))
        return 1
    scope = "working files" if args.worktree else "indexed files"
    print(f"PASS: {count} {scope}; no configured publication leaks found.")
    print("Scope: current tree only; history, licensing, and binary content need separate review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
