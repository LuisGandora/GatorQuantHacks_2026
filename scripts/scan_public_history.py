#!/usr/bin/env python3
"""Scan a Git ref's reachable history for publication-risk markers.

The scanner reads Git blobs, including historical blobs, but never prints blob
contents or matched values. Its report is limited to commit, path, object ID,
object size, and finding category. Findings are markers for human review, not
proof that a licensed-data or credential violation occurred.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import PurePosixPath


ROOT = PurePosixPath(".")
MAX_REPORTED_ROWS = 500

SCOPED_CREDENTIALS = (
    re.compile(rb"(?i)\b(?:MASSIVE|POLYGON)_API_KEY\s*[=:]\s*[\"']?([A-Za-z0-9_\-]{16,})"),
)
GENERIC_CREDENTIALS = (
    re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"(?i)(?:apikey|api_key|api-key|token|password|secret)\s*[=:]\s*[\"']?[A-Za-z0-9_\-]{24,}"),
)
PROVIDER_PAYLOAD_MARKERS = (
    re.compile(rb'"supporting_text"\s*:'),
    re.compile(rb'"filing_url"\s*:'),
    re.compile(rb"api\.(?:massive|polygon)\.io/(?:v\d+/)?(?:vX/)?(?:reference/)?(?:options|tickers|filings)"),
)
PRIVATE_PARTS = {".codex", ".agents", ".opencode", "submission_judge_outputs"}
LICENSED_PATH_PARTS = {
    ".massive_cache", ".polygon_cache", "cache", "caches", "raw", "raw_data",
    "licensed", "audit",
}


def git(*args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.check_output(
        ["git", *args], cwd=str(ROOT), input=input_bytes, stderr=subprocess.PIPE
    )


def path_categories(path: str) -> set[str]:
    parts = {part.lower() for part in PurePosixPath(path).parts}
    categories: set[str] = set()
    if any(part in PRIVATE_PARTS for part in parts):
        categories.add("private_artifact_path")
    if any(part in LICENSED_PATH_PARTS for part in parts) or path.lower().startswith(
        ("data/raw/", "exports/", "runs/audit/")
    ):
        categories.add("licensed_or_private_data_path")
    name = PurePosixPath(path).name.lower()
    if (name.startswith(".env") and name != ".env.example") or PurePosixPath(path).suffix in {
        ".pem", ".key", ".p12", ".pfx",
    }:
        categories.add("credential_or_private_key_path")
    return categories


def content_categories(path: str, content: bytes) -> set[str]:
    categories: set[str] = set()
    placeholder_tokens = (b"your", b"example", b"placeholder", b"redacted", b"changeme", b"replace")
    if any(
        (match := pattern.search(content)) is not None
        and not any(token in match.group(1).lower() for token in placeholder_tokens)
        for pattern in SCOPED_CREDENTIALS
    ):
        categories.add("scoped_provider_credential_marker")
    if any(pattern.search(content) for pattern in GENERIC_CREDENTIALS):
        categories.add("generic_credential_marker")
    if any(pattern.search(content) for pattern in PROVIDER_PAYLOAD_MARKERS):
        categories.add("provider_or_filing_payload_marker")
    if PurePosixPath(path).suffix.lower() == ".ipynb":
        try:
            notebook = json.loads(content)
            if any(cell.get("outputs") for cell in notebook.get("cells", [])):
                categories.add("saved_notebook_output")
        except (ValueError, TypeError, AttributeError):
            categories.add("invalid_notebook_blob")
    if len(content) > 2_000_000:
        categories.add("large_blob_over_2mb")
    return categories


@dataclass(frozen=True)
class Finding:
    commit: str
    path: str
    oid: str
    size: int
    category: str


class BlobReader:
    """Read one blob at a time so large historical payloads are not buffered together."""

    def __enter__(self) -> "BlobReader":
        self.proc = subprocess.Popen(
            ["git", "cat-file", "--batch"], cwd=str(ROOT), stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        return self

    def read(self, oid: str) -> bytes:
        assert self.proc.stdin is not None and self.proc.stdout is not None
        self.proc.stdin.write(oid.encode("ascii") + b"\n")
        self.proc.stdin.flush()
        header = self.proc.stdout.readline().split()
        if len(header) != 3 or header[1] != b"blob":
            raise RuntimeError("Git did not return the requested blob")
        size = int(header[2])
        data = self.proc.stdout.read(size)
        terminator = self.proc.stdout.read(1)
        if len(data) != size or terminator != b"\n":
            raise RuntimeError("Truncated Git blob response")
        return data

    def __exit__(self, *_: object) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.close()
        if self.proc.stdout is not None:
            self.proc.stdout.close()
        if self.proc.stderr is not None:
            self.proc.stderr.close()
        self.proc.wait()


def tree_entries(commit: str) -> list[tuple[str, str, int]]:
    raw = git("ls-tree", "-rlz", "--full-tree", commit)
    entries = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path_bytes = record.split(b"\t", 1)
        fields = metadata.split()
        if fields[1] == b"blob":
            entries.append((path_bytes.decode("utf-8", "surrogateescape"),
                            fields[2].decode("ascii"), int(fields[3])))
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="origin/main", help="ref whose reachable history is scanned")
    args = parser.parse_args()
    try:
        tip = git("rev-parse", "--verify", f"{args.ref}^{{commit}}").decode().strip()
        commits = git("rev-list", "--reverse", tip).decode().splitlines()
    except subprocess.CalledProcessError:
        print("ERROR: ref does not resolve to a commit", file=sys.stderr)
        return 2

    scanned: set[str] = set()
    findings: dict[tuple[str, str, str], Finding] = {}
    blob_categories: dict[tuple[str, str], set[str]] = {}
    with BlobReader() as reader:
        for commit in commits:
            for path, oid, size in tree_entries(commit):
                categories = set(path_categories(path))
                cache_key = (oid, PurePosixPath(path).suffix.lower())
                if cache_key not in blob_categories:
                    blob_categories[cache_key] = content_categories(path, reader.read(oid))
                    scanned.add(oid)
                categories.update(blob_categories[cache_key])
                for category in categories:
                    key = (oid, path, category)
                    findings.setdefault(key, Finding(commit, path, oid, size, category))

    counts = Counter(f.category for f in findings.values())
    print(f"ref={args.ref} tip={tip} commits={len(commits)} unique_blobs_scanned={len(scanned)}")
    print(f"finding_rows={len(findings)} categories={len(counts)}")
    for category, count in sorted(counts.items()):
        print(f"category_count={category}:{count}")
    # Commits were visited oldest-first, so first occurrence identifies when
    # this path/object/category entered the reachable history.
    rows = list(findings.values())
    for finding in rows[:MAX_REPORTED_ROWS]:
        print(f"finding commit={finding.commit} path={finding.path} oid={finding.oid} "
              f"bytes={finding.size} category={finding.category}")
    if len(rows) > MAX_REPORTED_ROWS:
        print(f"rows_omitted={len(rows) - MAX_REPORTED_ROWS}")
    print("Values and blob contents are suppressed; markers require review.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
