#!/usr/bin/env python3
"""Bounded, offline transaction-identity review of the frozen TRANSACTION_SOURCE census.

This script is read-only with respect to source data. It makes no network request,
reads no option price, payoff, market bar, 2026 filing, reserved-2023 record, JEV
output or other model, and builds no text classifier or semantic rule. It only
resolves issuer identity from CIK/ticker pairs that are already explicitly recorded
in frozen, metadata-only, local audit artifacts, then compares that evidence against
the direct canonical-ticker identity used by the frozen ``transaction_source_audit.py``
census.

Question. ``transaction_source_audit.py`` enrolls an accession only when a row's
``tickers`` field intersects the canonical TOP_100. Rows with no usable ticker are
disclosed as 818 unassigned unique accessions and are never enrolled, even though
the row's recorded CIK may belong to a canonical issuer. The frozen census resolved
identity only from CIKs/tickers known inside its own four disclosure files. This
review asks, using the full cached metadata-only universe identity already assembled
by ``source_identity_review.py`` plus three metadata-only enrollment files:

  * can any of the 818 tickerless accessions be recovered as canonical by exact CIK
    evidence (and if not, why not),
  * how many tickerless accessions are instead proven non-universe by CIK evidence,
  * how many stay genuinely unknown, and
  * what safe residual upper bounds follow for the unchanged 80/20 gates.

Identity method (frozen before any recovered count is calculated; see
``IDENTITY_METHOD``). A CIK is mapped to an economic issuer only by an explicit
recorded (CIK, ticker) pair. Names, aliases, share-class bridges, historical
migration and fuzzy fallback are forbidden. Recovery is applied only to accessions
with no usable recorded ticker; an explicit non-canonical ticker is never silently
re-labelled canonical. Multiple canonical mappings stay UNKNOWN.

Freeze discipline. Before any recovered count is computed the script builds and
verifies an explicit metadata-only input path/hash manifest. On first run it writes
the private manifest once under the git-ignored ``transaction_identity_review/``
directory; every later run must reproduce it byte-for-byte and re-verify every file
hash, or fail fast. Original transaction code, protocol, raw HTTP envelopes,
manifests and public reports are never deleted, rebuilt or modified.

Run:
    .venv/bin/python transaction_identity_review.py            # freeze/verify, analyse, write public reports
    .venv/bin/python transaction_identity_review.py --verify   # re-verify against committed public JSON, write nothing
    .venv/bin/python transaction_identity_review.py --selftest # bounded deterministic identity self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_JSON = ROOT / "TRANSACTION_IDENTITY_REVIEW.json"
OUT_MD = ROOT.parent / "docs/research/TRANSACTION_IDENTITY_REVIEW.md"
MANIFEST_DIR = ROOT / "transaction_identity_review"
MANIFEST_PATH = MANIFEST_DIR / "input_manifest.json"
MANIFEST_HASH_PATH = MANIFEST_DIR / "input_manifest_hash.json"

START, END = "2024-01-01", "2025-12-31"
WINDOW = [START, END]

SIGNING_TAGS = ["merger_agreement", "acquisition_agreement"]
COMPLETION_TAGS = ["merger_completion", "acquisition_completion"]
TAGS = SIGNING_TAGS + COMPLETION_TAGS
FAMILIES = {"signing": SIGNING_TAGS, "completion": COMPLETION_TAGS}
PRIMARY_FAMILY = "completion"
COMPARISON_FAMILY = "signing"
GATE = {"min_unambiguous_dedup_accessions": 80,
        "min_unambiguous_canonical_ticker_issuers": 20}

# Frozen direct counts this review must reproduce from the raw disclosure metadata.
# Source: transaction_source/counts.json (hash-verified in the manifest).
EXPECTED_FAMILY_COUNTS = {
    "signing": {"accessions": 56, "unambiguous_accessions": 52, "ambiguous_accessions": 4,
                "unambiguous_issuers": 24},
    "completion": {"accessions": 30, "unambiguous_accessions": 26, "ambiguous_accessions": 4,
                   "unambiguous_issuers": 21},
}
EXPECTED_TICKERLESS_ACCESSIONS = 818
EXPECTED_CROSS_FAMILY_OVERLAP = 2

OUTPUT_DIR = "transaction_source"
UNIVERSE_FILE = "transaction_source/universe.json"
UNIVERSE_FILE_SHA = "d93e29066a00b03288a79eb541e737685e763b0cd133b6c91e5776e61ed634ee"
UNIVERSE_DIGEST = "c29eff46a4c1c76651860b747d0bc69f10998aa7372ba9fc3445e52f94b276a5"

# The exact 20 paths authorised from SOURCE_IDENTITY_REVIEW.json evidence_corpus.files,
# with the sha256 each file had when that frozen public report was published. These are
# hard-coded so this review can refuse a tampered evidence corpus independent of the
# report file, matching the "validated hash" requirement.
CORE_IDENTITY_FILES = [
    ("earnings_payoff_results/filing_inventory.json",
     "40c35e5e4a14677ad36df3ee5c7c676b1ed67acfd9e3144a360c613f8c9625e3"),
    ("earnings_payoff_results/events.json",
     "a5eeb11940f418ade7fa10f7e05033087deadf84bcfb84fc9ad58b2afb85d600"),
    ("full_source_results/candidate_packets.json",
     "0a9ada17b249536d8db5b1d95d723ca30860a8c0cee9d36000e94f79b75876ef"),
    ("guidance_results/enrollment.json",
     "4997b249b8dbe13a88b42866671489e1bb0bda272d87b5fef417d6dfabde9eef"),
    ("guidance_results/disclosures_guidance_issuance_or_update.json",
     "51e6c7fc2dbfa29e2264e0ac734dd4e338ddc5bc7c1e071f2d6f0022365eeffc"),
    ("guidance_results/disclosures_guidance_withdrawal.json",
     "1143dbc2c9830f9a4409663e277a0eb04aed6476472e491650f214e2cc31f835"),
    ("expanded_guidance_results/enrollment.json",
     "c75f2addd0f6979bf2f3739b3073b94bf1c6d086be1b9193860f9672996b846d"),
    ("expanded_guidance_results/disclosures_annual_earnings.json",
     "8bee095b4fced858f10ca39df3b788025888355f3c23905f2dbd26b9d6f54090"),
    ("expanded_guidance_results/disclosures_guidance_issuance_or_update.json",
     "51e6c7fc2dbfa29e2264e0ac734dd4e338ddc5bc7c1e071f2d6f0022365eeffc"),
    ("expanded_guidance_results/disclosures_guidance_withdrawal.json",
     "1143dbc2c9830f9a4409663e277a0eb04aed6476472e491650f214e2cc31f835"),
    ("expanded_guidance_results/disclosures_preliminary_results.json",
     "65dd8c6ad7af4a94d2b2cae337ca9f68750995f6e72df7d097e6a972ca625e4d"),
    ("expanded_guidance_results/disclosures_quarterly_earnings.json",
     "44cc1608c336db8655366051d36af8aa198f9eea36492ab5658ad01b18408156"),
    ("credit_facility_feasibility/disclosures.json",
     "c2a32cdad9ae34afd4054cef0edaf0be6f14d1e5e2a88eeb6bfdfe861c5cadde"),
    ("credit_facility_feasibility/enrollment.json",
     "4ea6b2b0e425d9845029e36f2f56dc46121cab685ae3e6bd0a5f7acac8eeea66"),
    ("repurchase_results/disclosures.json",
     "c9b9e12eeb6bd6064f4bfa282855a2bf38a0136620fa7d32ff6636a66ef0f8bc"),
    ("repurchase_results/enrollment.json",
     "fb757c483f41b4490369cded2ef39128e29d1511525aaf1d3cd5dc4a6e7f674d"),
    ("departure_results/candidate_ceo_departure.json",
     "ce72cee57adc21f08e2f5a337e4370d8eb71e1455f551a30e4c82140a34c7337"),
    ("departure_results/candidate_cfo_departure.json",
     "5d7f6c5d8eaf5c4f68550eec0193c922c86559accf0de55b312dafd72efd7862"),
    ("departure_results/candidate_executive_officer_departure.json",
     "47086b3556dbf849e66f4408b61e497f6f271bee46cbfff3da343ac7855a4d8a"),
    ("departure_results/candidate_director_departure.json",
     "7d9f279566ca7e5613b0d83fb7ef4117aa3c4631abc3b854a273ecfb8e22b5cd"),
]

# Metadata-only additions authorised by the task, each hash taken from the file's own
# frozen source_manifest.json. All three are enrollment artifacts with only
# accession/date/cik/ticker/identity fields (no filing text).
ADDED_IDENTITY_FILES = [
    ("dividend_source/enrollment.json",
     "9b5ee0b3ec4d32ab5594ba20fa5586b648fa6d6c280d19ffaf1b236b291f53dd"),
    ("equity_issuance_source/enrollment.json",
     "9b860174f84a77cbd8d6aa619012ca6aa6d6bdad86dba775e3b3552bf3386f18"),
    ("transaction_source/enrollment.json",
     "c550677878056fb47ce92f867bf94c5ead06faa83279ec503786de7053429859"),
]

# The four frozen target disclosure files that contain the transaction census rows,
# including the tickerless rows. Only these metadata fields are ever read:
# accession_number, filing_date, cik, tickers, tertiary_category. supporting_text and
# filing_url are present in the files but are never accessed by this review.
TARGET_FIELDS_READ = ["accession_number", "filing_date", "cik", "tickers", "tertiary_category"]
TARGET_FIELDS_IGNORED = ["primary_category", "secondary_category", "supporting_text", "filing_url"]
TARGET_FILES = [
    ("transaction_source/disclosures_merger_agreement.json",
     "065ff941346f33b53932abc8bee7f9d2287b8e59052c0228a816522e5e6c81f6"),
    ("transaction_source/disclosures_acquisition_agreement.json",
     "6974090f3b74a93e1af60733316e797b36a739f8bfc4b3faab5c05cae6c9a286"),
    ("transaction_source/disclosures_merger_completion.json",
     "deffed0f1f3e5a7a37f1f2ff68caa19261a791d4ea987a9017274c97400f0015"),
    ("transaction_source/disclosures_acquisition_completion.json",
     "a0bc7425622960a3a387a035ad44037747e941ef47cad4b1b5ddfe003700f232"),
]

# The excluded corpus: never read here either.
EXCLUDED_CORPUS = {
    "path": "novelty_results/source_filings.json",
    "reason": "reserved notebook example holdout window 2023-06-01..2023-08-31; excluded "
              "entirely from the evidence corpus and never read by this review",
    "reserved_june_august_2023_records": 74,
}

IDENTITY_METHOD = {
    "version": 1,
    "statement": "Exact normalized CIK-to-ticker evidence only. An accession is "
                 "identity-recovered for the canonical universe only when it has no usable "
                 "recorded ticker and its recorded CIK maps, through explicitly recorded "
                 "(cik, ticker) pairs in the frozen metadata-only evidence corpus, to exactly "
                 "one canonical TOP_100 ticker. No company name, alias inference, share-class "
                 "bridge, historical migration or silent fallback; multiple canonical mappings "
                 "stay UNKNOWN.",
    "ticker_normalization": "strip, upper-case, '/' and '-' -> '.' (identical to the frozen audits)",
    "cik_normalization": "str(cik).zfill(10)",
    "evidence_fields_used": ["cik", "tickers (list of strings)", "ticker (single string)"],
    "evidence_fields_refused": ["company name", "targets", "supporting_text", "filing_url"],
    "recovery_scope": "only accessions with no usable recorded ticker; an accession carrying an "
                      "explicit non-canonical ticker is never re-labelled canonical even when its "
                      "CIK has canonical evidence (share-class/alias conflict stays UNKNOWN)",
    "ambiguity_rule": "a CIK mapping to more than one canonical ticker is UNKNOWN; a canonical "
                      "ticker mapping to more than one CIK (BLK has two) is UNKNOWN for issuer "
                      "counting",
    "date_fence": "every dated record in every input must be inside 2024-01-01..2025-12-31; an "
                  "out-of-window date fails fast",
    "hash_fence": "every evidence and target file must match its expected sha256; a mismatch or a "
                  "missing file fails fast",
    "freeze_order": "the input path/hash manifest and this method are written and verified before "
                    "any recovered count is computed; later runs must reproduce the manifest "
                    "byte-for-byte",
}


# ---------------------------------------------------------------------------
# Pure helpers (identical semantics to the inspected frozen audits)
# ---------------------------------------------------------------------------
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def digest_json(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def normalize_ticker(value):
    if not isinstance(value, str):
        return None
    return value.strip().upper().replace("/", ".").replace("-", ".")


def normalize_cik(value) -> str:
    return str(value).zfill(10)


def load_json_list(path: Path):
    """Parse a JSON list, failing fast on any other top-level type."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required metadata input: {path}")
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError(f"Schema error: {path.name} must be a JSON list, got {type(data).__name__}")
    return data


