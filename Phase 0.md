**Phase 0 Foundations \& MVP (REWRITTEN)**



**GOAL**

Deliver a minimal end-to-end pipeline that ingests 3-5 core data sources, validates data, and produces an author-ready weekly p

This document is the Phase 0 specification. It is intentionally prescriptive: small scope, clear acceptance criteria, and concrete outputs that let an author produce a publishable weekly brief with minimal manual work.





**Acceptance criteria (Phase 0)**

A1: Pipeline ingests at least 3 data sources (one is FRED) and stores raw versioned outputs.

A2: Validation runs for each dataset and produces a validation\_report; invalid datasets are excluded from the weekly package.

A3: Aggregator produces a ZIP package per week containing: data/ (CSV+JSON), charts/, summary.md (author draft), and validation\_reports/.

A4: Author can open summary.md, edit, and approve in under 60 minutes to send via an email provider.

A5: Basic monitoring: alerts for connector failure and a dashboard metric for data freshness SLA.





**Exact Phase 0 scope**

Sources to ingest (minimum 3):

i. FRED (macroeconomic time series)

ii. Market data (Alpha Vantage or Yahoo Finance) - indices, major FX pairs, commodities

iii. ACLED (geopolitical events)

Optional 4: IMF WEO or UN Contrade (if time permits)



Deliverables:

raw/ storage with versioned downloads and metadata

normalized/ storage with JSONL/CSV and schema version

Validation runner and sample JSON Schemas for the dataset types

Aggregator script that produces weekly ZIP and summary.md draft

Minimal author preview (static HTML or markdown preview file)





**Minimal pipeline contract (developer-facing)**

For each connector implement:

Config: YAML entry describing endpoint, dataset\_id, expected\_frequency, required\_columns, and freshness\_window (in hours).

Download behavior: write raw file to raw/(source)/(YYYY}/{MM}/{DD}/{dataset\_id).(ext) and write metadata JSON next to it.

Validation: run JSON Schema + freshness check; produce validation\_report\_{source)\_(date).json.

Normalization: convert into a canonical JSONL format depending on type (time\_series, market\_quote, event).

Packaging: normalized outputs stored under normalized/(source)/; aggregator reads normalized/.

Errors: connectors should exit non-zero on repeated failures (after N retries) and emit a machine-readable error artifact in

errors/{source}/{timestamp).json.





**Validation rules (M0.4)**

Dataset types \& minimal schema fields:

time\_series: series\_id, country (optional), metric, unit, frequency, observations\[{date, value}]

omarket\_quote: timestamp, ticker, open, high, low, close, volume, currency

event: event\_date, country, event\_type, summary, source\_url

Freshness: each dataset config has freshness\_window, validator fails the dataset if latest observation is older than freshness\_window.

Unit handling: if currency conversion is needed, include conversion\_rate metadata but do not auto-convert for Phase O unless trivial (USD market tickers preferred).

Anomaly checks: null\_rate < 5%, no duplicate timestamps for time series, basic outlier detection (z-score > 6 flagged).

Validation output: validation\_report includes pass:boolean, errors:\[...], warnings:\[...], data\_range:(min\_date,max\_date), row\_count.





**Aggregator behavior (M0.5)**

Input: normalized datasets covering the weekly window (configurable, default: Monday-Sunday UTC).

Output package (weekly-package\_(YYYY)-(WW).zip) contents:

data/: CSV and JSON exports for each normalized dataset included

charts/: PNG sparklines for selected indicators (6-8)-small, author-friendly

summary.md: author draft with a fixed template:

Title, date, TL;DR (3 bullets)

Top 3 risks (each 2-3 lines, data links)

Top 3 opportunities (each 2-3 lines, data links)

Appendix: data sources and key tables

validation\_reports/: JSON reports for included datasets

Aggregator acceptance: zip exists, summary.md populated with automated bullets (templates + data-driven facts), and charts generated.





**Author workflow**

1\. Aggregator runs and writes package to publish/weekly-package\_(YYYY)-(WW).zip and an HTML preview (publish/preview\_{YYYY)-(WW).html).

2\. Author opens summary.md (or HTML preview), edits language and decision guidance, and marks the draft as approved.

3\. On approval, a simple script sends the HTML to a configured email provider (SendGrid/Mailgun/SES) or exports to CMS.

Phase 0 target: author edit+approve < 60 minutes.



**Monitoring \& alerts**

Send an alert if any connector fails 3 times in a row or if data freshness SLA drops below threshold for any required dataset.

Emit metrics: last\_success\_(source), freshness\_(source) (hours since last observation), package\_success\_rate.



**Minimal tech choices \& dev notes**

Language: Python 3.10 (connectors, validator, aggregator)

Storage: S3-compatible (AWS S3 or MinIO locally). For Phase 0, local filesystem under ./data/ is acceptable.

Scheduler: GitHub Actions scheduled workflow or cron on a small VM.

Email: SendGrid/Mailgun for Phase 0 (provider choice configurable via env).

Tests: pytest for unit tests and small integration smoke tests.

Developer quickstart (local):

1\. Create a virtualenv and install requirements.

2\. Configure config/sources.yml with API keys via env vars.

3\. Run connector: python -m connectors.alpha\_vantage (example)

4\. Run validation: python -m validator run --source alpha\_vantage

5\. Run aggregator: python -m aggregator build --week YYYY-WW





**Milestones \& immediate next steps**

M0.1: Kickoff \& roles (not started)

M0.2: Sources selected (DONE)

M0.3: Implement connectors (start with one new connector + FRED)

M0.4: Implement validation runner and sample JSON Schemas

M0.5: Implement aggregator script and generate first sample package

M0.6: Dry-run, author feedback, iterate

Immediate next tactical choices (pick one):

A) Scaffold repo and implement starter Alpha Vantage connector + tests

B) Implement aggregator that reads existing FRED output and produces a sample weekly package (fast dry-run)

C) Build validation runner and sample JSON Schema for time\_series and market\_quote types

Author: Phase 0 rewritten to match the clarified GOAL. Marked the rewrite task done in the Phase 0 todo list.

