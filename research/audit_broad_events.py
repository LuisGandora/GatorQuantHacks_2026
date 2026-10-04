"""Record primary outliers and company concentration without changing event rules."""
from pathlib import Path
import pandas as pd

OUT = Path(__file__).resolve().parent / 'broad_strategy_results'


def run(expanded=False, observed=False):
    prefix = ('observed_' if observed else '') + ('expanded_' if expanded else '')
    robustness, audits = [], []
    for path in OUT.glob(f'*/{prefix}strict_matches.json.gz'):
        frame = pd.read_json(path)
        if frame.empty:
            continue
        frame = frame[(frame.horizon.astype(str) == '21') & (frame.otm == .05) & (frame.cost == .05)].copy()
        inventory = pd.read_csv(path.parent/'event_inventory.csv', parse_dates=['t_0'])
        inventory = inventory.rename(columns={'t_0': 'entry_date'}).drop_duplicates(['ticker', 'entry_date'])
        frame.entry_date = pd.to_datetime(frame.entry_date)
        frame = frame.merge(inventory[['ticker', 'entry_date', 'accession_number', 'supporting_text', 'filing_url']],
            on=['ticker', 'entry_date'], how='left', validate='many_to_one')
        for strategy, group in frame.groupby('strategy'):
            ordered = group.sort_values('difference')
            leave_one = [group[group.ticker != ticker].difference.mean() for ticker in group.ticker.unique()]
            robustness.append(dict(tag=path.parent.name, strategy=strategy, events=len(group),
                mean=group.difference.mean(), drop_best_three=ordered.iloc[:-3].difference.mean() if len(group) > 3 else float('nan'),
                drop_worst_three=ordered.iloc[3:].difference.mean() if len(group) > 3 else float('nan'),
                leave_one_company_min=min(leave_one) if len(leave_one) > 1 else float('nan'),
                leave_one_company_max=max(leave_one) if len(leave_one) > 1 else float('nan'),
                largest_company_share=group.ticker.value_counts().max()/len(group),
                zero_capacity_events=int((group.capacity == 0).sum()),
                interpretation='robustness diagnostic; no causal classification or independent significance claim'))
            for label, tail in [('bottom', ordered.head(5)), ('top', ordered.tail(5))]:
                tail = tail.copy()
                tail['audit_tail'] = label
                audits.append(tail)
    pd.DataFrame(robustness).to_csv(OUT/f'{prefix}outlier_robustness.csv', index=False)
    if audits:
        pd.concat(audits, ignore_index=True).to_csv(OUT/f'{prefix}event_text_audit.csv', index=False)
    print(f'Saved {len(robustness)} primary robustness diagnostics and supporting event text.')


if __name__ == '__main__':
    import sys
    run(expanded='--expanded' in sys.argv, observed='--observed-stock' in sys.argv)