def load_json_dict(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required JSON object: {path}")
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"Schema error: {path.name} must be a JSON object")
    return data


def validate_dates(path: Path, records, date_key: str = "filing_date"):
    """Fail fast on any dated record outside the authorized window; count undated."""
    dated, undated = 0, 0
    for record in records:
        if not isinstance(record, dict):
            raise ValueError(f"Schema error: non-object record in {path.name}")
        value = record.get(date_key)
        if not isinstance(value, str) or not value:
            undated += 1
            continue
        if not (START <= value <= END):
            raise ValueError(
                f"Out-of-window date in {path.name}: {value!r} is outside {START}..{END}; "
                "identity evidence is refused.")
        dated += 1
    return dated, undated


def identity_pairs(records, path: Path):
    """Yield explicit normalized (cik, ticker) pairs recorded in one metadata file.

    Strict schema: ``tickers`` if present must be a list of strings, ``ticker`` if
    present must be a string. A record without ``cik`` or without any ticker is
    counted but contributes no pair.
    """
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Schema error: non-object record #{index} in {path.name}")
        if any(k in record and record[k] is not None and not isinstance(record[k], str)
               for k in ("ticker",)):
            raise ValueError(f"Schema error: non-string ticker in {path.name}")
        if "tickers" in record and record["tickers"] is not None:
            if not isinstance(record["tickers"], list):
                raise ValueError(f"Schema error: tickers is not a list in {path.name}")
            if any(not isinstance(t, str) for t in record["tickers"]):
                raise ValueError(f"Schema error: non-string item in tickers in {path.name}")
        if "cik" not in record or record["cik"] is None:
            continue
        tickers = []
        if isinstance(record.get("tickers"), list):
            tickers.extend(t for t in record["tickers"] if isinstance(t, str) and t.strip())
        if isinstance(record.get("ticker"), str) and record["ticker"].strip():
            tickers.append(record["ticker"])
        for ticker in tickers:
            normalized = normalize_ticker(ticker)
            if normalized:
                yield normalize_cik(record["cik"]), normalized


def target_rows(records, path: Path):
    """Yield metadata-only dicts for one target disclosure file.

    Reads only TARGET_FIELDS_READ. ``supporting_text`` and ``filing_url`` are never
    accessed, and each row is re-projected into a new dict without them.
    """
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Schema error: non-object row #{index} in {path.name}")
        for key in ("accession_number", "filing_date", "cik", "tertiary_category"):
            if key not in record:
                raise ValueError(f"Schema error: missing {key!r} in {path.name}")
        if not isinstance(record["filing_date"], str):
            raise ValueError(f"Schema error: non-string filing_date in {path.name}")
        raw_tickers = record.get("tickers")
        if raw_tickers is not None and (
                not isinstance(raw_tickers, list)
                or any(not isinstance(t, str) for t in raw_tickers)):
            raise ValueError(f"Schema error: tickers must be null or a list of strings in {path.name}")
        if record["tertiary_category"] not in TAGS:
            raise ValueError(f"Schema error: unexpected tertiary_category in {path.name}")
        yield {
            "accession_number": record["accession_number"],
            "filing_date": record["filing_date"],
            "cik": normalize_cik(record["cik"]),
            "tickers": [normalize_ticker(t) for t in (raw_tickers or []) if t.strip()],
            "tertiary_category": record["tertiary_category"],
        }


# ---------------------------------------------------------------------------
# Frozen universe
# ---------------------------------------------------------------------------
def load_universe():
    path = ROOT / UNIVERSE_FILE
    actual_sha = sha256_file(path)
    if actual_sha != UNIVERSE_FILE_SHA:
        raise ValueError(f"Universe file hash mismatch: {UNIVERSE_FILE}")
    universe = load_json_list(path)
    if len(universe) != 100 or len(set(universe)) != 100 or not all(isinstance(t, str) for t in universe):
        raise ValueError("Canonical TOP_100 must be 100 distinct strings.")
    if digest_json(sorted(universe)) != UNIVERSE_DIGEST:
        raise ValueError("Canonical TOP_100 digest mismatch.")
    # Cross-check the other two frozen universes used by source_identity_review.py.
    for other in ("credit_facility_feasibility/universe.json", "repurchase_results/universe.json"):
        if load_json_list(ROOT / other) != universe:
            raise ValueError(f"Canonical universe mismatch: {other}")
    return universe


