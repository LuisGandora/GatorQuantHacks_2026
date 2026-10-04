"""Credit-term measurement feasibility pilot: fixed 12 original 8-Ks.

Outcome-blind, source-only, numerical-source-term pilot. It reads only the
enrollment metadata produced by the historical coverage study and the original
SEC submission packages for 12 deterministically selected 8-Ks. It reads no
market price, option chain, payoff, JEV/model output, 2026 data or sealed judges
window, builds no classifier or regex eligibility screen, and freezes no trade
hypothesis.

Canonical fail-fast single path:

    .venv/bin/python credit_terms_pilot.py freeze     # protocol+selection, before any SEC read
    .venv/bin/python credit_terms_pilot.py retrieve   # original SEC packages, <=2 req/s
    .venv/bin/python credit_terms_pilot.py prepare    # structural package parse only
    .venv/bin/python credit_terms_pilot.py audit      # bind manually reviewed quotes/offsets
    .venv/bin/python credit_terms_pilot.py report
    .venv/bin/python credit_terms_pilot.py verify

Every stage re-verifies the frozen protocol, the frozen selection, the protected
prior research and the immutable cache before doing anything. Nothing is
silently repaired. The evidence table is authored by hand from the retrieved
packages; the code only locates the quoted spans and checks arithmetic.
"""
import argparse
import hashlib
import json
import re
import time
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import requests

from departure_experiment import freeze
from full_source_experiment import checksum, normalized_text, source_url
from jev_experiment import ROOT, digest

OUTPUT = ROOT / 'credit_terms_pilot'
CACHE = OUTPUT  # every private artifact, including the HTTP cache, stays here
ENROLLMENT = ROOT / 'historical_credit_coverage/enrollment.json'
ENROLLMENT_HASH = ROOT / 'historical_credit_coverage/enrollment_hash.json'
YEARS = ['2022', '2023', '2024', '2025']
PER_YEAR = 3
HOLDOUT = ('2023-06-01', '2023-08-31')
SEC_USER_AGENT = 'GatorQuantHacksResearch/CreditTermsPilot (numerical source-term measurement feasibility)'
UNITS = {'thousand': 1e3, 'million': 1e6, 'billion': 1e9}

PROTOCOL = {
    'experiment': 'credit-term source-evidence measurement feasibility pilot (fixed 12 original 8-Ks)',
    'version': 1,
    'research_kind': 'outcome-blind source-only numerical measurement feasibility pilot; no economic outcome, no trade hypothesis, no classifier, no semantic score, no model call',
    'window': ['2022-01-01', '2025-12-31'],
    'sealed_holdout': {'start': HOLDOUT[0], 'end': HOLDOUT[1],
                       'rule': '2023-06-01..2023-08-31 is never requested or read; no 2026-or-later source. The pilot reads only its 12 frozen accessions, all outside the holdout.'},
    'enrollment_source': 'historical_credit_coverage/enrollment.json (147 original 8-Ks, 54 issuers, 2022-2025, sealed 2023 holdout excluded)',
    'selection': {
        'per_year': PER_YEAR, 'years': YEARS,
        'key': 'SHA256(accession_number encoded UTF-8), hexdigest ascending',
        'tie_break': 'accession_number ascending',
        'skip_repeat_ticker': 'within a filing year, skip an accession whose economic ticker (its single normalized ticker) was already selected that year; the same ticker may recur in a different year',
        'order': 'select from frozen enrollment metadata only, and freeze the 12 accession numbers and their SHA256 ordering before any SEC package is read or requested',
    },
    'retrieval': {
        'endpoint': 'original SEC submission package URL recorded in enrollment filing_url, validated by the shared source_url utility',
        'rate': 'at most 2 SEC requests/second (>=0.5 s spacing); retries back off, and connection failure or a systemic HTTP 403 stops the pilot',
        'cache': 'original bytes plus a per-accession record with response headers, byte count and raw SHA256, under the ignored credit_terms_pilot/ directory',
        'fail_fast': 'a network connection failure or a systemic access denial raises; an unrequested package is never treated as missing evidence',
    },
    'evidence_fields': {
        'facility_id': 'explicit facility identifier/name stated in the source, with exact quote; one row per distinct facility or tranche, never merged',
        'old_maturity': 'explicitly stated prior/old maturity date, with exact quote; null if not stated',
        'new_maturity': 'explicitly stated new/current maturity date, with exact quote; null if not stated',
        'old_capacity': 'explicitly stated prior/old commitment amount with unit, currency and exact quote; null if not stated',
        'new_capacity': 'explicitly stated new/current commitment amount with unit, currency and exact quote; null if not stated',
        'currency': 'explicit currency token stated in the source, with exact quote; null if not stated',
        'effective_or_announcement_date': 'explicitly stated effective or announcement date, with exact quote; null if not stated',
        'linkage': 'explicit source text tying an old and a new value to the same facility; required before any numeric date difference is computed',
    },
    'missing': 'null means the source does not explicitly state the term; missing is never recorded as zero and is never reconstructed from outside sources or from another facility',
    'amounts': 'an amount is recorded only when the quote carries an explicit thousands/millions/billions word and an explicit currency token; the number/unit/currency are re-checked against the frozen quote',
    'dates': 'a maturity change is computed only for an explicitly linked same-facility old/new pair, as new-minus-old in whole days; arithmetic is transparent and no date is inferred',
    'item_2_02': 'recorded only as the literal presence of an Item 2.02 heading in the original sequence-1 8-K document; a header fact, not inferred and not a qualitative label',
    'no_estimates': 'no model estimate, no inferred date/amount, no reconstructed prior terms, no unit scaling beyond an explicit word',
    'facility_separation': 'distinct facilities and loan tranches are retained as separate factual rows; old and new terms from different facilities are never combined',
    'validation': 'every recorded quote must occur exactly once in the named parsed document; offsets are recomputed from whitespace-normalized text; every amount/unit/currency and every date text is re-checked against its quote',
    'preservation': 'the historical coverage protocol hash and all six hashes recorded in EARNINGS_PAYOFF_FREEZE.json are recomputed on every verify; prior frozen experiments are never modified',
    'priors_untouched': 'the older unrelated novelty cache that exposed 74 reserved 2023 dates is NOT read by this pilot; the financial replication is unrun and the actual judges window is unknown',
    'forbidden': ['options or any market prices', 'option chains and bars', 'historical payoffs', 'JEV or other model calls',
                  'text classifier, semantic score or qualitative event label', 'regex eligibility classifier',
                  '2026 or later filing or financial data', 'sealed 2023 holdout request or read', 'the .novelty_cache reserved 2023 metadata',
                  'edits to prior frozen experiments', 'trade hypothesis freeze', 'best-strategy selection', 'commit'],
}

