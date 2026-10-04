#!/usr/bin/env python3
"""Check Git's index for common publication leaks without printing their contents.

Run from any directory. Stage the intended publication first; unstaged files are
deliberately excluded so the check describes exactly what a commit would contain.
No network calls or research stages are run. Exit 1 on findings, 0 on success.
"""
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
        or name.startswith(("data/raw/", "exports/", "runs/audit/"))
        or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}
    ):
        reasons.append("private credential/cache/export path")
    if any(pattern.search(content) for pattern in SECRETS):
        reasons.append("possible credential")
    if path.suffix == ".ipynb":
        try:
            notebook = json.loads(content)
            if any(cell.get("outputs") for cell in notebook["cells"]):
                reasons.append("saved notebook outputs")
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
    names = git("ls-files", "-z").decode().split("\0")
    findings = []
    count = 0
    for name in filter(None, names):
        count += 1
        for reason in inspect(name, git("show", ":" + name)):
            findings.append(f"{name}: {reason}")
    if findings:
        print("Publication check FAILED:\n" + "\n".join(findings))
        return 1
    print(f"PASS: {count} indexed files; no configured publication leaks found.")
    print("Scope: current Git index only; history, licensing, and binary content need separate review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