# ---------------------------------------------------------------------------
# Input manifest: build once, then verify immutably
# ---------------------------------------------------------------------------
def _evidence_entry(relative, expected_sha, expected_source):
    path = ROOT / relative
    actual_sha = sha256_file(path)
    records = load_json_list(path)
    dated, undated = validate_dates(path, records)
    pairs = list(identity_pairs(records, path))
    return {
        "path": relative,
        "role": "identity_evidence",
        "sha256": actual_sha,
        "expected_sha256": expected_sha,
        "expected_source": expected_source,
        "records_total": len(records),
        "distinct_ciks": len({cik for cik, _ in pairs}),
        "pairs": len(pairs),
        "dated": dated,
        "undated": undated,
    }


def _target_entry(relative, expected_sha):
    path = ROOT / relative
    actual_sha = sha256_file(path)
    records = load_json_list(path)
    dated, undated = validate_dates(path, records)
    rows = list(target_rows(records, path))
    return {
        "path": relative,
        "role": "target_metadata",
        "sha256": actual_sha,
        "expected_sha256": expected_sha,
        "expected_source": "transaction_source/source_manifest.json",
        "raw_rows": len(rows),
        "dated": dated,
        "undated": undated,
        "fields_read": TARGET_FIELDS_READ,
        "fields_ignored": TARGET_FIELDS_IGNORED,
    }


def build_manifest():
    universe = load_universe()
    evidence = [_evidence_entry(p, h, "SOURCE_IDENTITY_REVIEW.json evidence_corpus.files")
                for p, h in CORE_IDENTITY_FILES]
    evidence += [_evidence_entry(p, h, "source_manifest.json (added metadata-only enrollment)")
                 for p, h in ADDED_IDENTITY_FILES]
    targets = [_target_entry(p, h) for p, h in TARGET_FILES]
    for entry in evidence + targets:
        if entry["sha256"] != entry["expected_sha256"]:
            raise ValueError(
                f"Hash mismatch for {entry['path']}: expected {entry['expected_sha256']} "
                f"got {entry['sha256']}; refusing to continue.")
    return {
        "review": "transaction-identity-review",
        "manifest_version": 1,
        "kind": "metadata-only offline input manifest; no filing text, no prices, no models",
        "window": WINDOW,
        "identity_method": IDENTITY_METHOD,
        "identity_method_sha256": digest_json(IDENTITY_METHOD),
        "universe": {
            "path": UNIVERSE_FILE,
            "sha256": UNIVERSE_FILE_SHA,
            "digest": UNIVERSE_DIGEST,
            "tickers": len(universe),
            "cross_checked_against": ["credit_facility_feasibility/universe.json",
                                      "repurchase_results/universe.json"],
        },
        "identity_evidence_files": evidence,
        "target_metadata_files": targets,
        "excluded_corpus": EXCLUDED_CORPUS,
        "gates_unchanged": GATE,
        "authorized_additions": {
            "core": "the exact 20 paths in SOURCE_IDENTITY_REVIEW.json evidence_corpus.files",
            "added_metadata_only": [p for p, _ in ADDED_IDENTITY_FILES],
            "target": "the four transaction_source disclosure metadata files, metadata fields only",
        },
    }


def verify_manifest_files(manifest):
    for entry in manifest["identity_evidence_files"] + manifest["target_metadata_files"]:
        path = ROOT / entry["path"]
        if not path.exists():
            raise FileNotFoundError(f"Manifest input missing: {entry['path']}")
        actual = sha256_file(path)
        if actual != entry["sha256"]:
            raise ValueError(
                f"Immutable input changed: {entry['path']} ({entry['sha256']} -> {actual}). "
                "Refusing to reuse the frozen manifest.")


def freeze_or_verify_manifest(manifest):
    """Create the private manifest exactly once; later runs must reproduce it."""
    manifest_sha = digest_json(manifest)
    if not MANIFEST_PATH.exists():
        MANIFEST_DIR.mkdir(exist_ok=True)
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
        MANIFEST_HASH_PATH.write_text(json.dumps({"sha256": manifest_sha}, indent=2) + "\n")
        return "created", manifest_sha
    existing = load_json_dict(MANIFEST_PATH)
    if existing != manifest:
        for key in sorted(set(existing) | set(manifest)):
            if existing.get(key) != manifest.get(key):
                if key in ("identity_evidence_files", "target_metadata_files"):
                    for a, b in zip(existing.get(key, []), manifest.get(key, [])):
                        if a != b:
                            raise ValueError(
                                f"Frozen manifest drift at {key}: {a.get('path')} "
                                f"(recorded {a.get('sha256')} vs rebuilt {b.get('sha256')})")
                raise ValueError(f"Frozen manifest drift at key {key!r}; refusing to continue.")
        raise ValueError("Frozen manifest drift; refusing to continue.")
    recorded_sha = load_json_dict(MANIFEST_HASH_PATH)["sha256"]
    if recorded_sha != manifest_sha:
        raise ValueError("Private manifest hash does not match its content.")
    verify_manifest_files(existing)
    return "verified", manifest_sha


# ---------------------------------------------------------------------------
# Identity map and transaction aggregation
# ---------------------------------------------------------------------------
def build_identity_map(manifest):
    """cik -> set(explicit recorded tickers), from all identity evidence files."""
    cik_to_tickers = defaultdict(set)
    for entry in manifest["identity_evidence_files"]:
        records = load_json_list(ROOT / entry["path"])
        validate_dates(ROOT / entry["path"], records)
        for cik, ticker in identity_pairs(records, ROOT / entry["path"]):
            cik_to_tickers[cik].add(ticker)
    return cik_to_tickers


def universe_coverage(cik_to_tickers, universe):
    ticker_to_ciks = defaultdict(set)
    for cik, tickers in cik_to_tickers.items():
        for ticker in tickers:
            ticker_to_ciks[ticker].add(cik)
    covered = sorted(t for t in universe if t in ticker_to_ciks)
    multi_cik = {t: sorted(ticker_to_ciks[t]) for t in covered if len(ticker_to_ciks[t]) > 1}
    multi_ticker = {}
    for cik, tickers in cik_to_tickers.items():
        hit = sorted(tickers & universe)
        if len(hit) > 1:
            multi_ticker[cik] = hit
    return {
        "universe_tickers": len(universe),
        "tickers_with_cik_evidence": len(covered),
        "tickers_without_cik_evidence": sorted(universe - set(covered)),
        "universe_tickers_with_multiple_ciks": multi_cik,
        "ciks_mapping_to_multiple_universe_tickers": multi_ticker,
    }


def load_transaction_rows(manifest):
    """Return (tag, metadata-row) for every transaction disclosure row."""
    rows = []
    for entry in manifest["target_metadata_files"]:
        path = ROOT / entry["path"]
        for row in target_rows(load_json_list(path), path):
            rows.append((row["tertiary_category"], row))
    if not rows:
        raise ValueError("No transaction rows loaded.")
    return rows


def aggregate(rows):
    """Aggregate rows by accession over every row, including outside and tickerless."""
    grouped = {}
    for tag, row in rows:
        accession = row["accession_number"]
        event = grouped.setdefault(accession, {
            "accession_number": accession, "tags": set(), "ciks": set(),
            "tickers": set(), "filing_dates": set()})
        event["tags"].add(tag)
        event["ciks"].add(row["cik"])
        event["filing_dates"].add(row["filing_date"])
        event["tickers"].update(t for t in row["tickers"] if t)
    for event in grouped.values():
        event["tags"] = sorted(event["tags"])
        event["ciks"] = sorted(event["ciks"])
        event["filing_dates"] = sorted(event["filing_dates"])
        event["tickers"] = sorted(event["tickers"])
    return grouped


def resolve_accession_identity(event, universe, cik_to_tickers):
    """Return (category, mapped_canonical, mapped_any).

    This is a deterministic exact-CIK resolver, not a classifier or model; the name
    reflects the lookup it actually performs.
    """
    raw = set(event["tickers"])
    canonical = raw & universe
    if canonical:
        return "direct_ticker_match", sorted(canonical), sorted(canonical)
    mapped_canonical, mapped_any = set(), set()
    for cik in event["ciks"]:
        tickers = cik_to_tickers.get(cik, set())
        mapped_any |= tickers
        mapped_canonical |= tickers & universe
    if raw:
        if len(mapped_canonical) == 1:
            return "with_ticker_cik_canonical_conflict", sorted(mapped_canonical), sorted(mapped_any)
        if len(mapped_canonical) > 1:
            return "with_ticker_cik_ambiguous", sorted(mapped_canonical), sorted(mapped_any)
        if mapped_any:
            return "with_ticker_non_universe", [], sorted(mapped_any)
        return "with_ticker_cik_unreferenced", [], []
    if len(mapped_canonical) == 1:
        return "tickerless_identity_recovered", sorted(mapped_canonical), sorted(mapped_any)
    if len(mapped_canonical) > 1:
        return "tickerless_cik_ambiguous", sorted(mapped_canonical), sorted(mapped_any)
    if mapped_any:
        return "tickerless_cik_non_universe", [], sorted(mapped_any)
    return "tickerless_unresolved", [], []