# ---------------------------------------------------------------------------
# Manually reviewed source evidence.
#
# Authored by hand from the 12 frozen original SEC packages after retrieval. Each
# fact carries the exact parsed document filename and a whitespace-normalized
# quote. The audit stage locates each quote, records start/end offsets, and
# re-checks every amount, unit, currency and date text. Missing terms are null.
# A facility row is added only from explicit source text; facilities are never
# merged. `linkage` is present only when the source explicitly ties the old and
# new values to the same record.
#
# Reviewer notes. (1) Most 8-Ks announce a new or replacement facility and state
# only the new maturity/capacity; the prior term is not in the package, so it is
# recorded as null rather than reconstructed from another filing. (2) Only PM
# (2024) states both the old and the new maturity of one facility. (3) HON (2025)
# states an old $1.5 billion facility and a new $3.0 billion facility, but the
# 8-K does not state they are the same facility, so no capacity pair is claimed.
# (4) CAT (2022) addenda and TMUS/BKNG sub-limits are separate rows and are not
# summed into the parent commitment. The CAT addenda are USD-equivalent ceilings,
# not the borrowing currency; both years now carry a separate `borrowing_currency`
# annotation and a `currency_note`. (5) The `$` symbol is recorded as currency
# USD with the symbol quoted; AMD's ZT and receivables amounts are explicit raw
# dollars with no thousands/millions/billions scaling word, so under the frozen
# `amounts` clause their numeric capacity is null and the raw figure is retained
# only as an off-protocol provenance note (closed audit deviation DEV-1). (6) ADBE
# and LOW state a relative maturity
# ("two years following the initial funding date", "third anniversary of the
# signing date"); the date text is quoted but the date value stays null because
# no explicit calendar date is written.
SOURCE_EVIDENCE = {
    '0001193125-22-062961': {'facilities': [
        {'id': {'document': 'd296015d8k.htm', 'text': 'Amended and Restated Term Loan Credit Agreement',
                'quote': 'Amended and Restated Term Loan Credit Agreement (the “Term Loan”)'},
         'old_maturity': None,
         'new_maturity': {'document': 'd296015d8k.htm', 'text': 'December 31, 2022',
                          'quote': 'due and payable on December 31, 2022', 'value': '2022-12-31'},
         'old_capacity': None,
         'new_capacity': {'document': 'd296015d8k.htm', 'text': '$7.35 billion', 'quote': '$7.35 billion',
                          'value': 7.35, 'unit': 'billion', 'currency': 'USD'},
         'currency': {'document': 'd296015d8k.htm', 'text': '$', 'quote': '$7.35 billion', 'value': 'USD'},
         'effective_date': {'document': 'd296015d8k.htm', 'text': 'March 2, 2022',
                            'quote': 'On March 2, 2022, AT&T Inc.', 'value': '2022-03-02'},
         'linkage': None, 'note': 'Refinances a January 29, 2021 term loan; prior maturity not stated.'}]},
    '0001193125-22-263732': {'facilities': [
        {'id': {'document': 'd396252d8k.htm', 'text': 'Amended and Restated Credit Agreement',
                'quote': 'Amended and Restated Credit Agreement (the “Credit Agreement”)'},
         'old_maturity': None,
         'new_maturity': {'document': 'd396252d8k.htm', 'text': 'October 17, 2027',
                          'quote': 'Commitments under the Credit Agreement will mature on October 17, 2027',
                          'value': '2027-10-17'},
         'old_capacity': None,
         'new_capacity': {'document': 'd396252d8k.htm', 'text': '$7.5 billion',
                          'quote': '$7.5 billion revolving credit facility', 'value': 7.5, 'unit': 'billion',
                          'currency': 'USD'},
         'currency': {'document': 'd396252d8k.htm', 'text': '$', 'quote': '$7.5 billion revolving credit facility',
                      'value': 'USD'},
         'effective_date': {'document': 'd396252d8k.htm', 'text': 'October 17, 2022',
                            'quote': 'On October 17, 2022, T-Mobile USA, Inc.', 'value': '2022-10-17'},
         'linkage': None, 'note': 'Amends a 2020 credit agreement; prior maturity not stated.'},
        {'id': {'document': 'd396252d8k.htm', 'text': 'letter of credit sub-facility',
                'quote': 'letter of credit sub-facility of up to $1.5 billion'},
         'old_maturity': None, 'new_maturity': None, 'old_capacity': None,
         'new_capacity': {'document': 'd396252d8k.htm', 'text': '$1.5 billion',
                          'quote': 'letter of credit sub-facility of up to $1.5 billion', 'value': 1.5,
                          'unit': 'billion', 'currency': 'USD'},
         'currency': {'document': 'd396252d8k.htm', 'text': '$',
                      'quote': 'letter of credit sub-facility of up to $1.5 billion', 'value': 'USD'},
         'effective_date': None, 'linkage': None, 'note': 'Sub-limit within the revolver, kept separate.'},
        {'id': {'document': 'd396252d8k.htm', 'text': 'swingline loan sub-facility',
                'quote': 'swingline loan sub-facility of up to $500 million'},
         'old_maturity': None, 'new_maturity': None, 'old_capacity': None,
         'new_capacity': {'document': 'd396252d8k.htm', 'text': '$500 million',
                          'quote': 'swingline loan sub-facility of up to $500 million', 'value': 500,
                          'unit': 'million', 'currency': 'USD'},
         'currency': {'document': 'd396252d8k.htm', 'text': '$',
                      'quote': 'swingline loan sub-facility of up to $500 million', 'value': 'USD'},
         'effective_date': None, 'linkage': None, 'note': 'Sub-limit within the revolver, kept separate.'}]},
    '0000018230-22-000199': {'facilities': [
        {'id': {'document': 'cat-20220906.htm', 'text': '364-Day Facility',
                'quote': 'Credit Agreement (the “364-Day Facility”)'},
         'old_maturity': None,
         'new_maturity': {'document': 'cat-20220906.htm', 'text': 'August 31, 2023',
                          'quote': 'that expires on August 31, 2023', 'value': '2023-08-31'},
         'old_capacity': None,
         'new_capacity': {'document': 'cat-20220906.htm', 'text': '$3.15 billion',
                          'quote': 'aggregate amount of up to $3.15 billion', 'value': 3.15, 'unit': 'billion',
                          'currency': 'USD'},
         'currency': {'document': 'cat-20220906.htm', 'text': '$',
                      'quote': 'aggregate amount of up to $3.15 billion', 'value': 'USD'},
         'effective_date': {'document': 'cat-20220906.htm', 'text': 'September 1, 2022',
                            'quote': 'On September 1, 2022, Caterpillar Inc.', 'value': '2022-09-01'},
         'linkage': None, 'note': 'Replaces a prior 364-day facility entered September 2, 2021; prior maturity not stated.'},
        {'id': {'document': 'cat-20220906.htm', 'text': 'Local Currency Addendum',
                'quote': 'Local Currency Addendum that enables CIF to borrow in certain approved currencies including Pounds Sterling and Euros in an aggregate amount up to the equivalent of $100 million'},
         'old_maturity': None, 'new_maturity': None, 'old_capacity': None,
         'new_capacity': {'document': 'cat-20220906.htm', 'text': '$100 million',
                          'quote': 'including Pounds Sterling and Euros in an aggregate amount up to the equivalent of $100 million',
                          'value': 100, 'unit': 'million', 'currency': 'USD'},
         'currency': {'document': 'cat-20220906.htm', 'text': '$',
                      'quote': 'including Pounds Sterling and Euros in an aggregate amount up to the equivalent of $100 million',
                      'value': 'USD'},
         'borrowing_currency': 'Pounds Sterling and Euros (approved local currencies)',
         'currency_note': 'USD $100 million is the stated USD-equivalent ceiling of this addendum sub-limit, not the currency borrowed; borrowings are in approved local currencies including Pounds Sterling and Euros. Kept separate from, and never summed into, the $3.15 billion 364-Day Aggregate Commitment.',
         'effective_date': None, 'linkage': None,
         'note': 'Addendum within the 364-Day Aggregate Commitment, kept separate and not summed in.'},
        {'id': {'document': 'cat-20220906.htm', 'text': 'Japan Local Currency Addendum',
                'quote': 'Japan Local Currency Addendum that enables CFKK to borrow Japanese Yen in an aggregate amount up to the equivalent of $100 million'},
         'old_maturity': None, 'new_maturity': None, 'old_capacity': None,
         'new_capacity': {'document': 'cat-20220906.htm', 'text': '$100 million',
                          'quote': 'Japanese Yen in an aggregate amount up to the equivalent of $100 million',
                          'value': 100, 'unit': 'million', 'currency': 'USD'},
         'currency': {'document': 'cat-20220906.htm', 'text': '$',
                      'quote': 'Japanese Yen in an aggregate amount up to the equivalent of $100 million',
                      'value': 'USD'},
         'borrowing_currency': 'Japanese Yen',
         'currency_note': 'USD $100 million is the stated USD-equivalent ceiling of this addendum sub-limit, not the currency borrowed; borrowings are in Japanese Yen. Kept separate from, and never summed into, the $3.15 billion 364-Day Aggregate Commitment.',
         'effective_date': None, 'linkage': None,
         'note': 'Addendum within the 364-Day Aggregate Commitment, kept separate and not summed in.'},
        {'id': {'document': 'cat-20220906.htm', 'text': 'Three-Year Facility',
                'quote': 'extends the expiration date of the 2019 Three-Year Facility to August 29, 2025'},
         'old_maturity': None,
         'new_maturity': {'document': 'cat-20220906.htm', 'text': 'August 29, 2025',
                          'quote': 'extends the expiration date of the 2019 Three-Year Facility to August 29, 2025',
                          'value': '2025-08-29'},
         'old_capacity': None, 'new_capacity': None, 'currency': None,
         'effective_date': {'document': 'cat-20220906.htm', 'text': 'September 1, 2022',
                            'quote': 'On September 1, 2022, Caterpillar Inc.', 'value': '2022-09-01'},
         'linkage': None, 'note': 'Extension states only the new expiration date; prior maturity and capacity not stated.'},
        {'id': {'document': 'cat-20220906.htm', 'text': 'Five-Year Facility',
                'quote': 'extends the expiration date of the 2019 Five-Year Facility to September 1, 2027'},
         'old_maturity': None,
         'new_maturity': {'document': 'cat-20220906.htm', 'text': 'September 1, 2027',
                          'quote': 'extends the expiration date of the 2019 Five-Year Facility to September 1, 2027',
                          'value': '2027-09-01'},
         'old_capacity': None, 'new_capacity': None, 'currency': None,
         'effective_date': {'document': 'cat-20220906.htm', 'text': 'September 1, 2022',
                            'quote': 'On September 1, 2022, Caterpillar Inc.', 'value': '2022-09-01'},
         'linkage': None, 'note': 'Extension states only the new expiration date; prior maturity and capacity not stated.'}]},
    '0001075531-23-000033': {'facilities': [
        {'id': {'document': 'bkng-20230517.htm', 'text': 'Credit Agreement',
                'quote': 'a credit agreement (the "Credit Agreement")'},
         'old_maturity': None,
         'new_maturity': {'document': 'bkng-20230517.htm', 'text': 'May 17, 2028',
                          'quote': 'and any and all borrowings are due on May 17, 2028', 'value': '2028-05-17'},
         'old_capacity': None,
         'new_capacity': {'document': 'bkng-20230517.htm', 'text': '$2 billion',
                          'quote': 'extend a revolving line of credit up to $2 billion', 'value': 2.0,
                          'unit': 'billion', 'currency': 'USD'},
         'currency': {'document': 'bkng-20230517.htm', 'text': '$',
                      'quote': 'extend a revolving line of credit up to $2 billion', 'value': 'USD'},
         'effective_date': {'document': 'bkng-20230517.htm', 'text': 'May 17, 2023',
                            'quote': 'On May 17, 2023, Booking Holdings Inc. (the "Company") entered into',
                            'value': '2023-05-17'},
         'linkage': None, 'note': 'New agreement; the prior 2019 agreement is a separate terminated row.'},
        {'id': {'document': 'bkng-20230517.htm', 'text': 'letters of credit',
                'quote': 'up to $80 million of letters of credit'},
         'old_maturity': None, 'new_maturity': None, 'old_capacity': None,
         'new_capacity': {'document': 'bkng-20230517.htm', 'text': '$80 million',
                          'quote': 'up to $80 million of letters of credit', 'value': 80, 'unit': 'million',
                          'currency': 'USD'},
         'currency': {'document': 'bkng-20230517.htm', 'text': '$', 'quote': 'up to $80 million of letters of credit',
                      'value': 'USD'},
         'effective_date': None, 'linkage': None, 'note': 'Sub-limit within the revolver, kept separate.'},
        {'id': {'document': 'bkng-20230517.htm', 'text': 'swingline loans',
                'quote': 'up to $100 million of borrowings on same-day notice, referred to as swingline loans'},
         'old_maturity': None, 'new_maturity': None, 'old_capacity': None,
         'new_capacity': {'document': 'bkng-20230517.htm', 'text': '$100 million',
                          'quote': 'up to $100 million of borrowings on same-day notice, referred to as swingline loans',
                          'value': 100, 'unit': 'million', 'currency': 'USD'},
         'currency': {'document': 'bkng-20230517.htm', 'text': '$',
                      'quote': 'up to $100 million of borrowings on same-day notice, referred to as swingline loans',
                      'value': 'USD'},
         'effective_date': None, 'linkage': None, 'note': 'Sub-limit within the revolver, kept separate.'},
        {'id': {'document': 'bkng-20230517.htm', 'text': 'credit agreement, dated as of August 14, 2019',
                'quote': 'voluntarily terminated the $2 billion credit agreement, dated as of August 14, 2019'},
         'old_maturity': None, 'new_maturity': None,
         'old_capacity': {'document': 'bkng-20230517.htm', 'text': '$2 billion',
                          'quote': 'voluntarily terminated the $2 billion credit agreement, dated as of August 14, 2019',
                          'value': 2.0, 'unit': 'billion', 'currency': 'USD'},
         'new_capacity': None,
         'currency': {'document': 'bkng-20230517.htm', 'text': '$',
                      'quote': 'voluntarily terminated the $2 billion credit agreement, dated as of August 14, 2019',
                      'value': 'USD'},
         'effective_date': None, 'linkage': None,
         'note': 'Terminated prior facility. The filing does not state old and new capacity as the same facility, so no pair.'}]},
    '0001193125-23-010953': {'facilities': [
        {'id': {'document': 'd400939d8k.htm', 'text': 'Term Loan Credit Agreement',
                'quote': 'delayed draw term loan credit agreement (the “Term Loan Credit Agreement”)'},
         'old_maturity': None,
         'new_maturity': {'document': 'd400939d8k.htm', 'text': 'two years following the initial funding date',
                          'quote': 'The Term Loan will mature two years following the initial funding date',
                          'value': None},
         'old_capacity': None,
         'new_capacity': {'document': 'd400939d8k.htm', 'text': '$3.5 billion',
                          'quote': 'providing for an up to $3.5 billion senior unsecured term loan', 'value': 3.5,
                          'unit': 'billion', 'currency': 'USD'},
         'currency': {'document': 'd400939d8k.htm', 'text': '$',
                      'quote': 'providing for an up to $3.5 billion senior unsecured term loan', 'value': 'USD'},
         'effective_date': {'document': 'd400939d8k.htm', 'text': 'January 19, 2023',
                            'quote': 'On January 19, 2023, Adobe Inc. (the “Company”) entered into',
                            'value': '2023-01-19'},
         'linkage': None, 'note': 'Relative maturity text quoted; no explicit calendar date, so value is null.'}]},
    '0001193125-23-250325': {'facilities': [
        {'id': {'document': 'd468612d8k.htm', 'text': '364-Day Revolving Credit Agreement',
                'quote': '364-Day Revolving Credit Agreement with JPMorgan Chase Bank, N.A., as administrative agent, and the other lenders named therein (the “Facility”)'},
         'old_maturity': None,
         'new_maturity': {'document': 'd468612d8k.htm', 'text': 'October 1, 2024',
                          'quote': 'and matures on October 1, 2024', 'value': '2024-10-01'},
         'old_capacity': None,
         'new_capacity': {'document': 'd468612d8k.htm', 'text': '$6.0 billion',
                          'quote': 'provides available borrowing capacity of $6.0 billion', 'value': 6.0,
                          'unit': 'billion', 'currency': 'USD'},
         'currency': {'document': 'd468612d8k.htm', 'text': '$',
                      'quote': 'provides available borrowing capacity of $6.0 billion', 'value': 'USD'},
         'effective_date': {'document': 'd468612d8k.htm', 'text': 'October 3, 2023',
                            'quote': 'On October 3, 2023, General Motors Company (“GM”) entered into',
                            'value': '2023-10-03'},
         'linkage': None, 'note': 'New facility; prior term not stated.'}]},
    '0001104659-24-006244': {'facilities': [
        {'id': {'document': 'tm243707d1_8k.htm', 'text': '364-day revolving credit facility',
                'quote': 'existing 364-day revolving credit facility, dated as of February 12, 2013'},
         'old_maturity': {'document': 'tm243707d1_8k.htm', 'text': 'January 30,\n2024',
                          'quote': 'from January 30,\n2024 to January 28, 2025', 'value': '2024-01-30'},
         'new_maturity': {'document': 'tm243707d1_8k.htm', 'text': 'January 28, 2025',
                          'quote': 'from January 30,\n2024 to January 28, 2025', 'value': '2025-01-28'},
         'old_capacity': None,
         'new_capacity': {'document': 'tm243707d1_8k.htm', 'text': '$1.7 billion',
                          'quote': 'in the amount of $1.7 billion', 'value': 1.7, 'unit': 'billion',
                          'currency': 'USD'},
         'currency': {'document': 'tm243707d1_8k.htm', 'text': '$', 'quote': 'in the amount of $1.7 billion',
                      'value': 'USD'},
         'effective_date': {'document': 'tm243707d1_8k.htm', 'text': 'January 30, 2024',
                            'quote': 'effective as of January 30, 2024', 'value': '2024-01-30'},
         'linkage': {'kind': 'maturity', 'document': 'tm243707d1_8k.htm',
                     'quote': 'extends the expiration date of the Credit Agreement from January 30,\n2024 to January 28, 2025 in the amount of $1.7 billion',
                     'old_text': 'January 30,\n2024', 'new_text': 'January 28, 2025'},
         'note': 'Only filing with an explicit same-facility old-to-new maturity. The $1.7 billion is the extended commitment; prior capacity is not stated.'}]},
    '0001104659-24-096572': {'facilities': [
        {'id': {'document': 'tm2423020d1_8k.htm', 'text': '364-Day Facility',
                'quote': 'Credit Agreement (the “364-Day Facility”)'},
         'old_maturity': None,
         'new_maturity': {'document': 'tm2423020d1_8k.htm', 'text': 'August 28,\n2025',
                          'quote': 'that expires on August 28,\n2025', 'value': '2025-08-28'},
         'old_capacity': None,
         'new_capacity': {'document': 'tm2423020d1_8k.htm', 'text': '$3.15 billion',
                          'quote': 'aggregate amount of up to $3.15 billion', 'value': 3.15, 'unit': 'billion',
                          'currency': 'USD'},
         'currency': {'document': 'tm2423020d1_8k.htm', 'text': '$',
                      'quote': 'aggregate amount of up to $3.15 billion', 'value': 'USD'},
         'effective_date': {'document': 'tm2423020d1_8k.htm', 'text': 'August 29, 2024',
                            'quote': 'On August 29, 2024, Caterpillar Inc.', 'value': '2024-08-29'},
         'linkage': None, 'note': 'Replaces a prior 364-day facility; prior maturity not stated.'},
        {'id': {'document': 'tm2423020d1_8k.htm', 'text': 'Local Currency Addendum',
                'quote': 'Local Currency Addendum that enables CIF to borrow in certain approved currencies including Pounds\nSterling and Euros in an aggregate amount up to the equivalent of $100 million'},
         'old_maturity': None, 'new_maturity': None, 'old_capacity': None,
         'new_capacity': {'document': 'tm2423020d1_8k.htm', 'text': '$100 million',
                          'quote': 'including Pounds\nSterling and Euros in an aggregate amount up to the equivalent of $100 million',
                          'value': 100, 'unit': 'million', 'currency': 'USD'},
         'currency': {'document': 'tm2423020d1_8k.htm', 'text': '$',
                      'quote': 'including Pounds\nSterling and Euros in an aggregate amount up to the equivalent of $100 million',
                      'value': 'USD'},
         'borrowing_currency': 'Pounds Sterling and Euros (approved local currencies)',
         'currency_note': 'USD $100 million is the stated USD-equivalent ceiling of this addendum sub-limit, not the currency borrowed; borrowings are in approved local currencies including Pounds Sterling and Euros. Kept separate from, and never summed into, the $3.15 billion 364-Day Aggregate Commitment.',
         'effective_date': None, 'linkage': None,
         'note': 'Local-currency addendum within the 364-Day Aggregate Commitment, parallel to the CAT 2022 row; recorded separately and not summed into the parent commitment.'},
        {'id': {'document': 'tm2423020d1_8k.htm', 'text': 'Japan Local Currency Addendum',
                'quote': 'Japan Local Currency Addendum that enables\nCFKK to borrow Japanese Yen in an aggregate amount up to the equivalent of $100 million'},
         'old_maturity': None, 'new_maturity': None, 'old_capacity': None,
         'new_capacity': {'document': 'tm2423020d1_8k.htm', 'text': '$100 million',
                          'quote': 'Japanese Yen in an aggregate amount up to the equivalent of $100 million',
                          'value': 100, 'unit': 'million', 'currency': 'USD'},
         'currency': {'document': 'tm2423020d1_8k.htm', 'text': '$',
                      'quote': 'Japanese Yen in an aggregate amount up to the equivalent of $100 million',
                      'value': 'USD'},
         'borrowing_currency': 'Japanese Yen',
         'currency_note': 'USD $100 million is the stated USD-equivalent ceiling of this addendum sub-limit, not the currency borrowed; borrowings are in Japanese Yen. Kept separate from, and never summed into, the $3.15 billion 364-Day Aggregate Commitment.',
         'effective_date': None, 'linkage': None,
         'note': 'Japan local-currency addendum within the 364-Day Aggregate Commitment, parallel to the CAT 2022 row; recorded separately and not summed into the parent commitment.'},
        {'id': {'document': 'tm2423020d1_8k.htm', 'text': 'Three-Year Facility',
                'quote': 'extends the expiration date of the Three-Year Facility to August 29, 2027'},
         'old_maturity': None,
         'new_maturity': {'document': 'tm2423020d1_8k.htm', 'text': 'August 29, 2027',
                          'quote': 'extends the expiration date of the Three-Year Facility to August 29, 2027',
                          'value': '2027-08-29'},
         'old_capacity': None, 'new_capacity': None, 'currency': None,
         'effective_date': {'document': 'tm2423020d1_8k.htm', 'text': 'August 29, 2024',
                            'quote': 'On August 29, 2024, Caterpillar Inc.', 'value': '2024-08-29'},
         'linkage': None, 'note': 'Amendment No. 2 states only the new termination date; prior date not recited.'},
        {'id': {'document': 'tm2423020d1_8k.htm', 'text': 'Five-Year Facility',
                'quote': 'extends the expiration date of the Five-Year Facility to August 29, 2029'},
         'old_maturity': None,
         'new_maturity': {'document': 'tm2423020d1_8k.htm', 'text': 'August 29, 2029',
                          'quote': 'extends the expiration date of the Five-Year Facility to August 29, 2029',
                          'value': '2029-08-29'},
         'old_capacity': None, 'new_capacity': None, 'currency': None,
         'effective_date': {'document': 'tm2423020d1_8k.htm', 'text': 'August 29, 2024',
                            'quote': 'On August 29, 2024, Caterpillar Inc.', 'value': '2024-08-29'},
         'linkage': None, 'note': 'Amendment No. 2 states only the new termination date; prior date not recited.'}]},
    '0001193125-24-174346': {'facilities': [
        {'id': {'document': 'd447517d8k.htm', 'text': 'Second 364-Day Credit Agreement',
                'quote': 'Second 364-Day Credit Agreement (the “ Second 364-Day Credit Agreement ”)'},
         'old_maturity': None,
         'new_maturity': {'document': 'd447517d8k.htm', 'text': 'July 1, 2025',
                          'quote': 'repaid no later than July 1, 2025', 'value': '2025-07-01'},
         'old_capacity': None,
         'new_capacity': {'document': 'd447517d8k.htm', 'text': '$1.5 billion',
                          'quote': 'aggregate principal amount of $1.5 billion', 'value': 1.5, 'unit': 'billion',
                          'currency': 'USD'},
         'currency': {'document': 'd447517d8k.htm', 'text': '$',
                      'quote': 'aggregate principal amount of $1.5 billion', 'value': 'USD'},
         'effective_date': {'document': 'd447517d8k.htm', 'text': 'July 2, 2024',
                            'quote': 'On July 2, 2024, Honeywell International Inc.', 'value': '2024-07-02'},
         'linkage': None, 'note': 'New agreement; no prior term stated in this package.'}]},
    '0001193125-25-055636': {'facilities': [
        {'id': {'document': 'd915924d8k.htm', 'text': '364-Day Credit Agreement',
                'quote': '364-Day Credit Agreement (the “ 364-Day Credit Agreement ”)'},
         'old_maturity': None,
         'new_maturity': {'document': 'd915924d8k.htm', 'text': 'March 16, 2026',
                          'quote': 'repaid no later than March 16, 2026', 'value': '2026-03-16'},
         'old_capacity': None,
         'new_capacity': {'document': 'd915924d8k.htm', 'text': '$3.0 billion',
                          'quote': 'aggregate principal amount of $3.0 billion', 'value': 3.0, 'unit': 'billion',
                          'currency': 'USD'},
         'currency': {'document': 'd915924d8k.htm', 'text': '$',
                      'quote': 'aggregate principal amount of $3.0 billion', 'value': 'USD'},
         'effective_date': {'document': 'd915924d8k.htm', 'text': 'March 17, 2025',
                            'quote': 'On March 17, 2025, Honeywell International Inc.', 'value': '2025-03-17'},
         'linkage': None, 'note': 'New agreement; same-day termination of a separate facility is a different row.'},
        {'id': {'document': 'd915924d8k.htm', 'text': '364-day credit agreement dated as of March 18, 2024',
                'quote': 'terminated the commitments under its $1.5 billion 364-day credit agreement dated as of March 18, 2024'},
         'old_maturity': None, 'new_maturity': None,
         'old_capacity': {'document': 'd915924d8k.htm', 'text': '$1.5 billion',
                          'quote': 'terminated the commitments under its $1.5 billion 364-day credit agreement dated as of March 18, 2024',
                          'value': 1.5, 'unit': 'billion', 'currency': 'USD'},
         'new_capacity': None,
         'currency': {'document': 'd915924d8k.htm', 'text': '$',
                      'quote': 'terminated the commitments under its $1.5 billion 364-day credit agreement dated as of March 18, 2024',
                      'value': 'USD'},
         'effective_date': None, 'linkage': None,
         'note': 'The 8-K never states this is the same facility as the new $3.0 billion agreement, so no capacity pair is claimed.'}]},
    '0000060667-25-000199': {'facilities': [
        {'id': {'document': 'low-20251009.htm', 'text': 'Term Loan Credit Agreement',
                'quote': 'Term Loan Credit Agreement (the “ Term Loan Credit Agreement ”)'},
         'old_maturity': None,
         'new_maturity': {'document': 'low-20251009.htm', 'text': 'third anniversary of the signing date',
                          'quote': 'that will mature on the third anniversary of the signing date thereof',
                          'value': None},
         'old_capacity': None,
         'new_capacity': {'document': 'low-20251009.htm', 'text': '$2.0 billion',
                          'quote': '$2.0 billion unsecured term loan facility (the “ Term Loan Facility ”)',
                          'value': 2.0, 'unit': 'billion', 'currency': 'USD'},
         'currency': {'document': 'low-20251009.htm', 'text': '$',
                      'quote': '$2.0 billion unsecured term loan facility (the “ Term Loan Facility ”)',
                      'value': 'USD'},
         'effective_date': {'document': 'low-20251009.htm', 'text': 'September 16, 2025',
                            'quote': 'on September 16, 2025, the Company entered into a Term Loan Credit Agreement',
                            'value': '2025-09-16'},
         'linkage': None, 'note': 'Relative maturity text quoted; no explicit calendar date, so value is null.'}]},
    '0001193125-25-067902': {'facilities': [
        {'id': {'document': 'd943962d8k.htm', 'text': 'ZT Credit Agreement',
                'quote': 'the “ ZT Credit Agreement ”'},
         'old_maturity': None,
         'new_maturity': {'document': 'd943962d8k.htm', 'text': 'December 31, 2026',
                          'quote': 'that matures December 31, 2026', 'value': '2026-12-31'},
         'old_capacity': None,
         'new_capacity': None,
         'off_protocol': {'field': 'new_capacity', 'document': 'd943962d8k.htm',
                          'quote': 'an amount up to $641,666,666.67', 'raw_usd': 641666666.67,
                          'reason': "The source states a raw dollar figure with no explicit thousands/millions/billions scaling word, which the frozen 'amounts' clause forbids recording as an amount. The numeric capacity is null; the raw figure is retained here only as an off-protocol provenance note and is never scaled, counted, or treated as evidence."},
         'currency': {'document': 'd943962d8k.htm', 'text': '$', 'quote': 'an amount up to $641,666,666.67',
                      'value': 'USD'},
         'effective_date': None, 'linkage': None,
         'note': 'Pre-existing asset-based revolver described after the acquisition; no new facility date stated. Capacity is null because the stated $641,666,666.67 is a raw dollar amount with no scaling word (closed audit deviation DEV-1).'},
        {'id': {'document': 'd943962d8k.htm', 'text': 'master receivables purchase agreement',
                'quote': 'master receivables purchase agreement, dated as of April 19, 2022'},
         'old_maturity': None, 'new_maturity': None, 'old_capacity': None,
         'new_capacity': None,
         'off_protocol': {'field': 'new_capacity', 'document': 'd943962d8k.htm',
                          'quote': 'a facility limit of $850,000,000', 'raw_usd': 850000000.0,
                          'reason': "The source states a raw dollar figure with no explicit thousands/millions/billions scaling word, which the frozen 'amounts' clause forbids recording as an amount. The numeric capacity is null; the raw figure is retained here only as an off-protocol provenance note and is never scaled, counted, or treated as evidence."},
         'currency': {'document': 'd943962d8k.htm', 'text': '$', 'quote': 'a facility limit of $850,000,000',
                      'value': 'USD'},
         'effective_date': None, 'linkage': None,
         'note': 'Separate receivables purchase facility, kept separate; no stated maturity. Capacity is null because the stated $850,000,000 is a raw dollar amount with no scaling word (closed audit deviation DEV-1).'}]},
}

