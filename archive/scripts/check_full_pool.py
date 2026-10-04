import re
import pandas as pd

MONTHS = {m: i for i, m in enumerate('jan feb mar apr may jun jul aug sep oct nov dec'.split(), 1)}
MONTH_WORDS = {w: MONTHS[w[:3]] for m in ('january february march april june july august september october november december'.split())
               for w in (m, m[:3])} | {'may': 5, 'sept': 9}
DATE_RE = re.compile(r'\b(?:(?P<mon>[A-Za-z]{3,9})\.?\s+(?P<d>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<y>\d{4})|(?P<m2>\d{1,2})/(?P<d2>\d{1,2})/(?P<y2>\d{4}))\b')

def dates_in(text):
    out = []
    for m in DATE_RE.finditer(text or ""):
        mon, d, y = (MONTH_WORDS.get((m["mon"] or "").lower()), m["d"], m["y"]) if m["mon"] else (int(m["m2"]), m["d2"], m["y2"])
        try:
            if mon:
                out.append(pd.Timestamp(int(y), mon, int(d)))
        except ValueError:
            pass
    return out

def announce_date(text, filing_date):
    past = [d for d in dates_in(text) if d <= pd.Timestamp(filing_date).normalize()]
    return max(past) if past else None

# Load the full pool by running the events function logic
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

# We need to load the pipeline to get events
# Let's just check the jev_texts.csv which has all texts with JEV scores
jev_texts = pd.read_csv('runs/jev_texts.csv')
print(f"jev_texts shape: {jev_texts.shape}")
print(f"Tags: {jev_texts['tag'].unique()}")

# Filter to fresh tags
fresh_tags = ['ceo_appointment', 'ceo_departure', 'cfo_appointment', 'cfo_departure', 'executive_officer_appointment']
fresh_texts = jev_texts[jev_texts['tag'].isin(fresh_tags)].copy()
print(f"Fresh texts: {len(fresh_texts)}")

# Check parsed dates
fresh_texts['parsed'] = [announce_date(t, f) for t, f in zip(fresh_texts.supporting_text.fillna(""), fresh_texts.filing_date)]
fresh_texts['all_dates'] = fresh_texts.supporting_text.fillna("").apply(dates_in)

undated = fresh_texts.parsed.isna().sum()
total = len(fresh_texts)
print(f"\nUndated rate: {undated}/{total} = {undated/total:.1%}")

# Show some undated examples
print("\n=== UNDATED EXAMPLES ===")
undated_examples = fresh_texts[fresh_texts.parsed.isna()].head(20)
for _, row in undated_examples.iterrows():
    print(f"{row['tag']} {row['ticker']} filing={row['filing_date']}")
    print(f"  Dates found: {row['all_dates']}")
    print(f"  Text: {row['supporting_text'][:200]}")
    print()

# Show some dated examples  
print("\n=== DATED EXAMPLES ===")
dated_examples = fresh_texts[fresh_texts.parsed.notna()].head(10)
for _, row in dated_examples.iterrows():
    print(f"{row['tag']} {row['ticker']} filing={row['filing_date']} parsed={row['parsed'].date()}")
    print(f"  All dates: {row['all_dates']}")
    print(f"  Text: {row['supporting_text'][:200]}")
    print()