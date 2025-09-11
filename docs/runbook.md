# File: docs/runbook_phase0.md
# Runbook — Phase 0 MVP (FRED-only)

## Prereqs
- Python 3.10+
- Fill `.env` from `.env.example`
- Edit `src/wequo/config.yml` as needed

## Install
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python scripts/run_weekly.py
```
Output directory: `data/output/YYYY-MM-DD/` with:
- `fred.csv`
- `qa_report.md` (freshness & counts)
- `package_summary.json` (compact analytics)
- `prefill_notes.md` (bullets for authors)

## Notes
- Ensure `FRED_API_KEY` is set. If missing/invalid, the run will error.
- To add/change series, edit `series_ids` in `config.yml`.

---
# File: README_PHASE0.md
## WeQuo — Phase 0 (Foundations & MVP, FRED-only)
This is a minimal end-to-end pipeline that ingests **FRED** series, performs basic validation, and emits a weekly author-ready package.

### Quick start
1. `cp .env.example .env` and fill keys.
2. Edit `src/wequo/config.yml` (choose FRED `series_ids`).
3. `pip install -r requirements.txt`
4. `python scripts/run_weekly.py`

### Acceptance targets (from ROADMAP)
- Connector runs and stores outputs under `data/output/` ✅
- Validation produces a human-readable `qa_report.md` ✅
- Aggregator emits a single `package_summary.json` + `prefill_notes.md` that an author can use to fill `TEMPLATE.MD` within 2 hours ✅
