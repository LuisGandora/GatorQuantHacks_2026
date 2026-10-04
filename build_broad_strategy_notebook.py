"""Create a separate runnable notebook; preserve the human-owned starter."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
starter = json.loads((ROOT / 'gator-quant-hacks-8k-options-challenge.ipynb').read_text(encoding='utf-8'))


def md(text):
    return dict(cell_type='markdown', metadata={}, source=text.splitlines(keepends=True))


def code(text):
    return dict(cell_type='code', metadata={}, source=text.splitlines(keepends=True), execution_count=None, outputs=[])


starter['cells'] = [
    md('# Broad 8-K category × five-strategy discovery\n\n'
       'This separate notebook preserves the starter. The screen covers 24 categories and five strategies '
       '(120 primary comparisons); ten categories meet the preliminary 40-filing gate. '
       'Raw filing counts are not usable matched trade counts.\n\n'
       'Primary: 21 sessions, 3–6-month expiry, ATM long call and starter 5% OTM overlay legs. '
       'All fixed horizons and 3%/5%/10% strikes are retained. Overlays are incremental over stock. '
       'Gross marks, costs, capacity, and strict matched inference are distinct stages.\n'),
    code("from pathlib import Path\nimport json\nimport pandas as pd\n"
         "OUT = Path('broad_strategy_results')\n"
         "display(pd.read_csv(OUT/'category_inventory.csv'))\n"
         "display(pd.read_csv(OUT/'full_calendar_control_coverage_summary.csv'))\n"),
    md('## Recorded choices\n\n'
       'Choices are stored before performance review. Historical validation is not a pristine sealed window. '
       'The initial random-placebo pool is preserved separately from the expanded full-calendar pool. '
       'Control expansion follows date coverage, not favorable returns.\n'),
    code("for name in ['discovery_registration.json', 'cost_specification.json', "
         "'matching_inference_registration.json', 'full_calendar_control_registration.json']:\n"
         "    print(name)\n    print(json.dumps(json.loads((OUT/name).read_text(encoding='utf-8')), indent=2))\n"),
    md('## Data collection\n\n'
       'Collection uses the API key already loaded through the starter configuration. '
       'Run only one pricing process at a time. These flags default to False so opening the notebook '
       'shows saved evidence without duplicating an active terminal job.\n'),
    code("RUN_COLLECTION = False\nRUN_EXPANDED_CONTROLS = False\n"
         "if RUN_COLLECTION:\n    import broad_strategy_screen as screen\n    screen.price_all()\n"
         "if RUN_EXPANDED_CONTROLS:\n    import broad_control_inventory as controls\n    controls.price_controls()\n"
         "print('Completed category collections:', [p.parent.name for p in OUT.glob('*/pricing_complete.json')])\n"),
    md('## Accounting and saved analysis\n\n'
       'Verification checks strategy identities and output coverage. It does not prove fills or statistical significance. '
       'Strict controls use the same company/year/quarter/weekday, comparable expiry, and disclosure-free dates. '
       'Connected dependence components account conservatively for companies and overlapping holds; '
       'too few independent components prevents a reliable interval. Insignificance does not establish no effect.\n'),
    code("import verify_broad_strategy_data as verification\nverification.verify()\n"
         "for name in ['strict_matched_summary.csv', 'expanded_strict_matched_summary.csv', 'observed_expanded_strict_matched_summary.csv']:\n"
         "    path = OUT/name\n    if path.exists():\n"
         "        frame = pd.read_csv(path)\n"
         "        if not frame.empty:\n"
         "            primary = frame[(frame.horizon.astype(str)=='21') & (frame.otm==.05) & (frame.cost==.05)]\n"
         "            print(name)\n"
         "            compact = primary[['tag', 'strategy', 'events', 'companies', 'dependence_clusters', 'difference', 'ci_lo', 'ci_hi', 'conclusion']].copy()\n"
         "            compact[['difference', 'ci_lo', 'ci_hi']] *= 100\n"
         "            compact = compact.rename(columns={'difference': 'difference_pp', 'ci_lo': 'ci_lo_pp', 'ci_hi': 'ci_hi_pp'})\n"
         "            display(compact)\n"
         "            print('Differences are percentage points of entry stock notional; missing intervals do not imply no effect.')\n"
         "    else:\n        print(name, 'not yet completed')\n"),
    md('## Bid/ask execution experiment\n\n'
       'This registered pass uses the latest quote strictly before the following trading close, '
       'buys at the ask, sells at the bid, and charges $0.65 per contract per side. '
       'The primary freshness limit is 60 seconds; 300 seconds is exploratory. '
       'Displayed size is a capacity diagnostic, not a fill guarantee. Missing quotes are excluded. '
       'Category event counts are saved before P&L, separately from controls; strict matched counts follow. '
       'The 21-session comparison remains primary. Every other fixed horizon is exploratory.\n'),
    code("QUOTE = OUT/'quote_execution'\n"
         "RUN_QUOTE_COLLECTION = False\nRUN_QUOTE_ANALYSIS = False\nRUN_ALL_QUOTE_HORIZONS = False\n"
         "if RUN_QUOTE_COLLECTION:\n    import broad_quote_experiment\n    broad_quote_experiment.collect()\n"
         "if RUN_QUOTE_ANALYSIS:\n    import finish_broad_quote_experiment\n    finish_broad_quote_experiment.run()\n"
         "if RUN_ALL_QUOTE_HORIZONS:\n    import broad_quote_horizons\n    broad_quote_horizons.collect()\n"
         "    import broad_quote_returns\n    broad_quote_returns.run(QUOTE/'all_horizons', all_horizons=True)\n"
         "    import broad_quote_analysis\n"
         "    horizons = json.loads((QUOTE/'all_horizons'/'registration.json').read_text())['fixed_horizons']\n"
         "    frames = [broad_quote_analysis.analyze(QUOTE/'all_horizons', h, prefix=f'horizon_{h}_') for h in horizons]\n"
         "    pd.concat(frames, ignore_index=True).to_csv(QUOTE/'all_horizons'/'all_fixed_horizon_summary.csv', index=False)\n"
         "if (QUOTE/'registration.json').exists():\n    print(json.dumps(json.loads((QUOTE/'registration.json').read_text()), indent=2))\n"
         "for name in ['quote_usability_counts.csv', 'category_event_counts_before_returns.csv', 'bid_ask_primary_and_age_sensitivity.csv']:\n"
         "    path = QUOTE/name\n    if path.exists():\n"
         "        frame = pd.read_csv(path)\n"
         "        if not frame.empty:\n"
         "            print(name)\n"
         "            if 'difference' in frame:\n"
         "                frame[['difference', 'ci_lo', 'ci_hi']] *= 100\n"
         "                frame = frame.rename(columns={'difference': 'difference_pp', 'ci_lo': 'ci_lo_pp', 'ci_hi': 'ci_hi_pp'})\n"
         "            display(frame)\n"
         "if (QUOTE/'primary_execution_status.json').exists():\n    print(json.dumps(json.loads((QUOTE/'primary_execution_status.json').read_text()), indent=2))\n"
         "else:\n    print('Primary quote analysis is pending; coverage counts are not performance results.')\n"),
    md('## Interpretation and remaining validation\n\n'
       'A discovery signal is not an established trading edge. Review entry premiums, stock movements and tails, '
       'liquidity, costs, outliers, event text, and stability before a frozen validation test. '
       'Synthetic stock and last-trade option prices are screening limitations. No assignment or financing '
       'model is supplied. A conclusive claim requires valid uncertainty and independent validation.\n')]
path = ROOT / 'gator-quant-hacks-8k-options-broad-strategy-discovery.ipynb'
path.write_text(json.dumps(starter, ensure_ascii=False, indent=1), encoding='utf-8')
print(path)
