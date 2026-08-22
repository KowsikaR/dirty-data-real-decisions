# Dirty Data, Real Decisions

A reproducible Python data-quality assessment and operational analysis of case closure times. The project is deliberately conservative: it separates defects in the recording from changes in the underlying reality, answers only what the data supports, and states what it cannot answer.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_analysis.py
```

The first run creates `data/raw/sample_cases.csv` (15,000 deterministic synthetic rows) because no input CSV is supplied. It is labeled sample data and must not be presented as production evidence. To use real data, put one CSV in `data/raw/` and run the command again.

## What it does

`run_analysis.py` loads the raw CSV, records a row-level cleaning log, normalizes text and dates, identifies duplicate and impossible records, calculates closure duration, writes a cleaned CSV, creates four PNG charts, and generates:

- `reports/data_quality_report.md`
- `reports/operational_answers.md`
- `reports/cleaning_log.csv`
- `outputs/figures/closure_time_by_year.png`
- `outputs/figures/case_count_by_year.png`
- `outputs/figures/closure_time_by_category.png`
- `outputs/figures/missing_value_summary.png`

The analysis answers:

1. Whether closure times changed over intake years.
2. Which normalized categories have the longest median closure time.
3. What caused any increase. This is explicitly reported as **“Cannot be answered reliably from the available data.”** when no causal/explanatory fields are present. A time trend is not evidence of a cause.

## Input schema

The loader recognizes common names case-insensitively: `case_id`, `intake_date`, `closure_date`, and `category` (aliases include `id`, `opened_at`, `closed_at`, `type`). Extra columns are retained. Date parsing supports ISO, day-first, month-first, and common timestamp formats. Ambiguous dates are not silently guessed when they cannot be resolved.

## Project structure

```text
.
├── data/raw/                  # Put the source CSV here
├── data/processed/            # Cleaned output
├── notebooks/analysis.ipynb   # Reproducible walkthrough
├── outputs/figures/            # Generated charts
├── reports/                   # Quality and decision outputs
├── src/cleaning.py
├── src/quality_check.py
├── src/analysis.py
├── run_analysis.py
├── DECISIONS.md
├── AI-USAGE.md
└── requirements.txt
```

## Limitations

The included sample is synthetic. The pipeline cannot establish why closure times changed without fields such as staffing, workload, priority, process changes, or service-level policy. Duplicate identity is handled conservatively; conflicting duplicate rows are retained in the cleaning log and only one representative is used for duration analysis. Missing closure dates and invalid dates cannot contribute to duration summaries.

## GitHub and ZIP export

```bash
git init
git add .
git commit -m "Add dirty data case analysis"
git branch -M main
git remote add origin https://github.com/<user>/<repository>.git
git push -u origin main
```

From the parent directory, export with:

```bash
zip -r dirty-data-real-decisions.zip dirty-data-real-decisions/
```
