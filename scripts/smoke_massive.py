#!/usr/bin/env python3
"""Bounded endpoint/configuration QA; never price a trade or print API payloads."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from submission_pipeline import SubmissionBlocked, _key, _load_original, validate_dates, verify_pinned_sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', required=True)
    parser.add_argument('--end', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if root != Path.cwd().resolve():
        parser.error('Run from the repository root')
    first, last = validate_dates(args.start, args.end)
    if (last-first).days > 1:
        parser.error('Smoke check accepts at most two inclusive event dates')
    verify_pinned_sources(root)
    try:
        key = _key(root)
    except SubmissionBlocked:
        print('WARNING: NOT_RUN_NO_KEY; source/date checks passed; zero API requests')
        return 0
    pipeline = _load_original(root, args.start, args.end, key)
    checks = (
        ('disclosures', '/stocks/filings/8-K/vX/disclosures',
         {'filing_date.gte': args.start, 'filing_date.lte': args.end, 'limit': 1}),
        ('options_reference', '/v3/reference/options/contracts',
         {'underlying_ticker': 'AAPL', 'as_of': args.start, 'limit': 1}),
    )
    passed = True
    for label, endpoint, params in checks:
        try:
            pipeline['api_get'](endpoint, params)
            print(f'PASS: {label} wrapper returned; raw payload retained only in ignored cache')
        except pipeline['requests'].exceptions.RequestException as exc:
            status = getattr(getattr(exc, 'response', None), 'status_code', None)
            print(f'WARNING: {label} access unverified; HTTP status={status}; details suppressed')
            passed = False
    print('No pricing endpoint, return calculation, OOS stage or sealed window evaluated.')
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