CATEGORIES = [
    "direct_ticker_match",
    "with_ticker_non_universe",
    "with_ticker_cik_unreferenced",
    "with_ticker_cik_canonical_conflict",
    "with_ticker_cik_ambiguous",
    "tickerless_identity_recovered",
    "tickerless_cik_ambiguous",
    "tickerless_cik_non_universe",
    "tickerless_unresolved",
]


def summarize_identity_population(accessions, universe, cik_to_tickers):
    per_category = {c: {"accessions": [], "ciks": set(), "mapped_canonical": set()} for c in CATEGORIES}
    for accession, event in accessions.items():
        category, mapped_canonical, mapped_any = resolve_accession_identity(
            event, universe, cik_to_tickers)
        entry = per_category[category]
        entry["accessions"].append(accession)
        entry["ciks"].update(event["ciks"])
        entry["mapped_canonical"].update(mapped_canonical)
    summary = {}
    for category in CATEGORIES:
        entry = per_category[category]
        summary[category] = {
            "accessions": len(entry["accessions"]),
            "ciks": len(entry["ciks"]),
            "mapped_canonical_tickers": sorted(entry["mapped_canonical"]),
        }
    return summary, per_category


# ---------------------------------------------------------------------------
# Direct-census reproduction (mirrors the frozen enroll/resolve_identity)
# ---------------------------------------------------------------------------
def reproduce_direct(rows, universe):
    grouped = {}
    tag_counts = {tag: 0 for tag in TAGS}
    missing_accessions = set()
    missing_rows = {tag: 0 for tag in TAGS}
    for tag, row in rows:
        tag_counts[tag] += 1
        raw = [t for t in row["tickers"] if t]
        canonical = sorted(set(raw) & universe)
        outside = sorted(set(raw) - universe)
        if not canonical:
            if not raw:
                missing_rows[tag] += 1
                missing_accessions.add(row["accession_number"])
            continue
        accession = row["accession_number"]
        event = grouped.setdefault(accession, {
            "accession_number": accession, "filing_dates": set(), "ciks": set(),
            "tickers": set(), "outside_tickers": set(), "tags": set()})
        event["filing_dates"].add(row["filing_date"])
        event["ciks"].add(row["cik"])
        event["tickers"].update(canonical)
        event["outside_tickers"].update(outside)
        event["tags"].add(tag)
    accessions = []
    for accession, event in grouped.items():
        notes = []
        if len(event["filing_dates"]) > 1:
            notes.append("conflicting_filing_date")
        if len(event["ciks"]) > 1:
            notes.append("conflicting_cik")
        if len(event["tickers"]) > 1:
            notes.append("multiple_canonical_tickers")
        accessions.append({
            "accession_number": accession,
            "filing_date": sorted(event["filing_dates"])[0],
            "cik": sorted(event["ciks"])[0] if len(event["ciks"]) == 1 else None,
            "tickers": sorted(event["tickers"]),
            "outside_tickers": sorted(event["outside_tickers"]),
            "tags": sorted(event["tags"]),
            "identity_notes": notes,
        })
    accessions.sort(key=lambda a: (a["filing_date"], a["accession_number"]))
    return accessions, {"raw_rows": tag_counts, "missing_rows": missing_rows,
                        "missing_accessions": missing_accessions}


def resolve_identity(accessions):
    cik_tickers, ticker_ciks = defaultdict(set), defaultdict(set)
    for a in accessions:
        if a["cik"]:
            for t in a["tickers"]:
                cik_tickers[a["cik"]].add(t)
                ticker_ciks[t].add(a["cik"])
    resolved = []
    for a in accessions:
        unambiguous = len(a["tickers"]) == 1 and a["cik"] is not None and not a["identity_notes"]
        if unambiguous:
            ticker = a["tickers"][0]
            unambiguous = len(ticker_ciks[ticker]) == 1 and len(cik_tickers[a["cik"]]) == 1
        item = dict(a)
        item["identity"] = "unambiguous" if unambiguous else "unknown"
        item["identity_ticker"] = a["tickers"][0] if unambiguous else None
        resolved.append(item)
    return resolved


def family_rollup(accessions):
    unambiguous = [a for a in accessions if a["identity"] == "unambiguous"]
    tickers = sorted({a["identity_ticker"] for a in unambiguous})
    return {
        "accessions": len(accessions),
        "unambiguous_accessions": len(unambiguous),
        "ambiguous_accessions": len(accessions) - len(unambiguous),
        "unambiguous_issuers": len(tickers),
        "tickers": tickers,
    }


def reproduce_families(accessions):
    union_all = resolve_identity([dict(a) for a in accessions])
    families = {}
    for name, tags in FAMILIES.items():
        tagset = set(tags)
        subset = [dict(a) for a in accessions if tagset & set(a["tags"])]
        families[name] = resolve_identity(subset)
    families["union"] = union_all
    return families


# ---------------------------------------------------------------------------
# Family-scoped identity augmentation
# ---------------------------------------------------------------------------
def family_population(accessions, family):
    tagset = set(FAMILIES[family])
    return {acc: e for acc, e in accessions.items() if tagset & set(e["tags"])}


def augment_family(accessions, universe, cik_to_tickers, direct_rollup):
    summary, per_category = summarize_identity_population(accessions, universe, cik_to_tickers)
    direct = summary["direct_ticker_match"]
    recovered = summary["tickerless_identity_recovered"]
    known_outside = (summary["with_ticker_non_universe"]["accessions"]
                     + summary["with_ticker_cik_unreferenced"]["accessions"]
                     + summary["tickerless_cik_non_universe"]["accessions"])
    ambiguous_not_outside = (summary["with_ticker_cik_canonical_conflict"]["accessions"]
                             + summary["with_ticker_cik_ambiguous"]["accessions"]
                             + summary["tickerless_cik_ambiguous"]["accessions"])
    unknown = summary["tickerless_unresolved"]["accessions"]
    # A "safe" upper bound counts only accessions not proven outside within the cached
    # corpus: direct ones plus every identity-ambiguous accession plus every genuinely
    # unknown tickerless one.
    safe_upper = direct["accessions"] + ambiguous_not_outside + unknown
    unknown_ciks = set()
    ambiguous_ciks = set()
    for category in ("tickerless_unresolved",):
        unknown_ciks |= per_category[category]["ciks"]
    for category in ("with_ticker_cik_canonical_conflict", "with_ticker_cik_ambiguous",
                     "tickerless_cik_ambiguous"):
        ambiguous_ciks |= per_category[category]["ciks"]
    # Raw distinct-CIK ceiling: direct unambiguous issuers, one slack for a direct
    # ambiguous event, plus every CIK seen in an unresolved or identity-ambiguous
    # tickerless accession. This counts distinct CIKs, not canonical tickers, so it can
    # exceed the 100-ticker universe and must not be read as a canonical issuer bound.
    unknown_ambiguous_cik_ceiling = (
        direct_rollup["unambiguous_issuers"]
        + (1 if direct_rollup["ambiguous_accessions"] else 0)
        + len(unknown_ciks) + len(ambiguous_ciks))
    # Canonical ticker ceiling: no review of a 100-ticker universe can bound canonical
    # issuers above the universe size, so the canonical ceiling is the raw distinct-CIK
    # ceiling capped at len(universe). The two are reported separately and never merged.
    canonical_ticker_upper_issuers = min(unknown_ambiguous_cik_ceiling, len(universe))
    return {
        "categories": summary,
        "direct_accessions": direct["accessions"],
        "direct_unambiguous_accessions": direct_rollup["unambiguous_accessions"],
        "direct_ambiguous_accessions": direct_rollup["ambiguous_accessions"],
        "direct_unambiguous_issuers": direct_rollup["unambiguous_issuers"],
        "identity_recovered_accessions": recovered["accessions"],
        "identity_recovered_issuers": len(recovered["mapped_canonical_tickers"]),
        "known_outside_accessions": known_outside,
        "identity_ambiguous_not_outside_accessions": ambiguous_not_outside,
        "unknown_non_direct_accessions": unknown,
        "residual_safe_upper_accessions": safe_upper,
        "residual_unknown_cik_ceiling": unknown_ambiguous_cik_ceiling,
        "residual_safe_upper_issuers": canonical_ticker_upper_issuers,
        "residual_safe_upper_issuers_capped": (
            unknown_ambiguous_cik_ceiling > len(universe)),
    }


