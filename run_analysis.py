from pathlib import Path
import pandas as pd
from src.cleaning import generate_sample, clean_data
from src.quality_check import assess
from src.analysis import make_figures

ROOT = Path(__file__).parent
RAW_DIR, PROCESSED, REPORTS, FIGURES = ROOT/"data/raw", ROOT/"data/processed", ROOT/"reports", ROOT/"outputs/figures"

def pick_input():
    files = sorted(RAW_DIR.glob("*.csv"))
    real_files = [file for file in files if file.name != "sample_cases.csv"]
    if real_files:
        return real_files[0]
    if not files:
        path = RAW_DIR/"sample_cases.csv"; generate_sample(path)
        print(f"No input CSV found; generated clearly labeled sample data at {path}")
        return path
    return files[0]

def main():
    REPORTS.mkdir(exist_ok=True); PROCESSED.mkdir(exist_ok=True)
    path = pick_input()
    raw = pd.read_csv(path)
    cleaned, log, mapping = clean_data(raw)
    quality = assess(raw, cleaned, log)
    cleaned.to_csv(PROCESSED/"cleaned_cases.csv", index=False)
    log.to_csv(REPORTS/"cleaning_log.csv", index=False)
    quality.to_csv(REPORTS/"quality_checks.csv", index=False)
    by_year, by_category = make_figures(cleaned, FIGURES)
    quality.to_markdown(REPORTS/"data_quality_report.md", index=False)
    latest = by_year.iloc[-1] if len(by_year) else None
    first = by_year.iloc[0] if len(by_year) else None
    trend = "increased" if latest is not None and latest.median_days > first.median_days else "did not increase"
    with open(REPORTS/"operational_answers.md", "w", encoding="utf-8") as f:
        f.write("# Operational answers\n\n")
        f.write("## Question 1 — Have case closure times increased over the years?\n\n")
        f.write(f"**Answer: {trend}. Confidence: moderate.** The comparison uses median closure duration among valid, deduplicated records by intake year. ")
        f.write("This is descriptive evidence and does not establish a cause.\n\n")
        f.write("## Question 2 — Which case categories take longest to close?\n\n")
        if len(by_category):
            f.write(f"**Answer: {by_category.iloc[0]['category']}. Confidence: moderate.** It has the highest median duration ({by_category.iloc[0]['median_days']:.1f} days) among categories with valid durations. Small groups should be treated cautiously.\n\n")
            f.write(by_category.to_markdown(index=False) + "\n\n")
        else: f.write("**Answer: unavailable.** No valid durations exist.\n\n")
        f.write("## Question 3 — What caused the increase in closure time?\n\n")
        f.write("**Cannot be answered reliably from the available data. Confidence: high.** The export contains dates, identifiers, and categories, but no staffing, workload/backlog, priority, policy, process-change, or channel variables. The data can show that a change occurred; it cannot identify its operational cause.\n\n")
        f.write("### What would be needed\n\nStaffing and queue history, incoming volume, priority/SLA, workflow timestamps, policy/process-change dates, and a stable case-level audit history.\n")
    print("\nDirty Data, Real Decisions")
    print(f"Input: {path.name} | Raw rows: {len(raw):,} | Analyzed cases: {len(cleaned):,}")
    print(f"Valid durations: {cleaned['closure_duration_days'].notna().sum():,} | Date/interval issues: {int(cleaned['date_parse_failed'].sum()+cleaned['invalid_interval'].sum()):,}")
    print(f"Question 1: closure times {trend}. Question 3: cannot be answered reliably from the available data.")
    print("Reports, cleaned data, cleaning log, and figures generated successfully.")

if __name__ == "__main__":
    main()