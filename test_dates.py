import re

MONTHS = {m: i for i, m in enumerate('jan feb mar apr may jun jul aug sep oct nov dec'.split(), 1)}
MONTH_WORDS = {w: MONTHS[w[:3]] for m in ('january february march april june july august september october november december'.split())
               for w in (m, m[:3])} | {'may': 5, 'sept': 9}
DATE_RE = re.compile(r'\b(?:(?P<mon>[A-Za-z]{3,9})\.?\s+(?P<d>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<y>\d{4})|(?P<m2>\d{1,2})/(?P<d2>\d{1,2})/(?P<y2>\d{4}))\b')

# Test cases from the failures
test_texts = [
    'Mr. Harry K. Sideris was appointed as the President and Chief Executive Officer and as a member of the Board of Directors of Duke Energy, effective April 1, 2025.',
    'David J. Rosa, currently the Company\'s President, as Chief Executive Officer of the Company effective July 1, 2025.',
    'Clayton Magouyrk and Michael Sicilia were promoted to the roles of Chief Executive Officer of Oracle and members of the Board as of the Effective Date.',
    'On February 3, 2026, PayPal Holdings, Inc. (the "Company") announced that on February 2, 2026, the Board of Directors (the "Board") of the Company appointed Enrique Lores',
    'The Board appointed John Ternus, Apple\'s Senior Vice President of Hardware Engineering, as Chief Executive Officer and a member of the Board, in each case effective on the Transition Date.',
    'Salvatore Mancuso was elected Chief Executive Officer ("CEO") of Altria Group, Inc. ("Altria") effective upon the conclusion of Altria\'s Annual Meeting of Shareholders held on May 14, 2026. On May 13, 2026, the Compensation and Talent Development Committee',
    'Doug Petno, 61, and Troy Rohrbaugh, 56, Co-CEOs of the Commercial & Investment Bank (\'CIB\'), have been elected Co-Presidents of the Firm, effective immediately.',
    'Mr. Bartlett stepped down from his position as President and Chief Executive Officer, effective February 1, 2024, and will remain in his current role of advisor to the Chief Executive Officer until May 1, 2024.',
    'Jon Moeller, Chairman of the Board, President and Chief Executive Officer, will transition into the role of Executive Chairman of the Board, effective January 1, 2026, to serve at the pleasure of the Board of Directors.',
    'Chairman & CEO Peter Zaffino has notified the Company\'s Board of Directors that he intends to transition to Executive Chair of the Company and retire as CEO by mid-year.',
]

for text in test_texts:
    dates = []
    for m in DATE_RE.finditer(text):
        mon, d, y = (MONTH_WORDS.get((m['mon'] or '').lower()), m['d'], m['y']) if m['mon'] else (int(m['m2']), m['d2'], m['y2'])
        try:
            if mon:
                dates.append(f'{y}-{mon:02d}-{int(d):02d}')
        except ValueError:
            pass
    print(f'Found: {dates}')
    print(f'Text: {text[:100]}...')
    print()