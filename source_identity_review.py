#!/usr/bin/env python3
"""Independent source-identity review of the credit-facility and repurchase audits.

This script is read-only and offline. It makes no network request, reads no option
price, payoff, JEV output, 2026 filing, out-of-sample window or sealed judges data,
and builds no text classifier or semantic eligibility rule. It only resolves issuer
identity from CIK/ticker pairs that are already present in cached source inventories
and disclosure records, and it compares that identity evidence against the direct
ticker matching used by the two frozen source-feasibility audits.

Question: both frozen audits enrolled a disclosure row only when the row's `tickers`
intersected the canonical TOP_100 ticker list. A row whose `tickers` field is absent
(repurchase: 63 rows; credit facility: 1,419 rows) is therefore dropped even when its
CIK might belong to a canonical issuer. This script asks, using cached evidence only:

  * how many rows the audits enrolled by direct ticker match (reproduced),
  * how many additional rows are recoverable by CIK identity evidence,
  * how many remain unresolved because the CIK has no cached ticker evidence,
  * what population bounds and conflicts follow.

Unknowns stay unknown. A CIK is mapped to an economic issuer only when a cached
record explicitly pairs that CIK with a ticker. No company name is used.

Run:  .venv/bin/python source_identity_review.py
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "SOURCE_IDENTITY_REVIEW.json"

# Cached source inventories and disclosure records that explicitly pair a CIK with a
# ticker. These are local, git-ignored caches; the script fails loudly if one is
# missing. The first 17 entries are the narrow corpus (the two audits' own caches plus
# the earnings and guidance source inventories). The remaining 4 departure candidate
# inventories are the broad corpus.
#
# `novelty_results/source_filings.json` is EXCLUDED ENTIRELY. That cache is the
# notebook example's reserved-holdout window (2023-06-01..2023-08-31, the sealed
# judges interval) plus adjacent 2023 history, and 74 of its rows are reserved-date
# records. The first identity-review iteration read it before the reserved window was
# recognised; it is dropped here and never read again. See `EXPOSURE_LEDGER`.
NOVELTY_EXCLUDED = {
    "path": "novelty_results/source_filings.json",
    "reason": "reserved notebook example holdout window 2023-06-01..2023-08-31; "
              "74 reserved-date records; excluded entirely from the evidence corpus",
    "records": 1093,
    "reserved_june_august_2023_records": 74,
}
EVIDENCE_CORPUS = [
    "earnings_payoff_results/filing_inventory.json",
    "earnings_payoff_results/events.json",
    "full_source_results/candidate_packets.json",
    "guidance_results/enrollment.json",
    "guidance_results/disclosures_guidance_issuance_or_update.json",
    "guidance_results/disclosures_guidance_withdrawal.json",
    "expanded_guidance_results/enrollment.json",
    "expanded_guidance_results/disclosures_annual_earnings.json",
    "expanded_guidance_results/disclosures_guidance_issuance_or_update.json",
    "expanded_guidance_results/disclosures_guidance_withdrawal.json",
    "expanded_guidance_results/disclosures_preliminary_results.json",
    "expanded_guidance_results/disclosures_quarterly_earnings.json",
    "credit_facility_feasibility/disclosures.json",
    "credit_facility_feasibility/enrollment.json",
    "repurchase_results/disclosures.json",
    "repurchase_results/enrollment.json",
    "departure_results/candidate_ceo_departure.json",
    "departure_results/candidate_cfo_departure.json",
    "departure_results/candidate_executive_officer_departure.json",
    "departure_results/candidate_director_departure.json",
]
NARROW_CORPUS = EVIDENCE_CORPUS[:16]

# Fail-fast date fence for identity evidence. Identity pairs and disclosure rows are
# used only when every dated record lies inside the authorized 2024-2025 window.
# A record with a date outside this window is a hard error, never a silent drop.
AUTHORIZED_START, AUTHORIZED_END = "2024-01-01", "2025-12-31"

UNIVERSE_FILES = [
    "credit_facility_feasibility/universe.json",
    "repurchase_results/universe.json",
]

TAGS = {
    "share_repurchase_program": {
        "label": "repurchase",
        "disclosures": "repurchase_results/disclosures.json",
        "reported_direct": {"accessions": 36, "tickers": 26, "ciks": 26},
    },
    "credit_facility": {
        "label": "credit_facility",
        "disclosures": "credit_facility_feasibility/disclosures.json",
        "reported_direct": {"accessions": 62, "tickers": 38, "ciks": 39},
    },
}

# Documented provisional concerns in the frozen repurchase eligibility extraction.
# These are observations about recorded fields, not a re-parse: the extraction is
# reported as a provisional source count, not a validated signal.
PROVISIONAL_CONCERNS = [
    {
        "ticker": "GM",
        "accession_number": "0001467858-25-000063",
        "concern": "amount_attribution",
        "note": "Recorded authorization_dollars include $0.3B, but the span calls it "
                "'$0.3 billion of capacity was remaining under the Company's previously "
                "authorized program', not a new authorization.",
    },
    {
        "ticker": "AIG",
        "accession_number": "0000005272-25-000017",
        "concern": "amount_attribution",
        "note": "Recorded authorization_dollars include $3.4B, but the span calls it "
                "'approximately $3.4 billion remaining under the Board's prior share "
                "repurchase authorization'.",
    },
    {
        "ticker": "ISRG",
        "accession_number": "0001035267-25-000156",
        "concern": "amount_kind_attribution",
        "note": "amount_kind is 'incremental', but the span says the board 'increased the "
                "authorized amount ... to an aggregate of $4.0 billion, including amounts "
                "remaining under previous authorization'.",
    },
    {
        "ticker": "MO",
        "accession_number": "0001193125-24-071340",
        "concern": "asr_context",
        "note": "Driver span describes ASR transactions and an existing program 'expanded to "
                "$3.4 billion in connection with the Secondary Offering and the Share "
                "Repurchase'; this is an actual-repurchase context, not a clean standalone "
                "new authorization.",
    },
    {
        "ticker": "BAC",
        "accession_number": "0000070858-24-000194",
        "concern": "date_attribution",
        "note": "announcement_dates mixes the board date, the August 1, 2024 effective date, "
                "and a prior-program date; the recorded dates are not a single clean "
                "announcement date.",
    },
    {
        "ticker": "USB",
        "accession_number": "0001193125-24-217446",
        "concern": "date_attribution",
        "note": "announcement_dates includes December 22, 2020, a prior-authorization date, "
                "alongside the September 12, 2024 board date.",
    },
]

# Honest record of what this identity work touched. The first iteration read cached
# filing metadata that included the notebook's reserved-date holdout; that cache is
# dropped here, but the read already happened and the pristine holdout cannot be
# restored by this work. The financial-outcome replication (the only step that would
# actually open the reserved outcomes) has never been run.
EXPOSURE_LEDGER = {
    "first_iteration_read": {
        "file": "novelty_results/source_filings.json",
        "what_was_read": "previously cached filing metadata (cik, ticker, accession, "
                         "filing_date, items_text) only; no option price, no payoff, no "
                         "market/options data, no new source request",
        "reserved_window": "2023-06-01..2023-08-31 (notebook HOLDOUT_START..HOLDOUT_END)",
        "reserved_date_records_seen": 74,
        "total_records_seen": 1093,
        "first_iteration_status": "read; superseded by this corrected review",
    },
    "correction_applied_now": "novelty_results/source_filings.json is excluded entirely "
                              "from EVIDENCE_CORPUS and is not read again; all identity "
                              "pairs and disclosure rows must pass a 2024-2025 fail-fast "
                              "date check.",
    "cannot_restore": "A previously cached filing metadata file cannot be made pristine "
                      "again. This correction drops the file but does not restore a "
                      "pristine source-metadata holdout, and does not prove the reserved "
                      "window was cleanly untouched before this identity work.",
    "no_new_source_request": "No option, payoff or new source request was made during this "
                             "identity interval; only local cached metadata was read.",
    "financial_outcome_replication": "unrun. The actual judge-selected reserved window is "
                                     "unknown (judges change HOLDOUT_START..HOLDOUT_END), and "
                                     "no outcome or payoff was read by this review.",
    "claim_boundary": "This review does not claim the sealed data was entirely untouched.",
}


def normalize_ticker(value):
    """Same normalization used by the frozen audits: case/whitespace and '/' -> '.'."""
    if not isinstance(value, str):
        return None
    return value.strip().upper().replace("/", ".")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_dates(path, records):
    """Fail fast if any dated record lies outside the authorized 2024-2025 window.

    Returns a summary. A record with no parseable date is counted as undated and does
    not fail the check; a record with a date outside 2024-2025 raises immediately so a
    reserved-window or otherwise out-of-scope row can never silently enter a pair.
    """
    dated = 0
    undated = 0
    for record in records:
        if not isinstance(record, dict):
            undated += 1
            continue
        value = record.get("filing_date")
        if not isinstance(value, str) or not value:
            undated += 1
            continue
        if not (AUTHORIZED_START <= value <= AUTHORIZED_END):
            raise ValueError(
                f"Out-of-window date in {path.name}: {value!r} is outside "
                f"{AUTHORIZED_START}..{AUTHORIZED_END}; identity evidence is refused.")
        dated += 1
    return f"{dated} dated, {undated} undated; all dated records inside 2024-2025"


def load_universe():
    universes = []
    for relative in UNIVERSE_FILES:
        values = json.loads((ROOT / relative).read_text())
        universes.append((relative, values))
    first = universes[0][1]
    if len(first) != 100 or len(set(first)) != 100:
        raise ValueError("Canonical TOP_100 must be 100 distinct tickers.")
    for relative, values in universes:
        if values != first:
            raise ValueError(f"Universe mismatch: {relative}")
    return set(first), universes


def identity_pairs(path: Path):
    """Yield explicit (cik, ticker) pairs recorded in one cached file.

    Refuses any file whose dated records fall outside 2024-2025 before yielding a pair.
    """
    data = json.loads(path.read_text())
    records = data if isinstance(data, list) else []
    validate_dates(path, records)
    for record in records:
        if not isinstance(record, dict) or "cik" not in record:
            continue
        tickers = []
        if isinstance(record.get("tickers"), list):
            tickers.extend(t for t in record["tickers"] if isinstance(t, str))
        if isinstance(record.get("ticker"), str):
            tickers.append(record["ticker"])
        for ticker in tickers:
            normalized = normalize_ticker(ticker)
            if normalized:
                yield str(record["cik"]).zfill(10), normalized


def build_identity_map(files):
    cik_to_tickers = defaultdict(set)
    file_stats = []
    for relative in files:
        path = ROOT / relative
        if not path.exists():
            raise FileNotFoundError(f"Missing cached evidence source: {relative}")
        records = json.loads(path.read_text())
        if not isinstance(records, list):
            records = []
        date_check = validate_dates(path, records)
        pairs = list(identity_pairs(path))
        new_pairs = 0
        for cik, ticker in pairs:
            if ticker not in cik_to_tickers[cik]:
                new_pairs += 1
            cik_to_tickers[cik].add(ticker)
        file_stats.append({
            "path": relative,
            "sha256": sha256_file(path),
            "records": len({cik for cik, _ in pairs}),
            "pairs": len(pairs),
            "new_pairs": new_pairs,
            "date_check": date_check,
        })
    return cik_to_tickers, file_stats


def universe_coverage(cik_to_tickers, universe):
    ticker_to_ciks = defaultdict(set)
    for cik, tickers in cik_to_tickers.items():
        for ticker in tickers:
            ticker_to_ciks[ticker].add(cik)
    covered = sorted(t for t in universe if t in ticker_to_ciks)
    missing = sorted(universe - set(covered))
    multi_cik = {t: sorted(ticker_to_ciks[t]) for t in covered if len(ticker_to_ciks[t]) > 1}
    multi_universe = {}
    for cik, tickers in cik_to_tickers.items():
        hit = sorted(tickers & universe)
        if len(hit) > 1:
            multi_universe[cik] = hit
    return {
        "universe_tickers": len(universe),
        "tickers_with_cik_evidence": len(covered),
        "tickers_without_cik_evidence": missing,
        "universe_tickers_with_multiple_ciks": multi_cik,
        "ciks_mapping_to_multiple_universe_tickers": multi_universe,
    }


def classify_tag(rows, universe, cik_to_tickers):
    cik_has_universe = {c for c, ts in cik_to_tickers.items() if ts & universe}
    classes = defaultdict(lambda: {"rows": 0, "accessions": set(), "ciks": set()})
    for row in rows:
        accession = row.get("accession_number")
        cik = str(row["cik"]).zfill(10)
        raw_tickers = row.get("tickers")
        if raw_tickers:
            tickers = {normalize_ticker(t) for t in raw_tickers if isinstance(t, str)}
            tickers.discard(None)
            if tickers & universe:
                key = "direct_ticker_match"
            elif cik in cik_has_universe:
                key = "cik_recoverable"
            elif cik in cik_to_tickers:
                key = "with_ticker_non_universe"
            else:
                key = "with_ticker_cik_unreferenced"
        else:
            if cik in cik_has_universe:
                key = "cik_recoverable"
            elif cik in cik_to_tickers:
                key = "tickerless_cik_non_universe"
            else:
                key = "tickerless_unresolved"
        entry = classes[key]
        entry["rows"] += 1
        entry["accessions"].add(accession)
        entry["ciks"].add(cik)

    def summarize(key):
        entry = classes.get(key, {"rows": 0, "accessions": set(), "ciks": set()})
        return {
            "rows": entry["rows"],
            "accessions": len(entry["accessions"]),
            "ciks": len(entry["ciks"]),
        }

    # Direct-match detail and full population bounds.
    direct_tickers = sorted({normalize_ticker(t) for r in rows
                             if r.get("tickers") for t in r["tickers"]
                             if normalize_ticker(t) in universe})
    direct_accessions = classes["direct_ticker_match"]["accessions"]
    direct_ciks = sorted(classes["direct_ticker_match"]["ciks"])
    unresolved = classes.get("tickerless_unresolved", {"accessions": set()})
    unresolved_cik_counts = Counter()
    for row in rows:
        cik = str(row["cik"]).zfill(10)
        if not row.get("tickers") and cik not in cik_to_tickers:
            unresolved_cik_counts[cik] += 1
    # A universe issuer can carry more than one CIK (BLK is a cached example), so the
    # identity-only upper bound does not assume one CIK per issuer. The conditional
    # bound assumes the three universe tickers with no cached CIK evidence are the only
    # candidates and map one CIK each; it is reported as a sensitivity, not a fact.
    largest_three = sum(n for _, n in unresolved_cik_counts.most_common(3))
    return {
        "direct": {
            "accessions": len(direct_accessions),
            "tickers": len(direct_tickers),
            "ciks": len(direct_ciks),
            "ticker_list": direct_tickers,
        },
        "cik_recoverable": summarize("cik_recoverable"),
        "with_ticker_non_universe": summarize("with_ticker_non_universe"),
        "with_ticker_cik_unreferenced": summarize("with_ticker_cik_unreferenced"),
        "tickerless_cik_non_universe": summarize("tickerless_cik_non_universe"),
        "tickerless_unresolved": {
            **summarize("tickerless_unresolved"),
            "unresolved_cik_count": len(unresolved_cik_counts),
            "largest_cik_group_sizes": [n for _, n in unresolved_cik_counts.most_common(5)],
        },
        "population_bounds_accessions": {
            "confirmed_in_universe": len(direct_accessions),
            "identity_only_upper": len(direct_accessions) + len(unresolved["accessions"]),
            "conditional_upper_one_cik_per_uncovered_issuer":
                len(direct_accessions) + largest_three,
            "conditional_bound_is_definitive": False,
            "conditional_bound_note": "not definitive: a canonical ticker can carry more "
                                      "than one CIK (BLK already has two), so the one-CIK "
                                      "per missing-issuer assumption is unsupported",
        },
    }


def provisional_eligibility():
    """Counts recorded by the frozen repurchase audit, labelled provisional.

    Two different things are separated here and must not be conflated:
      * the raw source count (36 direct-ticker accessions, 2,108 tag rows) is a
        reproducible count of recorded rows;
      * the 12 standalone / 10 issuer figure is a provisional eligibility extraction
        from recorded fields, with known amount- and date-attribution problems.
    Neither is a validated signal.
    """
    path = ROOT / "repurchase_results/audits.json"
    raw_source = {
        "tag_rows": 2108,
        "direct_ticker_accessions": 36,
        "direct_ticker_issuers": 26,
        "direct_ticker_ciks": 26,
        "note": "reproducible raw source counts; not an eligibility or signal count",
    }
    if not path.exists():
        return {"status": "audit_records_unavailable", "raw_source_counts": raw_source}
    audits = json.loads(path.read_text())
    eligible = [a for a in audits if a.get("status") != "excluded"]
    standalone = [a for a in eligible if not a.get("item_2_02")]
    bundled = [a for a in eligible if a.get("item_2_02")]
    return {
        "status": "provisional_source_extraction_not_validated_signal",
        "raw_source_counts": raw_source,
        "provisional_extraction_rule": "recorded fields in repurchase_results/audits.json; not re-parsed here",
        "standalone_filings": len(standalone),
        "standalone_issuers": len({a["ticker"] for a in standalone}),
        "earnings_bundled_filings": len(bundled),
        "earnings_bundled_issuers": len({a["ticker"] for a in bundled}),
        "total_eligible_filings": len(eligible),
        "total_eligible_issuers": len({a["ticker"] for a in eligible}),
        "extraction_problem": "the 12/10 standalone figure depends on amount- and "
                              "date-attribution fields that the documented concerns below "
                              "show are not clean; it is a provisional extraction, not a "
                              "validated eligible-filing count",
        "documented_provisional_concerns": PROVISIONAL_CONCERNS,
    }


def main():
    universe, universe_files = load_universe()
    broad_map, broad_files = build_identity_map(EVIDENCE_CORPUS)
    narrow_map, _ = build_identity_map(NARROW_CORPUS)

    report = {
        "review": "source-identity-review",
        "kind": "offline, read-only source-identity review; no outcomes, options, JEV, "
                "2026, out-of-sample or sealed data; no text classifier",
        "canonical_universe": {
            "tickers": len(universe),
            "source_files": universe_files,
            "identical_across_audits": True,
        },
        "evidence_corpus": {
            "mode": "broad cached source inventory/disclosure corpus",
            "files": broad_files,
            "distinct_ciks": len(broad_map),
            "universe_coverage": universe_coverage(broad_map, universe),
            "date_validation": f"every dated record inside {AUTHORIZED_START}..{AUTHORIZED_END}; "
                               "out-of-window dates fail fast",
        },
        "excluded_corpus": NOVELTY_EXCLUDED,
        "exposure_ledger": EXPOSURE_LEDGER,
        "narrow_corpus_sensitivity": {
            "mode": "two audits' own caches plus earnings/guidance inventories",
            "universe_coverage": universe_coverage(narrow_map, universe),
        },
        "tags": {},
        "conflicts_and_claim_corrections": [],
        "provisional_repurchase_eligibility": provisional_eligibility(),
        "boundaries": {
            "network_requests": 0,
            "market_or_option_data_read": False,
            "jev_or_model_calls": 0,
            "text_classifier_or_semantic_rule_built": False,
            "frozen_audit_code_modified": False,
            "frozen_caches_modified": False,
            "commit_made": False,
        },
    }

    for tag, spec in TAGS.items():
        disclosure_path = ROOT / spec["disclosures"]
        rows = json.loads(disclosure_path.read_text())
        validate_dates(disclosure_path, rows)
        result = classify_tag(rows, universe, broad_map)
        result["disclosure_file"] = spec["disclosures"]
        result["disclosure_sha256"] = sha256_file(disclosure_path)
        result["disclosure_rows"] = len(rows)
        result["audit_reported_direct"] = spec["reported_direct"]
        result["direct_reproduced"] = (
            result["direct"]["accessions"] == spec["reported_direct"]["accessions"]
            and result["direct"]["tickers"] == spec["reported_direct"]["tickers"]
            and result["direct"]["ciks"] == spec["reported_direct"]["ciks"]
        )
        report["tags"][tag] = result
        if not result["direct_reproduced"]:
            report["conflicts_and_claim_corrections"].append(
                f"{tag}: reproduced direct counts differ from the frozen audit report.")
        if result["cik_recoverable"]["accessions"]:
            report["conflicts_and_claim_corrections"].append(
                f"{tag}: {result['cik_recoverable']['accessions']} additional accessions "
                "recovered by CIK identity evidence; the direct-ticker census is incomplete.")
        if result["tickerless_unresolved"]["accessions"]:
            report["conflicts_and_claim_corrections"].append(
                f"{tag}: {result['tickerless_unresolved']['accessions']} accessions are "
                "identity-unresolved (tickerless, CIK has no cached ticker evidence); the "
                "direct-ticker count is a lower bound, not a complete census.")
        bounds = result["population_bounds_accessions"]
        if bounds["identity_only_upper"] >= 80 and spec["reported_direct"]["accessions"] < 80:
            report["conflicts_and_claim_corrections"].append(
                f"{tag}: the 80-filing floor is not structurally impossible because the "
                f"identity-only population upper bound is {bounds['identity_only_upper']} "
                "(the tighter one-CIK-per-missing-issuer bound is not definitive; BLK "
                "already carries two CIKs).")

    coverage = report["evidence_corpus"]["universe_coverage"]
    if coverage["tickers_without_cik_evidence"]:
        report["conflicts_and_claim_corrections"].append(
            "cached CIK evidence does not cover these canonical tickers: "
            + ", ".join(coverage["tickers_without_cik_evidence"])
            + "; any tickerless row from those issuers stays unresolved.")
    if coverage["ciks_mapping_to_multiple_universe_tickers"]:
        report["conflicts_and_claim_corrections"].append(
            "a CIK maps to more than one canonical ticker: "
            + json.dumps(coverage["ciks_mapping_to_multiple_universe_tickers"]))
    if coverage["universe_tickers_with_multiple_ciks"]:
        report["conflicts_and_claim_corrections"].append(
            "a canonical ticker maps to more than one CIK: "
            + json.dumps(coverage["universe_tickers_with_multiple_ciks"]))

    OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    print("Excluded corpus:", NOVELTY_EXCLUDED["path"],
          f"({NOVELTY_EXCLUDED['reserved_june_august_2023_records']} reserved-date records)")
    print("Date validation:", report["evidence_corpus"]["date_validation"])
    print("Universe CIK evidence coverage:",
          f"{coverage['tickers_with_cik_evidence']}/{coverage['universe_tickers']}")
    print("Missing CIK evidence:", ", ".join(coverage["tickers_without_cik_evidence"]) or "none")
    for tag, result in report["tags"].items():
        print(f"\n{tag}  ({result['disclosure_rows']} disclosure rows)")
        print(f"  direct match          : {result['direct']['accessions']} accessions, "
              f"{result['direct']['tickers']} tickers, {result['direct']['ciks']} CIKs "
              f"(reproduced={result['direct_reproduced']})")
        print(f"  CIK recoverable       : {result['cik_recoverable']['accessions']} accessions")
        print(f"  with-ticker non-univ  : {result['with_ticker_non_universe']['accessions']} accessions")
        print(f"  tickerless, CIK known : {result['tickerless_cik_non_universe']['accessions']} accessions")
        print(f"  tickerless UNRESOLVED : {result['tickerless_unresolved']['accessions']} accessions, "
              f"{result['tickerless_unresolved']['unresolved_cik_count']} CIKs")
        print("  population bounds     :", result["population_bounds_accessions"])
    print("\nConflicts / claim corrections:")
    for line in report["conflicts_and_claim_corrections"]:
        print("  -", line)


if __name__ == "__main__":
    main()
