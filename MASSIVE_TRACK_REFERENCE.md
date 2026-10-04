# Massive Bonus Track — Local Challenge Reference

> **Provenance and trust level.** This file is an organized reference and paraphrase of the
> **user-supplied Massive challenge page text** pasted on **October 3, 2026** — not a verbatim
> transcription. It was **not independently browsed or verified**, and **no source URL was
> supplied**. The page's own footer states that the notebook and organizer announcements govern
> conflicts, so this reference is a **convenience copy, not the authority**. The official
> **notebook** and **organizer's Discord announcements** win over anything written here; the
> **Devpost listing** is relevant only to submission, not a higher authority than the source
> page. Nothing in this file is a ruling that the project does or does not satisfy the rules.
>
> Scope guardrails for the reference itself: it was produced without network access, without
> reading secrets or caches, without API calls, and without any financial run. It is a
> documentation-only artifact.

---

## Contents

1. [Provenance and precedence](#provenance-and-precedence)
2. [How to read the labels in this file](#how-to-read-the-labels-in-this-file)
3. [Event at a glance](#event-at-a-glance)
4. [Mission and scope](#mission-and-scope)
5. [Deliverables](#deliverables)
6. [Scoring rubric](#scoring-rubric)
7. [Study design rules](#study-design-rules)
8. [Data windows](#data-windows)
9. [Universe](#universe)
10. [Event-study methodology](#event-study-methodology)
11. [The five predefined strategies](#the-five-predefined-strategies)
12. [Strategy selection guidance (illustrative)](#strategy-selection-guidance-illustrative)
13. [No stock feed: synthetic shares and put–call parity](#no-stock-feed-synthetic-shares-and-putcall-parity)
14. [Allowed Massive API datasets](#allowed-massive-api-datasets)
15. [Trading calendar](#trading-calendar)
16. [Environment and tooling](#environment-and-tooling)
17. [Notebook structure](#notebook-structure)
18. [Starter baseline and stretch goals](#starter-baseline-and-stretch-goals)
19. [Illustrative worked examples from the page](#illustrative-worked-examples-from-the-page)
20. [Earlier-draft worked example (not current results)](#earlier-draft-worked-example-not-current-results)
21. [Prizes](#prizes)
22. [Schedule (Eastern)](#schedule-eastern)
23. [Operational checklist (12 items)](#operational-checklist-12-items)
24. [Quant note requirements (≤5 pages)](#quant-note-requirements-5-pages)
25. [Rule vs. project: organizer requirements vs. internal gates](#rule-vs-project-organizer-requirements-vs-internal-gates)
26. [Known ambiguities and unverified points](#known-ambiguities-and-unverified-points)
27. [Facts to re-verify before submission](#facts-to-re-verify-before-submission)

---

## Provenance and precedence

- **Source:** user-supplied page text pasted **2026-10-03**, paraphrased and organized here.
- **Verification:** not independently browsed or verified; **no URL supplied**.
- **Precedence on conflict:** the **official notebook** and **organizer announcements** govern;
  the page's final note states that precedence explicitly. The **Devpost listing** matters only
  for submission, not as a higher authority than the source page.
- **This reference is descriptive.** It records rules, examples, and project conventions. It
  does **not** assert that the current project passes any rule or gate.

## How to read the labels in this file

| Label | Meaning |
| --- | --- |
| `[ORGANIZER]` | Requirement stated on the challenge page. Authoritative only to the extent the page is. |
| `[STARTER]` | Behavior of the shipped starter notebook/scripts. Scaffolding, not a rule. |
| `[ILLUSTRATIVE]` | Numbers used to explain mechanics. Not results and not a guarantee. |
| `[EARLIER DRAFT]` | A worked example from an earlier draft of the page. **Not** current project output. |
| `[INTERNAL]` | This team's own gate, threshold, or convention. **Not** imposed by the organizer. |

---

## Event at a glance

- **Event:** Gator Quant Hacks (GQH) 2026.
- **Track:** Massive bonus, inside the **Systematic Trading** track. `[ORGANIZER]`
- **Dates:** October 2–4, 2026 (Eastern). `[ORGANIZER]`
- **Theme:** **8-K disclosure categories × US options** — a **research** exercise, **not** a
  P&L competition. `[ORGANIZER]`
- **Bonus linkage:** the supplied page states that **GQH judges send the ten strongest Massive
  entries to Massive**, whose team **picks the bonus winner**. `[ORGANIZER]`

## Mission and scope

`[ORGANIZER]`

- Research question: whether a chosen 8-K disclosure category carries information that is
  **not already priced** into the US options market, measured across **fixed horizons**.
- Choose **one or more disclosure categories** and **exactly one** of the **five predefined
  strategies**.
- The exercise is judged on **hypothesis novelty, analytical rigor, sealed replication, trade
  realism, and communication** — not on realized returns.
- **No guaranteed edge (research interpretation, not a page quote).** The page does describe an
  honest, well-argued **null** result with a clear **decay curve** as better than a lucky backtest.

## Deliverables

`[ORGANIZER]`

- **Notebook** — the starter notebook is the vehicle. It must run from a **clean kernel** with
  only the **API key** supplied by the runner, and with **start/end dates parametrized** so
  judges can rerun it on **unseen dates**.
- **README** — documents dependencies and how to run the notebook.
- **Quant note (PDF, ≤5 pages)** — the write-up described in
  [Quant note requirements](#quant-note-requirements-5-pages).
- **Public GitHub repository** containing the notebook and README.
- **Every source cited.**

## Scoring rubric

`[ORGANIZER]` Total = 100.

| Criterion | Weight |
| --- | ---: |
| Hypothesis novelty | 30 |
| Analytical rigor | 30 |
| Sealed replication | 20 |
| Trade realism | 10 |
| Communication | 10 |

- An honest, well-argued **null** with a clear decay curve is preferred over a lucky backtest.
- Research interpretation: there is **no guaranteed edge** (not an explicit page quote).

## Study design rules

`[ORGANIZER]`

- **Categories:** pick **one OR MORE** 8-K disclosure categories.
- **Strategy:** pick **exactly ONE** of the [five predefined strategies](#the-five-predefined-strategies).
- **Baseline:** one category, one strategy, one expiry bucket, one written interpretation.
- **Control:** compare event days against **ordinary days for the same names**.
- **Horizons:** report **all fixed horizons** (see [data windows](#data-windows) and
  [methodology](#event-study-methodology)).
- **Order of operations:** write the **hypothesis before** looking at results.
- **Costs:** all results **net of costs**.
- **Citations:** cite **every source**.
- **Repo:** public GitHub.
- **Write-up:** quant note **PDF ≤5 pages**.

## Data windows

`[ORGANIZER]`

| Window | Dates | Rule |
| --- | --- | --- |
| In-sample study | **2024-01-01 → 2025-12-31** | The fixed financial study window. |
| Out-of-sample (OOS) | **2026-01-01 → 2026-08-31** | **Do not tune** on it. |
| Judges' sealed holdout | **judge-set dates; notebook placeholders** | Dates are not disclosed; the notebook holds placeholders. |

- The notebook OOS and the **judges' sealed window replace the parent track's 20% holdout**.
- **Disclosure source coverage starts January 2022** (119 AI event types). That coverage does
  **not** expand the fixed financial study dates above. `[ORGANIZER]`

## Universe

`[ORGANIZER]`

- **TOP_100**: the **100 largest US companies**, held **static** — i.e. a fixed list with
  survivorship baked in by construction. Document this as a limitation.

## Event-study methodology

`[ORGANIZER]` unless marked.

### Timing

- **Entry:** the post-filing trade is **tradable if the filing is before the bell**; pre-filing
  **asks may already be priced in**.
- `t_pre` = **prior session chain**; `t0` = **filing session**; **post** = buy at the **close
  of t0** and exit at the horizon later.
- **Lag matters.** The rule that a company may announce within **≤4 business days** does
  **not** prove the market cannot know about the event before the filing; information can
  reach the market earlier.

### Implied move

- **Implied move = ATM(call + put) / spot.**
- Realized/implied is a **diagnostic**, **not** an automatic profit guarantee. Direction, IV,
  time, strike, and cost all matter.

### Fixed horizons

- **Holding horizons:** **1, 2, 3, 5, 10, 21, 42, 63 trading sessions**, plus **expiry**.
  `[ORGANIZER]`
- **Expiry bucket / contract DTE:** the headline bucket is **3–6 months**; the others are
  **1m / 2m**. This is the option's days-to-expiry bucket, **not** the holding horizon.
  `[ORGANIZER]`
- Moneyness: **5% OTM headline**; sensitivity **3% / 5% / 10%**. `[ORGANIZER]`

## The five predefined strategies

`[ORGANIZER]` — choose **exactly one**.

| # | Strategy | Structure | Notes given on the page |
| --- | --- | --- | --- |
| 1 | Long call | Buy **ATM call** | Max loss = premium; max gain = unlimited; breakeven = strike + premium |
| 2 | Covered call | Synthetic 100 shares; **sell OTM call** | — |
| 3 | Protective put | Synthetic shares; **buy OTM put** | — |
| 4 | Collar | Synthetic shares; **buy put, sell call** | — |
| 5 | Cash-secured put (CSP) | **Sell put**, cash-secured | — |

## Strategy selection guidance (illustrative)

`[ILLUSTRATIVE]` — how the page explains mapping a thesis to a structure. Not an automatic
rule and not a guarantee.

- Thesis sees **direction above implied** → **long call**.
- Thesis sees a **quiet / overpriced** setup → **covered call** or **CSP**.
- Thesis sees **holding risk** → **protective put** or **collar**.

**IV-crush intuition (illustrative only):**

- Hurts the **long call** and the **put hedge** (protective put).
- Helps the **short call** (covered call) and the **CSP**.
- The **collar** is roughly neutral (long put + short call).

## No stock feed: synthetic shares and put–call parity

`[ORGANIZER]`

- The challenge supplies **no stock price feed** (and no index-membership or earnings-calendar
  feed). See [allowed datasets](#allowed-massive-api-datasets).
- Where a strategy needs shares, build them **synthetically**: **long ATM call + short ATM put
  at the same strike and expiry**, by **put–call parity**.
- **Carry and dividend assumptions must be made explicit** wherever they are needed.
- Parity is a **modeling choice**, **not** an external stock feed.

## Allowed Massive API datasets

`[ORGANIZER]` — base host `api.massive.com`.

| Purpose | Endpoint |
| --- | --- |
| 8-K disclosures | `/stocks/filings/8-K/vX/disclosures` — **119 AI event types since January 2022** |
| Disclosure taxonomy | `/stocks/taxonomies/vX/disclosures` |
| Options chain (pre-session) | `/v3/reference/options/contracts?as_of=` |
| Daily aggregates (closes, volume) | `/v2/aggs/ticker/O:…/range/1/day/…` |

**Not provided:** stock feed, index-membership feed, earnings calendar. `[ORGANIZER]`

## Trading calendar

`[ORGANIZER]`

- Use **NYSE holiday rules** for the trading calendar.

## Environment and tooling

`[ORGANIZER]` / `[STARTER]`

- **Python ≥ 3.10**; tested on **3.14**. `[ORGANIZER]`
- **Starter notebook:** `gator-quant-hacks-8k-options-challenge.ipynb`.
- **Repo files:** `setup.sh`, `setup.ps1`, `requirements.txt`, `.env.example`, `.gitignore`,
  `README.md`.
- **Packages:** `pandas`, `numpy`, `requests`, `matplotlib`, `ipykernel`, `JupyterLab`.

### Key handling

`[ORGANIZER]`

- Ask for help in the **`#massive` Discord** channel.
- Provide the key via the **`MASSIVE_API_KEY` environment variable** or a **`.env`** file —
  **never hard-coded in the notebook/code**.
- **`.env` and `.massive_cache/` are ignored** and hold **licensed raw data**, which is
  **not public**.

### Setup path

`[STARTER]`

- Scripted (`./setup.sh` on macOS/Linux, `setup.ps1` on Windows): create venv → install
  dependencies → register kernel → create `.env`. Then fill in the key, choose the kernel,
  and **Run All**.
- Manual: create venv → activate → `pip install -r requirements.txt` → install `ipykernel` →
  copy `.env.example` to `.env` (then add the key).
- Windows PowerShell: `-ExecutionPolicy Bypass -File setup.ps1`, then activate and launch
  Jupyter.

### Runtime and cache behavior

`[STARTER]`

- **`RUN_PLACEBO = False`** is for iteration only; **restore it before submission**.
- The **cache never expires**; delete it explicitly to refetch. There is **no automatic
  migration**.
- Starter page claim: roughly **6,500 requests** and about **10 minutes** on a fresh run,
  **largely placebo**; cached runs take **seconds**. These are **descriptive estimates, not
  guarantees**.

## Notebook structure

`[STARTER]` — sections as described on the page:

| § | Section |
| --- | --- |
| 1 | Setup |
| 2 | Config |
| 3 | Calendar |
| 4 | Events |
| 5 | Chain / spot |
| 6 | P&L |
| 7 | Scoreboard / placebo |
| 8 | OOS |
| 9 | One ticker |
| 10 | Sensitivity |
| 11 | Trade spec |

- Plus a **timing stretch** and a **sealed, one-function-call** design for the judges' window.

## Starter baseline and stretch goals

`[STARTER]`

- **Baseline example:** CFO appointments, running **all five strategies** on the **3–6m**
  headline expiry bucket across **IS and OOS** (holding horizons remain the fixed list).
- **Stretches named on the page:**
  - Decay across horizons and buckets.
  - Combined categories.
  - Placebo.
  - Timing realism.
  - Realistic trade spec.

## Illustrative worked examples from the page

`[ILLUSTRATIVE]` — reproduced to explain mechanics. These are **not** results from the
current project, and none is evidence of edge.

### Implied-move lab

- Spot = **100**; ATM call = **3.40**; ATM put = **3.10**.
- Implied move = (3.40 + 3.10) / 100 = **6.5%**.
- Realized move = **+2** → realized/implied ratio ≈ 2 / 6.5 ≈ **0.31**.

### IV-collapse example

- **30 DTE**; IV falls **28% → 17%** (≈ a **40% relative collapse**).
- Long ATM call **cost 3.25**; decomposition: **direction +1.08**, **volatility −1.23**,
  **total −0.15 per share**.
- Black–Scholes with **zero rates**, **strike at spot**, pre-IV-calibrated **6.50 straddle**.

### Payoff explorer

- Illustrative long call: **premium 4**, **strike 100**, **breakeven 104**.
- At **108**: profit = 108 − 104 = **4 per share** = **400 per contract**.

### Source citation note

- The page refers to the **Options Playbook** conceptually (as a link label), but **no raw URL
  was supplied** in the pasted text.

## Earlier-draft worked example (not current results)

`[EARLIER DRAFT]` — the page's earlier-draft worked example, paraphrased **only** to preserve
its provenance. **It is not a current project result.** The final notebook ships with **no
outputs** and is fixed to **2024–25**, so a current first run differs.

- **70 CFO events** across **51 companies**, **2022 → November 2025**.
- Best structure: **collar**, about **+0.42% ordinary-day edge**, averaged over
  **h21 / h42 / expiry**.
- **No horizon interval excluded zero.**
- h21 after a **5% premium haircut each way**: about **−0.18%**.
- OOS had **12 events** and was only a **sign check, not proof**.

## Prizes

`[ORGANIZER]`

- **$500** to the winning team.
- **1 month of Massive Advanced** for each team member — choose **individual stocks, options,
  or futures**.
- **Swag.**
- **GQH judges send the ten strongest Massive entries to Massive**, whose team **picks the bonus
  winner**.

## Schedule (Eastern)

`[ORGANIZER]` — all times Eastern.

| Day | Time | Item |
| --- | --- | --- |
| Fri, Oct 2, 2026 | 6:30 pm | Meet Massive — Reitz Union Grand Ballroom |
| Sat, Oct 3, 2026 | 1:00 pm | Workshop — Reitz Room 2355 |
| Sat, Oct 3, 2026 | afternoon | Discord data help |
| Sun, Oct 4, 2026 | 10:00 am | **Devpost deadline** — late entries excluded |
| Sun, Oct 4, 2026 | 11:00 am | Code deadline — **commits after this are unreviewed** |
| Sun, Oct 4, 2026 | 1:00 pm | Shortlist |
| Sun, Oct 4, 2026 | 2:30 pm | Massive choice |
| Sun, Oct 4, 2026 | 3:35 pm | Winner |
| Sun, Oct 4, 2026 | — | Closing, remotely judged |

> **Operational caution:** do **not** persist a ticking browser countdown as the deadline.
> Treat the fixed Eastern times above as the schedule of record, and confirm against the
> organizer's channel.

## Operational checklist (12 items)

`[ORGANIZER]`

1. **Clean kernel**, key supplied.
2. **Start/end dates** parametrized.
3. **OOS untouched until the end** and **not tuned on**.
4. **Hypothesis** names the **category**, the **strategy**, and **why**.
5. **All horizons**, **IS and OOS**, **net of cost**, with a **CI**.
6. **Ordinary baseline / placebo**.
7. **Sensitivity**.
8. **Trade spec**: lag, cost (bps), liquidity, capacity.
9. **PDF ≤5 pages**.
10. **Public repo** with **README** and dependencies.
11. **No API key / `.env` / cache** in the submission.
12. **Devpost by 10:00 am.**

## Quant note requirements (≤5 pages)

`[ORGANIZER]`

The note must contain:

- **Hypothesis.**
- **Categories** and **strategy**.
- **Method.**
- **Results.**
- **All horizons**, **IS/OOS**.
- **Uncertainty.**
- **Break conditions.**
- **The actual trade** — including **entry lag**, **cost in bps**, **liquidity**, and
  **capacity**.
- **Sensitivity** on **neighbouring expiry**, **OTM**, **entry**, **horizon**, and
  **category definition**.

## Rule vs. project: organizer requirements vs. internal gates

**Organizer requirements** are the rules in the sections labeled `[ORGANIZER]` above:
the mission, the design constraints, the data windows, the five strategies, the allowed
datasets, the deliverables, the deadline schedule, and the 12-item checklist.

**Internal project conventions** — these are **this team's own**, and are **NOT** organizer
requirements:

- The **80/20 source-feasibility floor** and the **60/20 matched-economic-sample floor** used by
  internal experiments. Only the 80/20 is a source floor; the 60/20 is an economic inference
  floor.
- Internal **material-effect thresholds** (for example, the **0.005 net per five sessions**
  earnings benchmark referenced in the repo README).
- Internal **freeze / audit / evidence-gate** conventions and their pass/fail decisions.

These internal thresholds may shape how the team chooses to stop or continue its own work,
but they do **not** add, relax, or replace any organizer rule. This reference makes no claim
about whether the current project satisfies the organizer rules or any internal gate.

## Known ambiguities and unverified points

- **No URL and no independent verification.** The page text is paraphrased as given; wording
  that is compressed or ambiguous is not resolved here.
- **Exact scoring interpretation** (e.g., how "sealed replication" is scored) is not detailed
  beyond the weights.
- **Exact category list** and the mapping from disclosure categories to the 119 AI event types
  are not enumerated in the supplied text.
- **Holdout dates** are unknown by design (notebook placeholders).
- **Options Playbook** is referenced without a raw URL.
- The **IV-collapse example's exact percentages** are reproduced as given; the internal
  arithmetic implies roughly a 39–40% relative IV drop, described on the page as "40%".

## Facts to re-verify before submission

Confirm each of these against the **notebook** and **organizer announcements**, since they
govern conflicts:

- [ ] Study window **2024-01-01 → 2025-12-31**.
- [ ] OOS window **2026-01-01 → 2026-08-31**, not tuned.
- [ ] Holdout is **judge-set** and remains sealed.
- [ ] Holding horizons **1, 2, 3, 5, 10, 21, 42, 63** sessions plus expiry; headline expiry
      bucket **3–6m** (contract DTE, not holding horizon), other buckets **1m / 2m**.
- [ ] OTM headline **5%**, sensitivity **3/5/10%**.
- [ ] Rubric weights **30/30/20/10/10**.
- [ ] Quant note **≤5 pages**.
- [ ] Schedule times (Eastern) and the **Devpost 10:00 am** deadline.
- [ ] Prize details.

---

## Maintenance

- **Owner:** this repository's documentation set (this file and `README.md`).
- **Source of truth on conflict:** notebook and organizer announcements, not this file.
- **Change log:**
  - 2026-10-03 — created from the user-supplied Massive challenge page text; linked from
    `README.md`.
