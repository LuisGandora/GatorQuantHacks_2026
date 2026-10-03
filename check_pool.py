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

# Load the pool to see what dates the parser finds
pool = pd.read_csv('runs/date_queue.csv')
print(f"Pool size: {len(pool)}")
print()

# Check a few pool events that have parsed dates
for _, row in pool.head(20).iterrows():
    ann = announce_date(row['supporting_text'], row['filing_date'])
    dates = dates_in(row['supporting_text'])
    print(f"{row['tag']} {row['ticker']} filing={row['filing_date']} parsed={ann} all_dates={dates}")
    print(f"  Text: {row['supporting_text'][:150]}...")
    print()