# ---------------------------------------------------------------------------
# Freeze / verify
# ---------------------------------------------------------------------------
def protected_manifest():
    """Hash the historical coverage protocol and the six frozen payoff files."""
    freeze_hashes = json.loads((ROOT / 'EARNINGS_PAYOFF_FREEZE.json').read_text())
    recomputed = {name: checksum(ROOT / name) for name in freeze_hashes['implementation_files']}
    if recomputed != freeze_hashes['implementation_files']:
        raise ValueError('EARNINGS_PAYOFF_FREEZE.json implementation hashes changed; stop.')
    historical_protocol = json.loads((ROOT / 'historical_credit_coverage/protocol.json').read_text())
    claim = '726caa85be518c3a4a3791bdc8b43db99bad0adcf44868252dcaaf267c164062'
    if digest(historical_protocol) != claim or json.loads(
            (ROOT / 'historical_credit_coverage/protocol_hash.json').read_text())['sha256'] != claim:
        raise ValueError('Historical credit coverage protocol changed; stop.')
    enrollment = json.loads(ENROLLMENT.read_text())
    if digest(enrollment) != json.loads(ENROLLMENT_HASH.read_text())['sha256']:
        raise ValueError('Historical coverage enrollment changed; stop.')
    return {
        'historical_credit_coverage_protocol_sha256': claim,
        'historical_credit_coverage_protocol_recomputed': digest(historical_protocol),
        'historical_credit_coverage_protocol_md_sha256': checksum(ROOT / 'docs/research/HISTORICAL_CREDIT_COVERAGE_PROTOCOL.md'),
        'enrollment_digest': digest(enrollment),
        'enrollment_bytes_sha256': checksum(ENROLLMENT),
        'earnings_payoff_freeze_json_sha256': checksum(ROOT / 'EARNINGS_PAYOFF_FREEZE.json'),
        'earnings_payoff_freeze_recomputed': recomputed,
    }


