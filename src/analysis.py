from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

def summarize(df):
    valid = df[df["closure_duration_days"].notna()].copy()
    by_year = valid.assign(year=valid["intake_date"].dt.year).groupby("year").agg(
        cases=("case_id", "count"), median_days=("closure_duration_days", "median"),
        mean_days=("closure_duration_days", "mean")).reset_index()
    by_category = valid.groupby("category").agg(
        cases=("case_id", "count"), median_days=("closure_duration_days", "median"),
        mean_days=("closure_duration_days", "mean")).reset_index().sort_values("median_days", ascending=False)
    return by_year, by_category

def make_figures(df, out_dir):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    by_year, by_category = summarize(df)
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(8, 4.5)); ax.plot(by_year.year, by_year.median_days, marker="o"); ax.set(title="Median closure time by intake year", xlabel="Intake year", ylabel="Days"); fig.tight_layout(); fig.savefig(out_dir/"closure_time_by_year.png", dpi=140); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4.5)); ax.bar(by_year.year.astype(str), by_year.cases); ax.set(title="Case count by intake year", xlabel="Intake year", ylabel="Cases"); fig.tight_layout(); fig.savefig(out_dir/"case_count_by_year.png", dpi=140); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4.5)); ax.barh(by_category.category, by_category.median_days); ax.invert_yaxis(); ax.set(title="Median closure time by category", xlabel="Days"); fig.tight_layout(); fig.savefig(out_dir/"closure_time_by_category.png", dpi=140); plt.close(fig)
    missing = df.isna().sum().sort_values(ascending=False); missing = missing[missing > 0]
    fig, ax = plt.subplots(figsize=(8, 4.5)); (ax.bar(missing.index.astype(str), missing.values) if len(missing) else ax.text(.5, .5, "No missing values", ha="center")); ax.set(title="Missing values by column", ylabel="Missing cells"); ax.tick_params(axis="x", rotation=60); fig.tight_layout(); fig.savefig(out_dir/"missing_value_summary.png", dpi=140); plt.close(fig)
    return by_year, by_category