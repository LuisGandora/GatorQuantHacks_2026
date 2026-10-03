"""Verify collection coverage separately from any research conclusion."""
import json
from pathlib import Path
import pandas as pd

OUT = Path(__file__).resolve().parent / 'broad_strategy_results'


def verify(require_complete=False):
    categories = pd.read_csv(OUT/'category_inventory.csv').query('eligible_for_discovery').tag.tolist()
    complete = []
    for tag in categories:
        folder = OUT/tag
        done = (folder/'pricing_complete.json').exists()
        if done:
            required = ['event_inventory.csv', 'events_entries.csv', 'ordinary_entries.csv',
                        'events_gross_outcomes.csv.gz', 'ordinary_gross_outcomes.csv.gz',
                        'events_cost_sensitivity.csv.gz', 'ordinary_cost_sensitivity.csv.gz',
                        'events_pricing_exclusions.csv', 'ordinary_pricing_exclusions.csv']
            assert all((folder/name).exists() for name in required), f'Incomplete artifact set: {tag}'
            complete.append(tag)
    controls = pd.read_csv(OUT/'full_calendar_control_candidates.csv').drop_duplicates(['ticker', 't_0'])
    pool = OUT/'expanded_control_pool'
    expected = [pool/f'batch_{offset:05d}.csv.gz' for offset in range(0, len(controls), 25)]
    available = [path for path in expected if path.exists()]
    finished = (pool/'collection_complete.json').exists()
    if finished:
        metadata = json.loads((pool/'collection_complete.json').read_text())
        assert metadata['candidate_dates'] == len(controls)
        assert len(available) == len(expected), 'Missing expanded-control checkpoint'
        assert all((pool/f'exclusions_{offset:05d}.csv').exists() for offset in range(0, len(controls), 25))
    status = dict(category_collections=len(complete), required_categories=len(categories),
        expanded_batches_available=len(available), expanded_batches_required=len(expected),
        expanded_collection_complete=finished,
        distinction='File coverage does not prove usable prices, matching, inference, or an edge')
    if require_complete:
        assert len(complete) == len(categories) and finished, 'Collection is incomplete'
    print(json.dumps(status, indent=2))
    return status


if __name__ == '__main__':
    import sys
    verify(require_complete='--require-complete' in sys.argv)