def validate_scope(event):
    if not PROTOCOL['window'][0] <= event['filing_date'] <= PROTOCOL['window'][1]:
        raise ValueError('Enrollment date escaped the authorized 2022-2025 window.')
    if HOLDOUT[0] <= event['filing_date'] <= HOLDOUT[1] or event['filing_date'] >= '2026-01-01':
        raise ValueError('Enrollment date touched the sealed holdout or 2026.')
    if len(event['tickers']) != 1:
        raise ValueError('Selection requires exactly one economic ticker per enrollment row.')
    return event['tickers'][0]


def select(enrollment):
    """Deterministic metadata-only selection: SHA256(accession) ascending."""
    picks = []
    for year in YEARS:
        rows = [r for r in enrollment if r['filing_date'][:4] == year]
        rows = sorted(rows, key=lambda r: (hashlib.sha256(r['accession_number'].encode()).hexdigest(),
                                           r['accession_number']))
        seen, chosen = set(), 0
        for row in rows:
            ticker = validate_scope(row)
            if ticker in seen:
                continue
            seen.add(ticker)
            picks.append({'accession_number': row['accession_number'], 'cik': row['cik'].zfill(10),
                          'ticker': ticker, 'filing_date': row['filing_date'],
                          'filing_url': row['filing_url'],
                          'selection_sha256': hashlib.sha256(row['accession_number'].encode()).hexdigest()})
            chosen += 1
            if chosen == PER_YEAR:
                break
        if chosen != PER_YEAR:
            raise ValueError(f'Year {year} supplies fewer than {PER_YEAR} distinct-ticker filings.')
    if len(picks) != PER_YEAR * len(YEARS) or len({p['accession_number'] for p in picks}) != len(picks):
        raise ValueError('Fixed-12 selection is not 12 distinct accessions.')
    return picks


