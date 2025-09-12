Shortform Logo

Intro image (optional)

Get an instant summary of this page, plus context, alternative views, and links to learn more.

---
title: "Weekly Brief — Risk & Opportunity"
issue: "YYYY-W##"
date: ""
description: "Email-first, investor-focused weekly brief. One actionable page with appendices for data and methodology."
---

# Weekly Brief — Risk & Opportunity

> Issue: `YYYY-W##`  
> Date: _(YYYY-MM-DD)_

This is an email-first, one-page weekly brief designed to help investors and market professionals make faster, better decisions. Prioritize clear calls, conviction, sizing, and time horizon. Keep the main email to ~200-350 words; appendices may contain charts, data tables, and methods.

## TL;DR

- Single paragraph directional call and why. Include conviction (High/Medium/Low), horizon (days/weeks/months), and suggested percent tilt or size.

## 1) Quick Positioning 

- Top-level tactical position: long/short/tilt/cash with simple sizing guidance (e.g., "Overweight US Large Caps — 3% tactical tilt vs benchmark").
- Top 3 catalysts this week that would change the call (with triggers & time windows).
- Immediate risk controls (stop, hedge, liquidity target).

## 2) Market Signals (2–4 bullets — data + read)

- Macro & policy: latest central bank notes / rates / funding (one sentence each). Add the short data cite (FRED/Treasury). Example: "US payrolls miss; Fed pause read: Medium conv; equity risk-on fade if NFP < 150k." 
- Liquidity & credit: spreads, repo, FX stress (one-line signal + why it matters).
- Market internals: breadth, vol, flows (ETF flows, macro hedges). Flag any divergence.

## 3) Opportunities & Watchlist (3–6 short items)

For each item use this mini-structure (1–3 lines):
- Ticker/Instrument | Thesis (1 sentence) | Catalyst & horizon | Recommended instrument & sizing

Examples:
- XLE | Oil demand re-accel vs OPEC cuts; catalyst: weekly inventories (1–3w) | Trade: long XLE 2–3% tactical
- EURUSD | Soft Euro PMI vs US resilience; catalyst: ECB minutes (days) | Trade: small short via options or mini FX forwards

## 4) Top Risks & Contingency Triggers

- Rapid escalation: list 3 events that require immediate de-risking and specific actions (e.g., "Emerging market FX shock — reduce EM equity exposure to 0.5x within 24h").
- Model/technical risks (false signals, data noise) and what anchor metrics to check.

## 5) Trade Ideas (priority 3 — operational)

Provide up to 3 prioritized trades, each with: ticket/ticker, direction, size (small/medium/large or %), entry, stop/hedge, time horizon, and exit rules.

1) Title — e.g., "US Small Cap Defensive Pair"
- Ticker(s): IWM / SPY pair
- Direction & size: long IWM vs short SPY — small (1% net beta) 
- Entry: IWM relative weakness > 1 std dev intraday
- Stop/Hedge: close below recent support or 3% stop; hedge with short-dated put if large position
- Horizon: 1–4 weeks

2) Title
- ...

3) Title
- ...

## 6) Appendix — Data, Sources & Methods (expand as needed)

- Links to data visualizations and raw data.
- Key charts/tables: Market breadth, 2s10s, credit spreads, FX vols, ETF flows (embed or link to images saved in `data/output/YYYY-MM-DD/`).
- Methods: how deltas/anomalies are calculated (z-scores, rolling windows). Keep reproducible code references (module names and functions).

## Pipeline integration & provenance

- Run the pipeline: `scripts/run_weekly.py` to generate the data package for the issue. Attach or link the generated folder in `data/output/YYYY-MM-DD/`.
- Provenance & package metadata: include `package_summary.json` and `analytics_summary.json` from the data package; optionally reference `src/wequo/metadata.py` for provenance fields and `package_summary.json` keys.
- QA: attach `qa_report.md` and surface any missing-data or validation flags in the email if present.
- Authoring tools: the web app (`run_web_app.py`) and CLI (`src/wequo/tools/cli.py`) can preview packages and generate a pre-filled markdown — use them to speed authoring and ensure consistency.

---

### Author checklist (use before publishing)

1. Keep the main email to one screen (200–350 words). Put detailed charts in appendices.
2. Add clear conviction (High/Medium/Low) and horizon for every call.
3. Include tickets/ISINs and concrete sizing where relevant.
4. Cite raw data sources and attach charts or link to `data/output/YYYY-MM-DD/` package.
5. Run QA pipeline to ensure no missing data; attach `qa_report.md`.
6. Spellcheck and sanity-check numbers (percentages, dates, ticker names).

### Example quick-fill (paste into email body)

Subject: Weekly Market Brief — YYYY-W## | Main call (High Conv)

TL;DR: [Single-sentence call — 25 words]

Positioning: [One-line tactical action — size]

Signals: 1) [Macro], 2) [Liquidity/credit], 3) [Flows/vol]

Top Trade: [Ticker — direction — size — entry — stop — horizon]

Appendix: data snapshot & charts → `data/output/YYYY-MM-DD/` 

---

Notes:
- Use this template as the email-first canonical brief. Expand appendices for PMs and analysts who need data and reproducibility.
- For weekly publication, populate `issue` and `date`, run the pipeline (`scripts/run_weekly.py`) to generate the data package, and attach charts/qa from `data/output/YYYY-MM-DD/`.