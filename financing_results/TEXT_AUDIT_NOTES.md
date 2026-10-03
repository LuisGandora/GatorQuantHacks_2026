# Text audit

The initial completion screen (before any financing outcomes) was tightened because it admitted “issued a press release” and equity-linked units. Boundary tests exclude pricing-only announcements, underwriting agreements alone, exchangeable securities and acquisition funding stated in the excerpt. The final screen has 124 candidates from 292 combined company/accession transactions.

After the primary IS baseline became available, the full saved excerpts for the five largest and five smallest event-minus-control outcomes were inspected: TXN, NFLX, ORCL, TGT, WFC, AAPL, HD, LOW, MCD and AMZN. All ten explicitly state completed sale/issuance of notes. Two-tag copies were combined rather than counted twice. No return-dependent exclusion or rule change was made.

This audit verifies the excerpt-level transaction type, not absence of other corporate news, prior public announcements, acquisition uses omitted from the excerpt, or leverage effects. Several transactions explicitly reference earlier underwriting dates or previously announced offers. Entry after the filing is therefore conservatively public but does not capture the initial announcement reaction. Bank funding and corporate funding remain pooled as preregistered; differences are a possible source of heterogeneity, not a post-outcome reason to select a favorable subgroup.

The internal covered-call engine uses its existing “routine” column value as an eligibility flag for these rows. Here it means the new frozen debt screen passed; it does not apply the old CEO/CFO routine classifier or infer that all debt is economically harmless. The published results call the group completed_debt.

After the validation baseline was saved, all seven usable 21-session excerpts were checked: ACN, AMZN, CRM, LLY, META, MRK and NOW. Each explicitly describes completed issuance/sale of notes. No changes were made to eligibility, matching, construction or parameters. This remains an excerpt audit rather than a full filing/news-history audit.

The financing-only ordinary sensitivity builds its financing exclusion dates from the same source-window transaction audit. It does not establish complete financing-tag coverage outside the window boundaries. Its all-disclosure entry exclusion still uses the full padded API calendar. The primary all-disclosure ±30-day comparison uses that full API calendar throughout and is unaffected by this secondary boundary limitation.