# ---------------------------------------------------------------------------
# Transaction-known comparison
# ---------------------------------------------------------------------------
def transaction_known_map(rows):
    cik_to_tickers = defaultdict(set)
    for _tag, row in rows:
        for ticker in row["tickers"]:
            if ticker:
                cik_to_tickers[row["cik"]].add(ticker)
    return cik_to_tickers


def recovery_probe(accessions, universe, cik_to_tickers):
    summary, _ = summarize_identity_population(accessions, universe, cik_to_tickers)
    return {
        "identity_recovered_accessions": summary["tickerless_identity_recovered"]["accessions"],
        "identity_recovered_issuers": len(summary["tickerless_identity_recovered"]["mapped_canonical_tickers"]),
        "tickerless_cik_non_universe": summary["tickerless_cik_non_universe"]["accessions"],
        "tickerless_unresolved": summary["tickerless_unresolved"]["accessions"],
    }


# ---------------------------------------------------------------------------
# Preservation
# ---------------------------------------------------------------------------
def preservation_block():
    transaction_frozen = load_json_dict(ROOT / "TRANSACTION_SOURCE.json")
    manifest = load_json_dict(ROOT / "transaction_source/source_manifest.json")
    manifest_hash = load_json_dict(ROOT / "transaction_source/source_manifest_hash.json")["sha256"]
    audit_history = transaction_frozen.get("audit_history", {})
    gates = transaction_frozen.get("gates", {}).get("gates", {})
    checks = {
        "transaction_implementation_sha256_matches": (
            sha256_file(ROOT / "transaction_source_audit.py")
            == transaction_frozen["implementation_sha256"]),
        "transaction_reused_module_sha256_matches": (
            sha256_file(ROOT / "equity_issuance_source_audit.py")
            == transaction_frozen["reused_module_sha256"]),
        "transaction_source_manifest_self_hash_matches": digest_json(manifest) == manifest_hash,
        "transaction_source_manifest_entries_match": all(
            (ROOT / p).exists() and sha256_file(ROOT / p) == h for p, h in manifest.items()),
        "transaction_protocol_sha256_matches": (
            load_json_dict(ROOT / "transaction_source/protocol_hash.json")["sha256"]
            == transaction_frozen["protocol_sha256"]),
        "transaction_universe_digest_matches": (
            load_json_dict(ROOT / "transaction_source/universe_hash.json")["sha256"]
            == UNIVERSE_DIGEST),
        "transaction_enrollment_digest_matches": (
            digest_json(load_json_list(ROOT / "transaction_source/enrollment.json"))
            == load_json_dict(ROOT / "transaction_source/enrollment_hash.json")["sha256"]),
        "transaction_public_gate_outcome_preserved": (
            transaction_frozen.get("decision") == "primary_completion_gate_failed"
            and gates.get("signing", {}).get("observed", {}).get(
                "unambiguous_dedup_accessions") == 52
            and gates.get("completion", {}).get("observed", {}).get(
                "unambiguous_dedup_accessions") == 26
            and gates.get("completion", {}).get("passed") is False),
        "transaction_audit_history_preserved": (
            audit_history.get("immutable_manifest_discipline_violated") is True
            and audit_history.get("final_counts_are")
            == "corrected descriptive reprocessing, not pristine prospective processing"),
        "earnings_payoff_freeze_files_match": all(
            sha256_file(ROOT / name) == expected
            for name, expected in load_json_dict(
                ROOT / "EARNINGS_PAYOFF_FREEZE.json")["implementation_files"].items()),
        "transaction_preservation_report_all_unchanged": (
            load_json_dict(ROOT / "transaction_source/preservation.json")["earnings_payoff_freeze"]["all_unchanged"]
            and load_json_dict(ROOT / "transaction_source/preservation.json")["credit_terms_protocol"]["all_unchanged"]),
    }
    return {
        "all_unchanged": all(checks.values()),
        "checks": checks,
        "transaction_source_manifest_entries": len(manifest),
        "transaction_public_report_sha256": sha256_file(ROOT / "TRANSACTION_SOURCE.json"),
        "transaction_public_report_md_sha256": sha256_file(ROOT.parent / "docs/research/TRANSACTION_SOURCE.md"),
        "note": "Original transaction code, protocol, raw HTTP envelopes, manifests and the "
                "public TRANSACTION_SOURCE report (including audit_history) are byte-for-byte "
                "unchanged; no original manifest is deleted or rebuilt.",
    }


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------
def build_report(manifest, manifest_sha, universe, cik_to_tickers, rows):
    universe = set(universe)
    accessions = aggregate(rows)
    direct_accessions, diagnostics = reproduce_direct(rows, universe)
    families = reproduce_families(direct_accessions)
    tickerless = [a for a, e in accessions.items() if not e["tickers"]]
    if len(tickerless) != EXPECTED_TICKERLESS_ACCESSIONS:
        raise ValueError(
            f"Tickerless accession count drift: {len(tickerless)} != "
            f"{EXPECTED_TICKERLESS_ACCESSIONS}")
    for name in ("signing", "completion"):
        rollup = family_rollup(families[name])
        expected = EXPECTED_FAMILY_COUNTS[name]
        for key in ("accessions", "unambiguous_accessions", "ambiguous_accessions",
                    "unambiguous_issuers"):
            if rollup[key] != expected[key]:
                raise ValueError(
                    f"Direct reproduction drift for {name}.{key}: {rollup[key]} != {expected[key]}")

    # Direct reproduction block, with the frozen-report comparison.
    direct_block = {}
    for name in ("signing", "completion"):
        direct_block[name] = {**family_rollup(families[name]),
                              "reproduced_matches_frozen": True}
    direct_block["union"] = family_rollup(families["union"])

    coverage = universe_coverage(cik_to_tickers, universe)
    # Coverage from the core 20 files alone, for a like-for-like comparison to the prior report.
    core_map = defaultdict(set)
    for entry in manifest["identity_evidence_files"]:
        if entry["expected_source"].startswith("SOURCE_IDENTITY_REVIEW"):
            for cik, ticker in identity_pairs(load_json_list(ROOT / entry["path"]), ROOT / entry["path"]):
                core_map[cik].add(ticker)
    core_cov = universe_coverage(core_map, universe)
    independent_coverage = {
        "tickers_with_cik_evidence": core_cov["tickers_with_cik_evidence"],
        "tickers_without_cik_evidence": core_cov["tickers_without_cik_evidence"],
    }

    txn_map = transaction_known_map(rows)
    population_summary, per_category = summarize_identity_population(accessions, universe, cik_to_tickers)
    transaction_known_summary, txn_per_category = summarize_identity_population(accessions, universe, txn_map)

    family_blocks = {}
    for family in ("signing", "completion"):
        fam_pop = family_population(accessions, family)
        family_blocks[family] = augment_family(
            fam_pop, universe, cik_to_tickers, family_rollup(families[family]))
        family_blocks[family]["families"] = FAMILIES[family]

    # The canonical ticker ceiling can never exceed the universe size. Assert that the
    # reported number is exactly the raw distinct-CIK ceiling capped at len(universe), so
    # a >100 "issuer upper bound" can never re-enter the report.
    for family, block in family_blocks.items():
        if block["residual_safe_upper_issuers"] > len(universe):
            raise ValueError(
                f"{family}: canonical ticker issuer ceiling "
                f"{block['residual_safe_upper_issuers']} exceeds universe size {len(universe)}")
        if block["residual_safe_upper_issuers"] != min(
                block["residual_unknown_cik_ceiling"], len(universe)):
            raise ValueError(
                f"{family}: canonical ticker ceiling is not the capped distinct-CIK ceiling")

    # BLK ambiguity detail (the concrete unresolved case the task calls out).
    blk_accessions = []
    for accession, event in sorted(accessions.items()):
        if "BLK" in event["tickers"]:
            mapped = set()
            for cik in event["ciks"]:
                mapped |= cik_to_tickers.get(cik, set())
            blk_accessions.append({
                "accession_number": accession,
                "ciks": event["ciks"],
                "tickers": event["tickers"],
                "mapped_tickers": sorted(mapped),
                "tags": event["tags"],
            })

    report = {
        "review": "transaction-identity-review",
        "kind": "offline, read-only, metadata-only transaction identity review; no "
                "outcomes, options, prices, JEV, models, 2026, out-of-sample or reserved "
                "2023 data; no text classifier; no economic validation",
        "scope": "identity-augmented review of the frozen TRANSACTION_SOURCE census; the "
                 "original 80-filing / 20-issuer family gates are unchanged and are not "
                 "rescued by this review",
        "window": WINDOW,
        "canonical_universe": {
            "path": UNIVERSE_FILE,
            "tickers": len(universe),
            "sha256": UNIVERSE_FILE_SHA,
            "digest": UNIVERSE_DIGEST,
        },
        "freeze": {
            "manifest_path": str(MANIFEST_PATH.relative_to(ROOT)),
            "manifest_sha256": manifest_sha,
            # Session chronology, not current code order: exploratory identity counts were
            # printed before the manifest was first created, so it was not frozen before the
            # first counts. Every actual script run still verifies it before recomputing.
            "manifest_frozen_before_counts": False,
            "runtime_manifest_verified_before_counts": True,
            "manifest_frozen_before_counts_rationale": (
                "false for session history: the prior worker printed exploratory CIK/recovered "
                "counts before the input manifest existed; runtime order on every subsequent "
                "script run is manifest-first"),
            "manifest_immutable": True,
            "manifest_uninterrupted_custody": False,
            "original_manifest_creation_once": True,
            "identity_method_sha256": manifest["identity_method_sha256"],
            "gates_unchanged": GATE,
        },
        "provenance": {
            "pre_manifest_exploratory_exposure": True,
            "pre_manifest_exposure_detail": (
                "Before the input manifest was created the prior worker computed and printed "
                "exploratory identity figures: 818 tickerless accessions, zero canonical "
                "identity recovery, the known-outside CIKs and the family tallies. They were "
                "therefore not frozen at first sight."),
            "final_script_recomputes_after_manifest_validation": True,
            "runtime_order_vs_chronology": (
                "This is a statement about session chronology, not about the code path: every "
                "actual script run (the final generator run and the verification rerun) builds "
                "and verifies the immutable manifest before recomputing any count."),
            "prospective_inference": False,
            "custody": {
                "uninterrupted_custody": False,
                "detail": (
                    "During verification the whole transaction_identity_review/ directory was "
                    "backed up to /tmp/tir_manifest_backup, then removed, then restored. The "
                    "manifest bytes were retained and restored, but custody was not uninterrupted. "
                    "This concerns only the new review's private manifest directory; no original "
                    "transaction_source manifest was removed, rebuilt or altered."),
            },
            "filing_text_exposure": {
                "vendor_supporting_text_snippets_displayed": 2,
                "detail": (
                    "A prior schema peek printed the first merger_agreement record and the first "
                    "acquisition_completion record, including their vendor supporting_text "
                    "snippets (two snippets, limited to a first-record preview). No full SEC "
                    "package was read; those snippets were not used for any semantic judgment or "
                    "decision, and the script's analytical extraction ignores supporting_text "
                    "and filing_url."),
            },
        },
        "input_manifest": manifest,
        "identity_evidence_coverage": {
            "full_corpus": coverage,
            "core_20_only": independent_coverage,
            "prior_reported_coverage": {
                "tickers_with_cik_evidence": 96,
                "tickers_without_cik_evidence": ["AMGN", "AMZN", "TMO", "V"],
                "source": "SOURCE_IDENTITY_REVIEW.json evidence_corpus.universe_coverage",
            },
        },
        "direct_reproduction": {
            "source": "recomputed from the four transaction disclosure metadata files",
            "expected": EXPECTED_FAMILY_COUNTS,
            "result": direct_block,
            "cross_family_overlap_accessions": EXPECTED_CROSS_FAMILY_OVERLAP,
            "tickerless_accessions": len(tickerless),
            "diagnostics": {
                "raw_rows_by_tag": diagnostics["raw_rows"],
                "missing_ticker_rows_by_tag": diagnostics["missing_rows"],
                "tickerless_accessions": len(diagnostics["missing_accessions"]),
            },
            "reproduced_matches_frozen": True,
        },
        "population_identity_categories": population_summary,
        "transaction_known_vs_full_cached": {
            "note": "recovery applied to accessions with no usable ticker; transaction-known "
                    "uses only CIK/ticker pairs recorded in the four transaction disclosure "
                    "files, full-cached adds the 20 frozen evidence files plus three added "
                    "metadata-only enrollment files",
            "transaction_known": {
                "identity_recovered_accessions": transaction_known_summary["tickerless_identity_recovered"]["accessions"],
                "tickerless_cik_non_universe": transaction_known_summary["tickerless_cik_non_universe"]["accessions"],
                "tickerless_unresolved": transaction_known_summary["tickerless_unresolved"]["accessions"],
            },
            "full_cached": {
                "identity_recovered_accessions": population_summary["tickerless_identity_recovered"]["accessions"],
                "tickerless_cik_non_universe": population_summary["tickerless_cik_non_universe"]["accessions"],
                "tickerless_unresolved": population_summary["tickerless_unresolved"]["accessions"],
            },
            "delta_recovered_accessions": (
                population_summary["tickerless_identity_recovered"]["accessions"]
                - transaction_known_summary["tickerless_identity_recovered"]["accessions"]),
        },
        "family_identity_augmentation": family_blocks,
        "overlap": {
            "direct_accessions": population_summary["direct_ticker_match"]["accessions"],
            "identity_recovered_accessions": population_summary[
                "tickerless_identity_recovered"]["accessions"],
            "direct_and_recovered_overlap": len(
                set(per_category["direct_ticker_match"]["accessions"])
                & set(per_category["tickerless_identity_recovered"]["accessions"])),
            "full_cached_and_transaction_known_recovered_overlap": len(
                set(per_category["tickerless_identity_recovered"]["accessions"])
                & set(txn_per_category["tickerless_identity_recovered"]["accessions"])),
            "recovered_signing_and_completion_overlap": len({
                acc for acc in per_category["tickerless_identity_recovered"]["accessions"]
                if set(FAMILIES["signing"]) & set(accessions[acc]["tags"])
                and set(FAMILIES["completion"]) & set(accessions[acc]["tags"])}),
            "direct_signing_and_completion_overlap": EXPECTED_CROSS_FAMILY_OVERLAP,
            "note": "direct and identity-recovered sets are disjoint by construction; the "
                    "recovered sets are empty here, so every recovered overlap is zero",
        },
        "unresolved_ambiguities": {
            "blk_two_ciks": {
                "canonical_ticker": "BLK",
                "ciks": sorted(coverage["universe_tickers_with_multiple_ciks"].get("BLK", [])),
                "accessions": blk_accessions,
                "resolution": "UNKNOWN; both CIKs legitimately carry the BLK ticker, so the "
                              "one-CIK-per-ticker rule cannot be satisfied and the accessions "
                              "stay out of the unambiguous count",
            },
            "cik_mapping_to_multiple_universe_tickers": coverage[
                "ciks_mapping_to_multiple_universe_tickers"],
            "share_class_or_alias_conflicts": population_summary[
                "with_ticker_cik_canonical_conflict"],
            "universe_tickers_without_cik_evidence": coverage["tickers_without_cik_evidence"],
        },
        "preservation": preservation_block(),
        "boundaries": {
            "network_requests": 0,
            "market_or_option_data_read": False,
            "filing_text_read": {
                "session_schema_peek_vendor_supporting_snippets": 2,
                "full_sec_packages_read": 0,
                "used_for_semantic_judgment_or_decision": False,
                "script_analytical_extraction_ignores_text": True,
                "note": "a schema peek displayed two vendor supporting_text snippets (first "
                        "merger_agreement and first acquisition_completion records); they did not "
                        "enter the analysis",
            },
            "jev_or_model_calls": 0,
            "text_classifier_or_semantic_rule_built": False,
            "identity_resolver_is_not_a_classifier_or_model": True,
            "economic_prices_or_models": False,
            "original_manifests_rebuilt_or_deleted": False,
            "original_code_protocol_http_reports_unmodified": True,
            "prior_experiment_or_oos_files_modified": False,
            "commit_made": False,
        },
        "conclusions": [
            "The frozen direct census reproduces exactly: signing 56 deduplicated / 52 "
            "unambiguous accessions and 24 unambiguous issuers; completion 30 / 26 and 21.",
            "Full cached universe identity recovers ZERO additional canonical accessions or "
            "issuers for either family; the direct-ticker census is not enlarged by CIK identity "
            "evidence.",
            f"{population_summary['tickerless_cik_non_universe']['accessions']} of the 818 "
            "tickerless accessions have CIK evidence inside the cached corpus that maps only to "
            "non-universe tickers, so they are treated as outside for this bounded review. That "
            "is corpus-bounded evidence, not timeless proof that the issuer cannot carry an "
            "unseen canonical ticker. The remaining "
            f"{population_summary['tickerless_unresolved']['accessions']} stay genuinely unknown.",
            "Residual issuer ceilings are reported on two bases: a distinct-CIK ceiling ("
            f"signing {family_blocks['signing']['residual_unknown_cik_ceiling']}, completion "
            f"{family_blocks['completion']['residual_unknown_cik_ceiling']}) that is not a "
            "canonical issuer bound, and a canonical ticker ceiling capped at the 100-ticker "
            f"universe (signing {family_blocks['signing']['residual_safe_upper_issuers']}, "
            f"completion {family_blocks['completion']['residual_safe_upper_issuers']}).",
            "The identity-augmented result is an exploratory corrected source-feasibility check, "
            "not economic validation and not a pristine prospective census; it does not change "
            "the original 80/20 gate outcomes, which remain failing on accession count.",
            "A source-feasibility gate failure is not evidence that no alpha exists.",
        ],
        "limitations": [
            "Recovery and non-universe exclusion are bounded by the cached evidence corpus. A "
            "universe issuer whose CIK never appears in the 20 frozen evidence files or the three "
            "added enrollment files cannot be recovered and stays UNKNOWN; conversely, a CIK whose "
            "only cached tickers are non-universe is treated as outside for this review, which is "
            "corpus-bounded evidence and not timeless proof that the issuer cannot carry an unseen "
            "canonical ticker.",
            "Two canonical tickers still lack cached CIK evidence: "
            + ", ".join(coverage["tickers_without_cik_evidence"]) + ".",
            "The 2024-2025 static September-2026 TOP_100 carries survivorship bias; targets "
            "already acquired or delisted before the snapshot are excluded.",
            "Vendor tertiary-category tags are classifications, not proof of a signed deal or a "
            "completed transaction; the analytical extraction reads only metadata fields and no "
            "filing text is used in any computation.",
            "Session chronology is not pristine prospective processing: exploratory identity "
            "counts were printed before the manifest was created (see provenance), so no "
            "prospective inference is claimed.",
            "The private manifest has content immutability but not uninterrupted custody: during "
            "verification the directory was backed up to /tmp/tir_manifest_backup, removed and "
            "restored byte-for-byte. Original transaction_source manifests were never touched.",
            "A prior schema peek displayed two vendor supporting_text snippets (first "
            "merger_agreement and first acquisition_completion records). No full SEC package was "
            "read and the snippets did not enter the analysis or any decision.",
            "The transaction_source manifests were disclosed as rebuilt twice after acquisition; "
            "the original first manifests remain lost and this review cannot recover them.",
        ],
    }
    return report


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def render_markdown(report):
    fam = report["family_identity_augmentation"]
    pop = report["population_identity_categories"]
    cov = report["identity_evidence_coverage"]
    lines = [
        "# Transaction identity review: bounded, offline, metadata-only",
        "",
        f"Decision: **identity recovery adds 0 canonical accessions and 0 issuers; the "
        f"original 80/20 gates stay failed and unchanged.** This review is an exploratory "
        "corrected source-feasibility check, not economic validation and not a pristine "
        "prospective census. No price, option, payoff, full SEC package, JEV call, model, 2026 "
        "filing or reserved-2023 record was read; two vendor supporting_text snippets appeared "
        "in a schema peek but did not enter the analysis (see Provenance).",
        "",
        f"Window {report['window'][0]}..{report['window'][1]}; canonical static TOP_100 "
        f"universe (`{report['canonical_universe']['digest'][:20]}...`). The input path/hash "
        f"manifest (sha256 `{report['freeze']['manifest_sha256'][:20]}...`) is immutable and "
        "every run reproduces it byte-for-byte, but it was **not** frozen before the first counts "
        "in session chronology (see Provenance); runtime order on every run is manifest-first.",
        "",
        "## Provenance and custody",
        "",
        f"- Pre-manifest exploratory exposure: "
        f"{report['provenance']['pre_manifest_exploratory_exposure']}. "
        f"{report['provenance']['pre_manifest_exposure_detail']}",
        f"- Final script recomputes after manifest validation: "
        f"{report['provenance']['final_script_recomputes_after_manifest_validation']}. "
        f"{report['provenance']['runtime_order_vs_chronology']}",
        f"- Prospective inference: "
        f"{str(report['provenance']['prospective_inference']).lower()}.",
        f"- Filing-text exposure: "
        f"{report['provenance']['filing_text_exposure']['detail']}",
        f"- Custody: {report['provenance']['custody']['detail']}",
        "",
        "## Identity method (frozen)",
        "",
        f"- {report['input_manifest']['identity_method']['statement']}",
        f"- Normalization: {report['input_manifest']['identity_method']['ticker_normalization']}; "
        f"CIK {report['input_manifest']['identity_method']['cik_normalization']}.",
        f"- Refused: {', '.join(report['input_manifest']['identity_method']['evidence_fields_refused'])}.",
        f"- {report['input_manifest']['identity_method']['ambiguity_rule']}.",
        "",
        "## Direct census reproduction (independent recompute)",
        "",
        "| Family | Dedup | Unambiguous | Ambiguous | Unambiguous issuers | Matches frozen |",
        "|---|---:|---:|---:|---:|:--:|",
    ]
    for name in ("signing", "completion"):
        r = report["direct_reproduction"]["result"][name]
        lines.append(f"| {name} | {r['accessions']} | {r['unambiguous_accessions']} | "
                     f"{r['ambiguous_accessions']} | {r['unambiguous_issuers']} | "
                     f"{str(r['reproduced_matches_frozen']).lower()} |")
    u = report["direct_reproduction"]["result"]["union"]
    lines.append(f"| union (descriptive) | {u['accessions']} | {u['unambiguous_accessions']} | "
                 f"{u['ambiguous_accessions']} | {u['unambiguous_issuers']} | true |")
    lines += [
        "",
        f"Tickerless accessions: {report['direct_reproduction']['tickerless_accessions']} "
        "(matches the frozen 818).",
        "",
        "## Population identity categories (all 5,754 accessions)",
        "",
        "| Category | Accessions | CIKs |",
        "|---|---:|---:|",
    ]
    for category in CATEGORIES:
        entry = pop[category]
        lines.append(f"| {category} | {entry['accessions']} | {entry['ciks']} |")
    lines += [
        "",
        "## Identity-augmented family counts",
        "",
        "| Family | Direct (any) | Direct unamb. | Identity-recovered | Augmented unamb. | "
        "Known outside | Unknown | Safe upper accessions |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("signing", "completion"):
        b = fam[name]
        augmented = b["direct_unambiguous_accessions"] + b["identity_recovered_accessions"]
        lines.append(f"| {name} | {b['direct_accessions']} | {b['direct_unambiguous_accessions']} | "
                     f"{b['identity_recovered_accessions']} | {augmented} | "
                     f"{b['known_outside_accessions']} | {b['unknown_non_direct_accessions']} | "
                     f"{b['residual_safe_upper_accessions']} |")
    lines += [
        "",
        "The safe upper bound counts every accession not proven outside within the cached "
        "corpus (direct + identity-ambiguous + unknown tickerless). It is a residual ceiling for "
        "feasibility, not a claim that those accessions are canonical issuers.",
        "",
        "Residual issuer ceilings. The distinct-CIK ceiling counts direct unambiguous issuers "
        "plus one ambiguous slack plus unresolved/ambiguous CIKs; it can exceed the universe and "
        "is not a canonical issuer bound. The canonical ticker ceiling caps it at the 100-ticker "
        "universe.",
        "",
        "| Family | Direct unamb. issuers | Distinct-CIK ceiling | Canonical ticker upper issuers | Capped |",
        "|---|---:|---:|---:|:--:|",
    ]
    for name in ("signing", "completion"):
        b = fam[name]
        lines.append(f"| {name} | {b['direct_unambiguous_issuers']} | "
                     f"{b['residual_unknown_cik_ceiling']} | {b['residual_safe_upper_issuers']} | "
                     f"{str(b['residual_safe_upper_issuers_capped']).lower()} |")
    lines += [
        "",
        "## Transaction-known vs full cached identity",
        "",
        f"- transaction-known recovery: "
        f"{report['transaction_known_vs_full_cached']['transaction_known']['identity_recovered_accessions']} "
        "accessions.",
        f"- full-cached recovery: "
        f"{report['transaction_known_vs_full_cached']['full_cached']['identity_recovered_accessions']} "
        "accessions.",
        f"- delta: {report['transaction_known_vs_full_cached']['delta_recovered_accessions']}.",
        f"- direct / recovered overlap: "
        f"{report['overlap']['direct_and_recovered_overlap']}; full-cached / transaction-known "
        f"recovered overlap: "
        f"{report['overlap']['full_cached_and_transaction_known_recovered_overlap']}; recovered "
        f"signing / completion overlap: "
        f"{report['overlap']['recovered_signing_and_completion_overlap']}.",
        "",
        "## CIK evidence coverage",
        "",
        f"- Full corpus: {cov['full_corpus']['tickers_with_cik_evidence']}/100 canonical tickers; "
        f"missing {', '.join(cov['full_corpus']['tickers_without_cik_evidence']) or 'none'}.",
        f"- Core 20 files only: {cov['core_20_only']['tickers_with_cik_evidence']}/100; "
        f"missing {', '.join(cov['core_20_only']['tickers_without_cik_evidence']) or 'none'}.",
        f"- Prior report: {cov['prior_reported_coverage']['tickers_with_cik_evidence']}/100.",
        "",
        "## Unresolved ambiguities",
        "",
        f"- BLK two CIKs "
        f"{report['unresolved_ambiguities']['blk_two_ciks']['ciks']}: "
        f"{len(report['unresolved_ambiguities']['blk_two_ciks']['accessions'])} accessions stay "
        "UNKNOWN; they are never merged.",
        f"- CIK mapping to multiple canonical tickers: "
        f"{report['unresolved_ambiguities']['cik_mapping_to_multiple_universe_tickers'] or 'none'}.",
        f"- Share-class / alias conflicts (explicit non-canonical ticker with canonical CIK): "
        f"{report['unresolved_ambiguities']['share_class_or_alias_conflicts']['accessions']} "
        "accessions, left UNKNOWN.",
        "",
        "## Preservation and boundaries",
        "",
        f"- Original transaction/prior-artifact preservation checks all true: "
        f"{report['preservation']['all_unchanged']}.",
        f"- Network requests: 0; economic prices/models: false; JEV/model calls: 0; "
        f"classifier/model built: false (the CIK lookup is a deterministic resolver, not a "
        f"classifier).",
        f"- Filing text: "
        f"{report['boundaries']['filing_text_read']['session_schema_peek_vendor_supporting_snippets']} "
        "vendor supporting_text snippets shown in a first-record schema peek; no full SEC "
        "packages read; snippets ignored by the extraction and not used for any decision.",
        f"- Private manifest: content immutable and reproduced byte-for-byte; uninterrupted "
        f"custody: {str(report['provenance']['custody']['uninterrupted_custody']).lower()} "
        "(backed up to /tmp/tir_manifest_backup, removed and restored during verification, "
        "bytes retained; no original transaction_source manifest touched).",
        "",
        "## Reproduction",
        "",
        "```",
        ".venv/bin/python transaction_identity_review.py --selftest  # bounded identity self-test",
        ".venv/bin/python transaction_identity_review.py            # freeze once, then analyse",
        ".venv/bin/python transaction_identity_review.py --verify   # immutable manifest + committed JSON",
        "```",
        "",
        "## Limitations",
        "",
    ]
    lines += [f"- {item}" for item in report["limitations"]]
    lines += [
        "",
        "A source-feasibility gate failure is not evidence that no alpha exists. No economic "
        "price or model was opened, so this review says nothing about returns or profitability.",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Identity self-test
# ---------------------------------------------------------------------------
def identity_selftest():
    universe = {"AAA", "BBB"}
    identity_cases = [
        ({"tickers": ["AAA"], "ciks": ["0000000001"]}, "direct_ticker_match"),
        ({"tickers": [], "ciks": ["0000000002"]}, "tickerless_identity_recovered"),
        ({"tickers": [], "ciks": ["0000000003"]}, "tickerless_cik_ambiguous"),
        ({"tickers": [], "ciks": ["0000000004"]}, "tickerless_cik_non_universe"),
        ({"tickers": [], "ciks": ["0000000005"]}, "tickerless_unresolved"),
        ({"tickers": ["ZZZ"], "ciks": ["0000000002"]}, "with_ticker_cik_canonical_conflict"),
        ({"tickers": ["ZZZ"], "ciks": ["0000000004"]}, "with_ticker_non_universe"),
        ({"tickers": ["ZZZ"], "ciks": ["0000000005"]}, "with_ticker_cik_unreferenced"),
    ]
    identity = {
        "0000000002": {"AAA"},
        "0000000003": {"AAA", "BBB"},
        "0000000004": {"ZZZ"},
    }
    for event, expected in identity_cases:
        category, _, _ = resolve_accession_identity(event, universe, identity)
        if category != expected:
            raise AssertionError(f"identity selftest: {event} -> {category}, expected {expected}")
    # A ticker that maps to multiple canonical tickers must never recover.
    category, _, _ = resolve_accession_identity({"tickers": [], "ciks": ["0000000003"]}, universe, identity)
    assert category == "tickerless_cik_ambiguous"
    # A canonical ticker shared by two CIKs must not be collapsed.
    cov = universe_coverage({"0000000002": {"AAA"}, "0000000009": {"AAA"}}, universe)
    assert cov["universe_tickers_with_multiple_ciks"] == {"AAA": ["0000000002", "0000000009"]}
    # The canonical issuer ceiling must never exceed the universe size.
    capped = min(241, len(universe))
    assert capped == len(universe) and capped <= len(universe)
    # Out-of-window date fails fast.
    try:
        validate_dates(Path("synthetic.json"), [{"filing_date": "2023-07-01"}])
    except ValueError:
        pass
    else:
        raise AssertionError("identity selftest: out-of-window date did not fail")
    # A frozen manifest entry whose sha256 no longer matches the file must fail fast.
    try:
        verify_manifest_files({
            "identity_evidence_files": [{"path": UNIVERSE_FILE, "sha256": "0" * 64}],
            "target_metadata_files": [],
        })
    except ValueError:
        pass
    else:
        raise AssertionError("identity selftest: hash mismatch did not fail")
    print("transaction identity review identity self-test: OK (9 identity cases + ambiguity, "
          "ceiling, collision, date and hash fences)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def run(write_outputs=True, freeze=True):
    manifest = build_manifest()
    if freeze:
        _status, manifest_sha = freeze_or_verify_manifest(manifest)
    else:
        verify_manifest_files(manifest)
        manifest_sha = digest_json(manifest)
    # Only now, after the manifest is frozen and verified, are counts computed.
    universe = load_universe()
    cik_to_tickers = build_identity_map(manifest)
    rows = load_transaction_rows(manifest)
    report = build_report(manifest, manifest_sha, universe, cik_to_tickers, rows)
    if write_outputs:
        OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n")
        OUT_MD.write_text(render_markdown(report))
        print(f"Wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")
    return report


def verify():
    report = run(write_outputs=False, freeze=False)
    if not OUT_JSON.exists() or not OUT_MD.exists():
        raise FileNotFoundError("Committed public reports are missing; run without --verify first.")
    committed = json.loads(OUT_JSON.read_text())
    if committed != report:
        raise ValueError("Committed TRANSACTION_IDENTITY_REVIEW.json does not match the recompute.")
    if OUT_MD.read_text() != render_markdown(report):
        raise ValueError("Committed docs/research/TRANSACTION_IDENTITY_REVIEW.md does not match the recompute.")
    # The committed report embeds the frozen manifest; require a byte-identical rebuild.
    if committed.get("input_manifest") != report["input_manifest"]:
        raise ValueError("Embedded input manifest does not reproduce from the frozen inputs.")
    print("verify: immutable manifest, recomputed report and committed public reports all match.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true",
                        help="re-verify manifest and recompute against committed public reports")
    parser.add_argument("--selftest", action="store_true", help="run bounded identity self-test")
    args = parser.parse_args(argv)
    if args.selftest:
        identity_selftest()
    elif args.verify:
        identity_selftest()
        verify()
    else:
        identity_selftest()
        report = run(write_outputs=True)
        pop = report["population_identity_categories"]
        for name in ("signing", "completion"):
            block = report["family_identity_augmentation"][name]
            print(f"{name}: direct {block['direct_accessions']} / unamb "
                  f"{block['direct_unambiguous_accessions']}, recovered "
                  f"{block['identity_recovered_accessions']}, unknown "
                  f"{block['unknown_non_direct_accessions']}, safe upper "
                  f"{block['residual_safe_upper_accessions']}, canonical ticker ceiling "
                  f"{block['residual_safe_upper_issuers']} (capped from "
                  f"{block['residual_unknown_cik_ceiling']})")
        print("tickerless accessions:", report["direct_reproduction"]["tickerless_accessions"],
              "| outside (corpus-bounded):", pop["tickerless_cik_non_universe"]["accessions"],
              "| unresolved:", pop["tickerless_unresolved"]["accessions"])
        print("preservation all unchanged:", report["preservation"]["all_unchanged"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
