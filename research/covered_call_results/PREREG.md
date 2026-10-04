# CC1: routine appointment covered-call incremental value

Written before reviewing this experiment's P&L or retrieving its historical OOS data.
The machine-readable `frozen_protocol.json` records the full design and implementation hashes.

Prediction: the mean **covered-call net P&L minus identical stock-alone P&L** at 21 trading
sessions, minus the same incremental value on matched ordinary days, is **positive**.
CEO and CFO appointments are separate primary tests; resignations are separate secondary tests.

Baseline: starter 3–6 month expiry, 5% OTM strike rule, next-session-close public entry,
three-session maximum exit staleness, 5% entry/exit premium haircut plus $0.65 per contract
per side. Routine classification, original universe/windows and primary ordinary-day rules
are retained from the earlier local study. Observed Massive stock closes replace parity.

All sensitivity settings, dependence intervals, exclusion counts, tails, capacity and the
judges' date-parameterized rerun are declared in the frozen protocol. No favorable sensitivity
can substitute for the primary comparison. The team's existing harness, JEV rules and ledger
are not modified or rerun as a rescue.

Related historical periods have already been viewed in previous local/team research.
These dates are historical validation, **not** untouched sealed data.

Sealed prediction: **fragile/inconclusive**, because routine observations and comparable
ordinary controls are scarce, upside tails are asymmetric, and execution costs matter.
A positive effect is not presumed to replicate. No judge window is executed here.

Before any pricing ran, a tuple/list JSON serialization comparison bug was corrected.
The abandoned registration is retained in `frozen_protocol_registration_v0.json`.
No outcome-based design revision was made.
