# Dependence review

The registered primary interval groups repeated companies, reused controls and overlapping holding periods into connected components. This is deliberately conservative. A dense chain of overlapping events can connect most of the study into one component, making that interval unestimable. This is a limitation of the estimator and available independent variation; it does not establish that the economic effect is zero.

Firm clustering alone misses common market shocks. Calendar clustering alone misses persistent company effects. Multiway clustering addresses nonnested dependence, but standard firm/date clustering is not automatically robust to serially correlated common time effects. These issues are discussed in [Cameron, Gelbach and Miller](https://www.nber.org/papers/t0327) and [Standard errors for two-way clustering with serially correlated time effects](https://arxiv.org/abs/2201.11304).

Any alternative estimator needs a separately recorded specification and validation of its assumptions. In particular, overlapping 21-session event and control returns create dependence across dates; distant event labels can share nearby control holdings. A shorter arbitrary date cluster cannot be substituted merely to obtain a narrower interval.

The current primary rule remains unchanged. No alternative interval is selected according to whether it produces significance. A future calendar-panel approach would need daily strategy contributions, company dependence, common serial effects, sufficient time coverage, and independent validation. It cannot be represented as a fresh sealed-window result from the already inspected historical data.