def verify():
    if json.loads((OUTPUT / 'protocol.json').read_text()) != PROTOCOL:
        raise ValueError('Credit-terms pilot protocol changed; do not migrate or silently rescore.')
    if json.loads((OUTPUT / 'protocol_hash.json').read_text()) != {'sha256': digest(PROTOCOL)}:
        raise ValueError('Credit-terms pilot protocol hash mismatch.')
    if json.loads((OUTPUT / 'preservation.json').read_text()) != protected_manifest():
        raise ValueError('Protected prior research changed; stop. Do not touch frozen experiments.')
    frozen = json.loads((OUTPUT / 'selection.json').read_text())
    enrollment = json.loads(ENROLLMENT.read_text())
    if select(enrollment) != frozen:
        raise ValueError('Selection is no longer deterministic; enrollment metadata changed.')
    if digest(frozen) != json.loads((OUTPUT / 'selection_hash.json').read_text())['sha256']:
        raise ValueError('Frozen selection digest mismatch.')


def stage_freeze():
    enrollment = json.loads(ENROLLMENT.read_text())
    if len(enrollment) != 147 or len({r['cik'] for r in enrollment}) != 55 or len(
            {t for r in enrollment for t in r['tickers']}) != 54:
        raise ValueError('Historical coverage enrollment shape changed; explicit diagnosis required.')
    if digest(enrollment) != json.loads(ENROLLMENT_HASH.read_text())['sha256']:
        raise ValueError('Historical coverage enrollment digest mismatch.')
    picks = select(enrollment)
    OUTPUT.mkdir(exist_ok=True)
    freeze(OUTPUT / 'protocol.json', PROTOCOL)
    freeze(OUTPUT / 'protocol_hash.json', {'sha256': digest(PROTOCOL)})
    freeze(OUTPUT / 'selection.json', picks)
    freeze(OUTPUT / 'selection_hash.json', {'sha256': digest(picks)})
    freeze(OUTPUT / 'preservation.json', protected_manifest())
    doc = ['# Credit-term source-evidence measurement pilot: protocol', '',
        'Kind: outcome-blind, source-only, numerical measurement feasibility pilot over a fixed 12-filing set. No economic outcome, no market price, no option data, no classifier, no semantic score, no JEV or model call, and no trade-hypothesis freeze.',
        '',
        'The historical coverage study enrolled 147 original 8-Ks (54 issuers) across 2022-2025 with 2023-06-01..2023-08-31 sealed. This pilot measures whether explicit numerical credit terms (facility identity, old/new maturity, old/new capacity, currency, effective/announcement date) can be read by hand from original SEC packages, and how many of the fixed 12 carry a verifiable paired maturity and/or capacity change. It is a measurement feasibility pilot, not a population prevalence estimate and not an economic result.',
        '',
        '## Selection (frozen before any SEC package is read)', '',
        'Exactly three filings per year 2022, 2023, 2024, 2025, by ascending SHA256(accession_number UTF-8), skipping a repeat economic ticker within that year. Selection uses frozen enrollment metadata only, and the 12 accessions and ordering are frozen here before any SEC package is read or requested.', '',
        '## Evidence (manually reviewed, no heuristic parser)', '',
        'For each filing document an explicit facility identifier/name, stated old maturity, stated new maturity, old capacity, new capacity, currency, and effective/announcement date, each with an exact whitespace-normalized quote and offsets. Missing stays null. Distinct facilities and tranches stay separate. A numeric date difference is computed only for an explicitly linked same-facility old/new pair.', '',
        '## Boundaries', '',
        'Original SEC packages only, at most 2 requests/second, with a hash-and-header cache and fail-fast on systemic access errors. No 2026 source, no sealed 2023 holdout read, and the older novelty cache exposing 74 reserved 2023 dates is not read. The historical coverage protocol and all six EARNINGS_PAYOFF_FREEZE.json hashes are preserved and re-verified.', '',
        '## Exact specification', '', f'Protocol SHA256: `{digest(PROTOCOL)}`.', '',
        '```json', json.dumps(PROTOCOL, indent=2), '```', '',
        '## Frozen selection', '', '```json', json.dumps(picks, indent=2), '```', '']
    (ROOT / 'docs/research/CREDIT_TERMS_PILOT_PROTOCOL.md').write_text('\n'.join(doc))
    print('Frozen credit-terms protocol', digest(PROTOCOL), 'picks', len(picks), flush=True)


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
def events():
    verify()
    return json.loads((OUTPUT / 'selection.json').read_text())


def stage_retrieve():
    cohort = events()
    folder = OUTPUT / 'packages'
    folder.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers['User-Agent'] = SEC_USER_AGENT
    keep = ['Date', 'Content-Type', 'Content-Length', 'ETag', 'Last-Modified', 'Server']
    for i, event in enumerate(cohort):
        accession = event['accession_number']
        record_path = folder / f'{accession}.json'
        raw_path = folder / f'{accession}.txt'
        url = source_url(event['filing_url'], event)
        if record_path.exists():
            record = json.loads(record_path.read_text())
            if record['url'] != url or (record.get('success') and checksum(raw_path) != record['raw_sha256']):
                raise ValueError('Original package integrity failure.')
            continue
        record = {'accession': accession, 'url': url, 'attempts': [], 'success': False}
        for attempt in range(3):
            time.sleep(.5 if attempt == 0 else 2 ** attempt)  # <=2 req/s
            try:
                r = session.get(url, timeout=45, allow_redirects=False)
            except requests.RequestException as exc:
                raise RuntimeError('SEC connection failed; fail-fast rather than record missing evidence.') from exc
            record['attempts'].append({'status': r.status_code})
            if r.status_code == 200:
                if '<DOCUMENT>' not in r.text or '<SEC-HEADER>' not in r.text:
                    record['error'] = 'Response is not a complete SEC submission package.'
                    break
                raw_path.write_bytes(r.content)
                record.update(success=True, raw_sha256=checksum(raw_path), bytes=len(r.content),
                              headers={k: r.headers.get(k) for k in keep if r.headers.get(k) is not None})
                break
            record['error'] = f'HTTP{r.status_code}'
            if r.status_code == 403:
                raise RuntimeError('Systemic SEC 403; stop the pilot rather than treat sources as missing.')
            if r.status_code not in [429, 500, 502, 503, 504]:
                break
        freeze(record_path, record)
        print(f"Original packages {i+1}/{len(cohort)}; last={record.get('error', 'ok')}", flush=True)
    verify()


