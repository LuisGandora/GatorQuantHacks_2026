"""Check sweep equivalence to the existing full company/overlap graph."""
import numpy as np
import pandas as pd
import leadership_hypothesis as p
from broad_strategy_analysis import fast_dependence_clusters
p.np = np  # The reference helper normally receives numpy through load_starter().

rng = np.random.default_rng(20261003)
for trial in range(200):
    rows = []
    for i in range(int(rng.integers(1, 60))):
        starts = rng.integers(0, 500, int(rng.integers(1, 5)))
        intervals = [(int(start), int(start+rng.integers(0, 30))) for start in starts]
        rows.append(dict(ticker=str(rng.integers(0, 20)), intervals=intervals))
    frame = pd.DataFrame(rows)
    reference, fast = p.dependence_clusters(frame), fast_dependence_clusters(frame)
    np.testing.assert_array_equal(reference[:, None] == reference[None, :], fast[:, None] == fast[None, :])
print('PASS: 200 company/overlap graph comparisons, including control intervals and zero-length holds.')
