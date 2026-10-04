"""Audit saved execution inputs without calculating or inspecting trade returns."""
import json
from collections import Counter
from pathlib import Path
from datetime import datetime
import argparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'governance_executable_candidate'


def audit(folder='governance_executable_candidate'):
    out = ROOT / folder
    months=3 if folder.startswith('credit_') else 4
    report = {}
    for window in ('discovery', 'validation'):
        files = sorted((out / 'call_coverage' / window).glob('*.json'))
        statuses, errors, issuers = Counter(), [], set()
        matches = 0
        for file in files:
            row = json.loads(file.read_text())
            statuses[row['status']] += 1
            if row['status'] != 'matched':
                continue
            matches += 1
            issuer = row.get('issuer')
            if not issuer or issuer in issuers:
                errors.append([file.name, 'missing_or_repeated_issuer'])
            issuers.add(issuer)
            event = row['event']
            for trade in [event] + row['controls']:
                if trade['strike'] <= trade['spot']:
                    errors.append([file.name, 'call_not_otm'])
                if abs(trade['dte_sessions'] - event['dte_sessions']) > 7:
                    errors.append([file.name, 'maturity_caliper'])
                if not .8 <= trade['rv20'] / event['rv20'] <= 1.25:
                    errors.append([file.name, 'volatility_caliper'])
                dates = [datetime.fromisoformat(trade[k]) for k in ('day', 'exit_date')]
                if (dates[0].year, (dates[0].month-1)//months) != (dates[1].year, (dates[1].month-1)//months):
                    errors.append([file.name, 'hold_crosses_block'])
                for kind in ('entry_quote', 'exit_quote'):
                    q = trade[kind]
                    if not (q['status'] == 'valid' and 0 < q['bid'] <= q['ask'] and min(q['bid_size'], q['ask_size']) > 0):
                        errors.append([file.name, 'invalid_book'])
                    bar_end = (q['stock_bar_timestamp_ms'] + 60_000) * 1_000_000
                    age = (q['sip_timestamp'] - bar_end) / 1e9
                    if not 0 <= age <= 60 or q['execution_timestamp_ns'] != q['sip_timestamp'] + 100_000_000:
                        errors.append([file.name, 'timestamp_integrity'])
                    clock=datetime.fromtimestamp(q['sip_timestamp']/1e9,ZoneInfo('America/New_York'))
                    if not 9*3600+45*60 <= clock.hour*3600+clock.minute*60+clock.second < 10*3600+15*60:
                        errors.append([file.name,'outside_execution_window'])
            if folder.startswith('credit_prebaseline'):
                if len(row['controls'])!=1 or row['controls'][0]['expiry']!=event['expiry'] or event['dte_sessions']-row['controls'][0]['dte_sessions']!=-5:
                    errors.append([file.name,'prebaseline_expiry_or_session_gap'])
        report[window] = dict(examined=len(files), matched=matches,
            exclusion_counts=dict(statuses), input_integrity_errors=errors,
            returns_calculated=False,
            limitation='Checkpoint audit; historical CIK checks are performed by the collector. Full text and fixed-horizon coverage audits remain required.')
    target = out / 'input_audit.json'
    target.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    if any(x['input_integrity_errors'] for x in report.values()):
        raise SystemExit('Saved execution inputs failed audit')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--folder', choices=['governance_executable_candidate', 'governance_executable_v2_candidate', 'governance_executable_v3_candidate','credit_renewal_v2_candidate','credit_prebaseline_candidate','credit_prebaseline_v2_candidate','credit_prebaseline_v3_candidate'], default='governance_executable_candidate')
    audit(p.parse_args().folder)