# ---------------------------------------------------------------------------
# Structural parse (mechanical, no eligibility classification)
# ---------------------------------------------------------------------------
def parse_package(raw, event):
    """Adapted from full_source_experiment.parse_package for the 2022-2025 pilot
    window (the shared helper is hard-scoped to 2024-2025). Same structure and
    validations; no evidence inference."""
    header = raw.split('<DOCUMENT>', 1)[0]

    def value(pattern):
        match = re.search(pattern, header, re.I)
        if not match:
            raise ValueError('Required SEC header field absent.')
        return match.group(1).strip()

    accession = value(r'ACCESSION NUMBER:\s*([^\r\n]+)')
    form = value(r'CONFORMED SUBMISSION TYPE:\s*([^\r\n]+)')
    filed = value(r'FILED AS OF DATE:\s*(\d{8})')
    stamp = value(r'<ACCEPTANCE-DATETIME>(\d{14})')
    cik = value(r'CENTRAL INDEX KEY:\s*(\d+)').zfill(10)
    company = value(r'COMPANY CONFORMED NAME:\s*([^\r\n]+)')
    if accession != event['accession_number'] or form != '8-K' or cik != event['cik'].zfill(10) \
            or filed != event['filing_date'].replace('-', ''):
        raise ValueError('SEC header does not match the frozen enrollment.')
    accepted = f'{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}'
    if not PROTOCOL['window'][0] <= accepted <= PROTOCOL['window'][1] or stamp[:8] > filed:
        raise ValueError('SEC acceptance timestamp escaped the authorized window.')
    if HOLDOUT[0] <= accepted <= HOLDOUT[1] or accepted >= '2026-01-01':
        raise ValueError('SEC acceptance timestamp touched the sealed holdout or 2026.')
    docs = []
    for block in re.findall(r'<DOCUMENT>(.*?)</DOCUMENT>', raw, re.S | re.I):
        def field(name):
            found = re.search(r'<' + name + r'>([^\r\n]+)', block, re.I)
            return found.group(1).strip() if found else None
        body = re.search(r'<TEXT>(.*?)</TEXT>', block, re.S | re.I)
        if not body:
            continue
        docs.append({'filename': field('FILENAME'), 'type': field('TYPE'), 'sequence': field('SEQUENCE'),
                     'description': field('DESCRIPTION'), 'text': normalized_text(body.group(1)),
                     'body_sha256': hashlib.sha256(body.group(1).encode()).hexdigest()})
    if sum(d['type'] == '8-K' and d['sequence'] == '1' for d in docs) != 1:
        raise ValueError('Exactly one sequence-1 original 8-K document required.')
    return {'accession': accession, 'company': company, 'filing_date': event['filing_date'],
            'filing_timestamp': f'{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]} {stamp[8:10]}:{stamp[10:12]}:{stamp[12:14]} America/New_York (SEC acceptance)',
            'documents': docs}


def stage_prepare():
    cohort = events()
    folder = OUTPUT / 'parsed'
    folder.mkdir(exist_ok=True)
    for event in cohort:
        accession = event['accession_number']
        record = json.loads((OUTPUT / 'packages' / f'{accession}.json').read_text())
        if not record['success']:
            freeze(folder / f'{accession}.json', {'accession': accession, 'retrieved': False, 'error': record.get('error')})
            continue
        raw_path = OUTPUT / 'packages' / f'{accession}.txt'
        if checksum(raw_path) != record['raw_sha256']:
            raise ValueError('Raw package changed.')
        parsed = parse_package(raw_path.read_text(errors='strict'), event)
        parsed['retrieved'] = True
        parsed['url'] = record['url']
        parsed['headers'] = record.get('headers', {})
        freeze(folder / f'{accession}.json', parsed)
    print('Parsed original packages:', len(cohort), flush=True)
    verify()


# ---------------------------------------------------------------------------
# Manual-evidence audit: bind quotes/offsets and verify every fact
# ---------------------------------------------------------------------------
DATE_RE = re.compile(r'%B %d, %Y'.replace('%B', r'[A-Z][a-z]+').replace('%d', r'\d{1,2}').replace('%Y', r'\d{4}'))


def date_value(text):
    """Parse an explicit calendar date text; None for a relative term."""
    normal = re.sub(r'\s+', ' ', text).strip()
    match = DATE_RE.fullmatch(normal)
    if not match:
        return None
    from datetime import datetime
    return datetime.strptime(normal, '%B %d, %Y').date().isoformat()


def document_of(parsed, filename):
    doc = next((d for d in parsed['documents'] if d['filename'] == filename), None)
    if doc is None:
        raise ValueError(f'Evidence document {filename} not in package.')
    return doc


def locate(text, quote):
    hits = [m.start() for m in re.finditer(re.escape(quote), text)]
    if len(hits) != 1:
        raise ValueError(f'Quote must occur exactly once; found {len(hits)}: {quote[:60]!r}')
    return hits[0]


def check_fact(parsed, fact):
    """Return a fact record with recomputed offsets; verify text, amount, date."""
    doc = document_of(parsed, fact['document'])
    start = locate(doc['text'], fact['quote'])
    end = start + len(fact['quote'])
    if fact['text'] not in fact['quote']:
        raise ValueError('Fact text is not inside its quote.')
    record = {'document': doc['filename'], 'document_sha256': doc['body_sha256'],
              'start': start, 'end': end, 'quote': fact['quote'], 'text': fact['text']}
    for key in ['value', 'unit', 'currency']:
        if key in fact:
            record[key] = fact[key]
    if isinstance(fact.get('value'), (int, float)):
        # Frozen 'amounts' clause: an amount is recorded only when the quote
        # carries an explicit thousands/millions/billions word and an explicit
        # currency token. Fail fast here so a raw dollar figure can never again
        # be recorded as a capacity without a scaling word.
        if not re.search(r'\b(?:thousand|million|billion)s?\b', fact['text'], re.I):
            raise ValueError(
                "Frozen 'amounts' clause violated: no explicit thousands/millions/billions "
                f"word in {fact['text']!r}; record null instead of a raw figure.")
        number = re.search(r'([\d,]+(?:\.\d+)?)', fact['text'])
        if not number or abs(float(number.group(1).replace(',', '')) - float(fact['value'])) > 1e-6:
            raise ValueError(f"Amount text does not match value: {fact['text']!r}")
        if not fact.get('unit') or not re.search(re.escape(fact['unit']), fact['text'], re.I):
            raise ValueError(f"Missing unit word: {fact['text']!r}")
        if fact.get('currency') == 'USD' and '$' not in fact['text']:
            raise ValueError(f"Missing currency token: {fact['text']!r}")
    if fact.get('value') and 'unit' not in fact:
        if fact['value'] == 'USD':
            if '$' not in fact['text']:
                raise ValueError(f"Missing currency symbol: {fact['text']!r}")
        elif date_value(fact['text']) != fact['value']:
            raise ValueError(f"Date text does not match value: {fact['text']!r}")
    return record


AMOUNT_FIELDS = ('old_capacity', 'new_capacity')


def validate_amount_rule():
    """Fail-fast scan of the authored evidence for the frozen 'amounts' clause.

    Every recorded numeric capacity must carry an explicit
    thousands/millions/billions word and a currency token. A raw dollar figure
    with no scaling word is forbidden and must stay null, so this raises before
    any derived artifact is written."""
    for accession, filing in SOURCE_EVIDENCE.items():
        for facility in filing['facilities']:
            label = facility['id']['text']
            for field in AMOUNT_FIELDS:
                fact = facility.get(field)
                if not fact or not isinstance(fact.get('value'), (int, float)):
                    continue
                if not re.search(r'\b(?:thousand|million|billion)s?\b', fact['text'], re.I):
                    raise ValueError(
                        f"{accession} {label!r} {field} lacks the frozen thousands/millions/billions "
                        "scaling word; record null and explain off-protocol instead of recording the raw figure.")


def audit_filing(parsed, evidence):
    core = next((d for d in parsed['documents'] if d['type'] == '8-K' and d['sequence'] == '1'), None)
    item_2_02 = bool(core) and bool(re.search(r'(?im)^\s*Item\s*2\.02', core['text']))
    facilities = []
    for facility in evidence['facilities']:
        row = {'id': check_fact(parsed, facility['id']), 'note': facility.get('note')}
        for field in ['old_maturity', 'new_maturity', 'old_capacity', 'new_capacity', 'currency', 'effective_date']:
            row[field] = check_fact(parsed, facility[field]) if facility.get(field) else None
        if facility.get('borrowing_currency'):
            row['borrowing_currency'] = facility['borrowing_currency']
        if facility.get('currency_note'):
            row['currency_note'] = facility['currency_note']
        if facility.get('off_protocol'):
            # Off-protocol provenance only: the raw figure is not evidence and is
            # never counted as a capacity. Its quote is still located so the
            # explanation is grounded in the parsed text.
            off = dict(facility['off_protocol'])
            off_doc = document_of(parsed, off['document'])
            off['start'] = locate(off_doc['text'], off['quote'])
            off['end'] = off['start'] + len(off['quote'])
            off['document_sha256'] = off_doc['body_sha256']
            row['off_protocol'] = off
        row['linkage'] = None
        if facility.get('linkage'):
            link = facility['linkage']
            if link['kind'] not in ['maturity', 'capacity']:
                raise ValueError('Unknown linkage kind.')
            doc = document_of(parsed, link['document'])
            start = locate(doc['text'], link['quote'])
            if link['old_text'] not in link['quote'] or link['new_text'] not in link['quote']:
                raise ValueError('Linkage quote does not contain both linked terms.')
            old_field, new_field = ('old_' + link['kind'], 'new_' + link['kind'])
            old_fact, new_fact = facility.get(old_field), facility.get(new_field)
            if not old_fact or not new_fact or old_fact['text'] != link['old_text'] or new_fact['text'] != link['new_text']:
                raise ValueError('Linkage does not bind the recorded old/new terms.')
            row['linkage'] = {'kind': link['kind'], 'document': doc['filename'],
                              'document_sha256': doc['body_sha256'], 'start': start,
                              'end': start + len(link['quote']), 'quote': link['quote'],
                              'old_text': link['old_text'], 'new_text': link['new_text']}
            if link['kind'] == 'maturity':
                old_v, new_v = date_value(link['old_text']), date_value(link['new_text'])
                if not old_v or not new_v:
                    raise ValueError('Linked maturities must be explicit calendar dates.')
                delta = (date.fromisoformat(new_v) - date.fromisoformat(old_v)).days
                row['linkage']['old_maturity'] = old_v
                row['linkage']['new_maturity'] = new_v
                row['linkage']['change_days'] = delta
            else:
                row['linkage']['change_usd'] = (
                    new_fact['value'] * UNITS[new_fact['unit']] - old_fact['value'] * UNITS[old_fact['unit']])
        facilities.append(row)
    return {'accession': parsed['accession'], 'company': parsed['company'], 'filing_date': parsed['filing_date'],
            'filing_timestamp': parsed['filing_timestamp'], 'item_2_02': item_2_02, 'facilities': facilities}


def stage_audit():
    cohort = events()
    if set(SOURCE_EVIDENCE) != {e['accession_number'] for e in cohort}:
        raise ValueError('Manual evidence does not match the frozen 12 accessions.')
    validate_amount_rule()
    audits = []
    for event in cohort:
        parsed = json.loads((OUTPUT / 'parsed' / f'{event["accession_number"]}.json').read_text())
        if not parsed.get('retrieved'):
            raise ValueError('Cannot audit an unretrieved package.')
        audits.append(audit_filing(parsed, SOURCE_EVIDENCE[event['accession_number']]))
    freeze(OUTPUT / 'source_evidence.json', audits)
    paired_m = sum(any(f['linkage'] and f['linkage']['kind'] == 'maturity' for f in a['facilities']) for a in audits)
    paired_c = sum(any(f['linkage'] and f['linkage']['kind'] == 'capacity' for f in a['facilities']) for a in audits)
    print(f'Audited 12 filings; paired maturity {paired_m}, paired capacity {paired_c}', flush=True)
    verify()


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def summarise(audits):
    tickers = {e['accession_number']: e['ticker'] for e in events()}
    rows, paired_m, paired_c, both, unlinked_m, unlinked_c = [], 0, 0, 0, 0, 0
    for a in audits:
        fac = a['facilities']
        paired_m += any(f['linkage'] and f['linkage']['kind'] == 'maturity' for f in fac)
        paired_c += any(f['linkage'] and f['linkage']['kind'] == 'capacity' for f in fac)
        both += any(f['linkage'] and f['linkage']['kind'] == 'maturity' for f in fac) and any(
            f['linkage'] and f['linkage']['kind'] == 'capacity' for f in fac)
        unlinked_m += any(f['old_maturity'] and f['new_maturity'] and not (f['linkage'] and f['linkage']['kind'] == 'maturity') for f in fac)
        unlinked_c += any(f['old_capacity'] and f['new_capacity'] and not (f['linkage'] and f['linkage']['kind'] == 'capacity') for f in fac)
        rows.append({'accession': a['accession'], 'ticker': tickers[a['accession']],
                     'filing_date': a['filing_date'], 'filing_timestamp': a['filing_timestamp'],
                     'item_2_02': a['item_2_02'], 'facilities': len(fac),
                     'facility_rows': [{'id': f['id']['text'].replace('\n', ' '),
                                        'old_maturity': (f['old_maturity'] or {}).get('value'),
                                        'new_maturity': (f['new_maturity'] or {}).get('value'),
                                        'old_capacity_usd': None if not f['old_capacity'] else f['old_capacity']['value'] * UNITS[f['old_capacity']['unit']],
                                        'new_capacity_usd': None if not f['new_capacity'] else f['new_capacity']['value'] * UNITS[f['new_capacity']['unit']],
                                        'currency': (f['currency'] or {}).get('value'),
                                        'borrowing_currency': f.get('borrowing_currency'),
                                        'currency_note': f.get('currency_note'),
                                        'off_protocol': f.get('off_protocol'),
                                        'effective_date': (f['effective_date'] or {}).get('value'),
                                        'paired': None if not f['linkage'] else f['linkage']['kind']}
                                       for f in fac]})
    return {'filings': len(audits), 'years': Counter(a['filing_date'][:4] for a in audits),
            'paired_maturity_filings': paired_m, 'paired_capacity_filings': paired_c, 'paired_both_filings': both,
            'unlinked_maturity_filings': unlinked_m, 'unlinked_capacity_filings': unlinked_c,
            'unknown_maturity_filings': len(audits) - paired_m, 'unknown_capacity_filings': len(audits) - paired_c,
            'item_2_02_filings': sum(a['item_2_02'] for a in audits), 'rows': rows}


def stage_report():
    cohort = events()
    audits = json.loads((OUTPUT / 'source_evidence.json').read_text())
    if [a['accession'] for a in audits] != [e['accession_number'] for e in cohort]:
        raise ValueError('Audit order does not match the frozen selection.')
    summary = summarise(audits)
    metrics = {
        'experiment': PROTOCOL['experiment'], 'protocol_sha256': digest(PROTOCOL),
        'selection_sha256': json.loads((OUTPUT / 'selection_hash.json').read_text())['sha256'],
        'research_kind': PROTOCOL['research_kind'],
        'provenance': {
            'annotation_author': 'opencode-go/deepseek-v4.1-flash',
            'human_authorship': False,
            'human_validation': False,
            'additional_runtime_inference_during_pipeline': False,
            'runtime_model_or_jev_calls': 0,
            'protocol_no_model_call_clause_qualification': 'The frozen protocol research_kind string says "no model call". That clause is disclosed as a limitation/ambiguity, not satisfied on every interpretation: it holds only as no additional runtime inference or model call during pipeline execution; it is NOT a claim that no model authored the annotations or this report, which were model-authored as the user required, with no human validation. See docs/research/CREDIT_TERMS_PILOT.md "Provenance and annotation scope".',
            'annotation_scope': 'sequence-1 original 8-K body only (exact-quote bound facts); an audited subset, not an exhaustive whole-package annotation',
            'exhibit_paired_term_search': 'the independent audit extended the paired-term search to every text-bearing exhibit and found no additional explicit same-facility old/new pair beyond PM',
            'exhaustive_package_annotation': False,
            'independent_audit_files': ['docs/research/CREDIT_TERMS_PILOT_REVIEW.md', 'CREDIT_TERMS_PILOT_REVIEW.json'],
            'corrections_record': 'docs/research/CREDIT_TERMS_PILOT_CORRECTIONS.md',
            'pre_correction_archive': 'credit_terms_pilot/audit_history/MANIFEST.json',
        },
        'is_measurement_feasibility_pilot': True, 'is_population_prevalence_estimate': False,
        'is_economic_result': False, 'economic_outcomes_read': False, 'market_data_requests': 0,
        'jev_or_model_calls': 0, 'trade_hypothesis_frozen': False, 'oos_or_judges_opened': False,
        'statistics': {k: v for k, v in summary.items() if k != 'rows'},
        'by_year': dict(sorted(summary['years'].items())),
        'selection': [{'accession': e['accession_number'], 'ticker': e['ticker'], 'year': e['filing_date'][:4],
                       'sha256': e['selection_sha256']} for e in cohort],
        'source_evidence': summary['rows'],
        'preservation': protected_manifest(),
        'retrieval': {e['accession_number']: {'success': True, 'bytes': json.loads(
            (OUTPUT / 'packages' / f"{e['accession_number']}.json").read_text())['bytes']} for e in cohort},
    }
    freeze(OUTPUT / 'metrics.json', metrics)
    (ROOT / 'CREDIT_TERMS_PILOT.json').write_text(json.dumps(metrics, indent=2, allow_nan=False) + '\n')
    s = summary
    timestamps = {a['accession']: a['filing_timestamp'] for a in audits}
    lines = ['# Credit-term source-evidence measurement pilot (fixed 12 original 8-Ks)', '',
        f"Decision input: **{s['paired_maturity_filings']}/12 filings have a verifiable paired maturity change, "
        f"{s['paired_capacity_filings']}/12 a verifiable paired capacity change, {s['paired_both_filings']}/12 both.** "
        'This is a measurement feasibility pilot over a fixed 12-filing set, not a population prevalence estimate and not an economic result. '
        'No market or strategy outcome was read, no classifier or semantic score was built, and no trade hypothesis was frozen. '
        'The evidence and this report are annotated by the named model `opencode-go/deepseek-v4.1-flash`, with no additional pipeline inference or runtime model call, and with no human validation.', '',
        '## Provenance and annotation scope', '',
        'Annotations are authored by `opencode-go/deepseek-v4.1-flash`; they are not human-authored and no human validation is claimed. '
        '`jev_or_model_calls: 0` is a runtime-instrumentation count for the deterministic pipeline, not a claim that no model was involved: the hand-authored evidence and this report were produced by that model, and no additional runtime inference or model call was made during pipeline execution. '
        'The frozen protocol\'s `no model call` clause is disclosed here as a limitation/ambiguity: it is satisfied only as no additional runtime inference during pipeline execution, and it is not claimed that every interpretation of that clause was met, because the annotations and this report were model-authored as the user required, with no human validation. '
        'The exact-quote bound evidence set audits the sequence-1 original 8-K body only (an audited subset); the independent audit separately extended the paired-term search to every text-bearing exhibit and found no additional explicit same-facility old/new pair beyond PM. This is not an exhaustive whole-package annotation.', '',
        '## Fixed selection', '',
        'Three filings per year 2022-2025 chosen from the frozen historical-coverage enrollment metadata by ascending SHA256(accession_number), skipping a repeat economic ticker within the year. '
        'The 12 accessions and field definitions were frozen in a hashed protocol before any SEC package was read.', '',
        '| Year | Ticker | Accession | Filed | SEC acceptance | SHA256(accession) |',
        '|---|---|---|---|---|---|']
    for e in cohort:
        lines.append(f"| {e['filing_date'][:4]} | {e['ticker']} | {e['accession_number']} | {e['filing_date']} | "
                     f"{timestamps[e['accession_number']].replace(' America/New_York (SEC acceptance)', '')} | {e['selection_sha256'][:16]}... |")
    lines += ['', '## Pairing result', '',
        '| Quantity | Filings |', '|---|---:|',
        f"| Verifiable paired **maturity** change | {s['paired_maturity_filings']} |",
        f"| Verifiable paired **capacity** change | {s['paired_capacity_filings']} |",
        f"| Both | {s['paired_both_filings']} |",
        f"| Old and new maturity both stated but not explicitly linked (unknown pairing) | {s['unlinked_maturity_filings']} |",
        f"| Old and new capacity both stated but not explicitly linked (unknown pairing) | {s['unlinked_capacity_filings']} |",
        f"| No verifiable paired maturity change (missing reads as unknown, not zero) | {s['unknown_maturity_filings']} |",
        f"| No verifiable paired capacity change (missing reads as unknown, not zero) | {s['unknown_capacity_filings']} |",
        f"| Filings with a literal Item 2.02 heading | {s['item_2_02_filings']} |", '',
        'The only verifiable paired change is PM (2024-01-24): the Extension Agreement extends the expiration date of one facility '
        'from January 30, 2024 to January 28, 2025 (364 days). No filing states an old and a new capacity for the same linked facility. '
        'HON (2025) shows an old $1.5 billion facility and a new $3.0 billion facility, but the 8-K does not state they are the same facility, so it is not counted as a pair.', '',
        '## Source-evidence table (manually reviewed; exact quotes, offsets in the ignored JSON)', '',
        'Amounts are shown in explicit USD; `null` means not stated. `pair` is the linkage kind computed only from an explicit same-facility old/new statement.', '',
        '| Ticker | Facility | Old maturity | New maturity | Old cap (USD) | New cap (USD) | Currency | Effective/announce | Pair |',
        '|---|---|---|---|---:|---:|---|---|---|']
    for row in summary['rows']:
        for f in row['facility_rows']:
            capn = lambda v: '' if v is None else f'{v:,.0f}'
            lines.append(f"| {row['ticker']} | {f['id']} | {f['old_maturity'] or ''} | {f['new_maturity'] or ''} | "
                         f"{capn(f['old_capacity_usd'])} | {capn(f['new_capacity_usd'])} | {f['currency'] or ''} | "
                         f"{f['effective_date'] or ''} | {f['paired'] or ''} |")
    lines += ['',
        'Sub-limit rows carrying a `borrowing_currency` annotation (the CAT 2022 and CAT 2024 local-currency addenda) record a USD-equivalent ceiling of $100 million; that ceiling is not the currency borrowed, and each row is kept separate from its parent facility and never summed in.', '',
        '## Corrections applied to the audited snapshot', '',
        '- **DEV-1 (closed):** the two AMD raw dollar figures (`$641,666,666.67`, ZT Credit Agreement; `$850,000,000`, master receivables purchase agreement) carry no thousands/millions/billions scaling word, so under the frozen `amounts` clause their numeric capacity is **null**; each raw figure is retained only in an off-protocol provenance note and is never scaled or counted. A fail-fast validator now rejects any numeric amount that lacks an explicit scaling word.',
        '- **DEV-2 (closed):** the CAT 2024 filing adds the two distinct local-currency addendum sub-limits (`Local Currency Addendum`, `Japan Local Currency Addendum`) at their exact quote offsets, parallel to the CAT 2022 rows; each is a $100 million USD-equivalent sub-limit inside the 364-Day Aggregate Commitment and is never summed into the $3.15 billion parent. The CAT 2022 rows now carry the same borrowing-currency clarification.',
        '- The original audited derived snapshot and code/report hashes are archived under the ignored `credit_terms_pilot/audit_history/` with a manifest; the archive is a static record, not a compatibility execution path. The corrected snapshot replaced by this cleanup is archived separately under `credit_terms_pilot/audit_history/final_review/` with its own manifest, also a static read-only record and not a compatibility path. Full details are in `docs/research/CREDIT_TERMS_PILOT_CORRECTIONS.md`.', '',
        '## Mechanism: maturity runway versus capacity', '',
        'The two credit terms carry different economics. A **capacity** change alters the size of an undrawn commitment: a larger revolver is more headroom, but an unused commitment is not cash and does not remove operating, demand or litigation risk, so its link to equity downside is weak for mega-cap issuers. '
        'A **maturity** change alters the refinancing calendar: pushing a term out reduces the near-term rollover pressure and the chance that a firm must refinance into a stressed market, which is a liquidity-runway channel that can matter to equity downside even when the commitment is undrawn. '
        'On that reasoning a paired maturity extension is the more economically meaningful of the two terms, and it is the measurement that this pilot can actually verify.', '',
        '## Chief objections', '',
        '- The pilot is tiny and fixed by hash, not random. It cannot estimate prevalence in the 147-filing population; it can only show whether measurement is possible filing by filing.',
        '- Most 8-Ks announce a new or replacement facility and do not recite a linked prior term, so a verifiable pair is the exception; an absent or unlinked prior term is unknown, not evidence that the new term was the whole disclosure. Verifying paired changes requires an amendment that recites both dates, which is a minority of disclosures; the 1/12 result reflects that disclosure structure, not necessarily economic rarity.',
        '- A maturity extension may be scheduled and anticipated, and mega-cap TOP_100 issuers are rarely funding-constrained, so even a clean measurement does not imply a priced effect.',
        '- The filing/announcement date is not the economic effective date for every facility, and a term extension changes the liability schedule rather than available capital.',
        '- The static September-2026 TOP_100 carries survivorship and large-cap selection bias.', '',
        '## Recommendation', '',
        '**Recommendation: do not extend this measurement to all 147.** The pilot is a measurement-feasibility result, not a route to a priced effect, and it gives insufficient financial feasibility at scale. '
        'The paired yield is low: 1 of 12 filings carries a verifiable paired maturity change, none carries a paired capacity change, and the remaining 11 of 12 lack a verifiable paired maturity change (missing reads as unknown, not evidence that all 11 state a new term), so extending the manual annotation to all 147 would be a large effort with a low expected paired yield. '
        'More important, the authorized contestant financial window is 2024-2025, where the direct `credit_facility` cohort is only about 62 filings, too few to support a powered numerical maturity-runway test after strict marks. '
        'No option price, payoff or economic outcome is opened for this direction, no price study or trade hypothesis is frozen, and a low paired yield is not a guarantee about any other cohort.',
        '', '## Boundaries', '',
        'Original SEC packages only, at most 2 requests/second, with a hash-and-header cache. The historical coverage protocol hash and all six EARNINGS_PAYOFF_FREEZE.json hashes were recomputed and preserved; prior frozen experiments were not modified and nothing was committed. '
        'The older unrelated novelty cache that exposed 74 reserved 2023 dates was not read; the financial replication is unrun and the actual judges window is unknown. '
        'Private packages, parsed text and cache live in the ignored `credit_terms_pilot/` directory; exact character offsets are in the ignored `source_evidence.json` and are re-verified by the `verify` stage.', '']
    (ROOT / 'docs/research/CREDIT_TERMS_PILOT.md').write_text('\n'.join(lines))
    print(json.dumps(metrics['statistics'], indent=2, default=str), flush=True)


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------
def stage_verify():
    verify()
    cohort = events()
    audits = json.loads((OUTPUT / 'source_evidence.json').read_text())
    if [a['accession'] for a in audits] != [e['accession_number'] for e in cohort]:
        raise ValueError('Audit cohort mismatch.')
    if set(SOURCE_EVIDENCE) != {e['accession_number'] for e in cohort}:
        raise ValueError('Manual evidence set mismatch.')
    validate_amount_rule()
    # Re-bind every fact from the immutable parsed text and re-check arithmetic.
    for a in audits:
        parsed = json.loads((OUTPUT / 'parsed' / f"{a['accession']}.json").read_text())
        fresh = audit_filing(parsed, SOURCE_EVIDENCE[a['accession']])
        if fresh != a:
            raise ValueError('Recomputed source evidence differs from the frozen table.')
    summary = summarise(audits)
    # Scope and selection determinism checks.
    if len(cohort) != 12 or Counter(e['filing_date'][:4] for e in cohort) != Counter({y: 3 for y in YEARS}):
        raise ValueError('Selection is not exactly three filings per year.')
    if any(HOLDOUT[0] <= e['filing_date'] <= HOLDOUT[1] or e['filing_date'] < '2022-01-01' or e['filing_date'] > '2025-12-31' for e in cohort):
        raise ValueError('Selection escaped the authorized window or touched the holdout.')
    if any(len(SOURCE_EVIDENCE[e['accession_number']]['facilities']) < 1 for e in cohort):
        raise ValueError('Every filing must carry at least one factual facility row.')
    print('Verified pilot:', json.dumps({k: v for k, v in summary.items() if k != 'rows'}, default=str), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['freeze', 'retrieve', 'prepare', 'audit', 'report', 'verify'])
    {'freeze': stage_freeze, 'retrieve': stage_retrieve, 'prepare': stage_prepare,
     'audit': stage_audit, 'report': stage_report, 'verify': stage_verify}[parser.parse_args().stage]()
