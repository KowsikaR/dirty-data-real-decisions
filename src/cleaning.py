from pathlib import Path
import numpy as np
import pandas as pd

ALIASES = {
    "case_id": ["case_id", "caseid", "id", "case number"],
    "intake_date": ["intake_date", "intake", "opened_at", "open_date", "created_at"],
    "closure_date": ["closure_date", "closed_at", "close_date", "resolved_at"],
    "category": ["category", "case_category", "type", "case type"],
}

def _column_map(columns):
    normalized = {str(c).strip().casefold().replace(" ", "_"): c for c in columns}
    result = {}
    for target, aliases in ALIASES.items():
        for alias in aliases:
            key = alias.casefold().replace(" ", "_")
            if key in normalized:
                result[target] = normalized[key]
                break
    return result

def generate_sample(path, n=15000, seed=42):
    """Create deterministic synthetic data with intentionally documented defects."""
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2018-01-01")
    intake = start + pd.to_timedelta(rng.integers(0, 365 * 7, n), unit="D")
    year_effect = (intake.year - 2018) * 2.0
    durations = np.maximum(1, rng.normal(18 + year_effect, 9, n).round().astype(int))
    categories = rng.choice(["Billing", "Technical", "Account", "Complaint", "Request"], n)
    closure = intake + pd.to_timedelta(durations, unit="D")
    date_formats = rng.choice(["iso", "dmy", "mdy"], n)
    # Keep slash-formatted sample dates unambiguous: real exports often lack
    # this luxury, in which case the documented day-first policy applies.
    date_formats = np.where((date_formats != "iso") & ((intake.day <= 12) | (closure.day <= 12)), "iso", date_formats)
    def fmt(date, style):
        if style == "iso": return date.strftime("%Y-%m-%d")
        if style == "dmy": return date.strftime("%d/%m/%Y")
        return date.strftime("%m/%d/%Y")
    df = pd.DataFrame({
        "case_id": [f" C-{i:05d} " for i in range(n)],
        "intake_date": [fmt(d, s) for d, s in zip(intake, date_formats)],
        "closure_date": [fmt(d, s) for d, s in zip(closure, date_formats)],
        "category": categories,
    })
    # Inject realistic defects without making the sample unusable.
    df.loc[10:29, "category"] = [" billing " if i % 2 else "BILLING" for i in range(20)]
    df.loc[100:109, "category"] = np.nan
    df.loc[200:204, "closure_date"] = np.nan
    df.loc[300:304, "closure_date"] = "not-a-date"
    df.loc[400:404, "closure_date"] = df.loc[400:404, "intake_date"].values
    df.loc[500:504, "closure_date"] = df.loc[500:504, "intake_date"].values
    # These are physically impossible: closure before intake.
    for i in range(600, 605):
        df.loc[i, "closure_date"] = (intake[i] - pd.Timedelta(days=3)).strftime("%Y-%m-%d")
    df = pd.concat([df, df.iloc[[20, 21, 22]].copy()], ignore_index=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path

def parse_dates(series):
    values = series.astype("string").str.strip()
    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    iso = values.str.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}", na=False)
    parsed.loc[iso] = pd.to_datetime(values.loc[iso], errors="coerce", yearfirst=True)
    rest = ~iso
    # Resolve unambiguous slash dates per row. For 01/02/2020-style
    # ambiguity, use day-first consistently and document that policy.
    parts = values.str.extract(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$")
    first = pd.to_numeric(parts[0], errors="coerce")
    second = pd.to_numeric(parts[1], errors="coerce")
    month_first = rest & first.le(12) & second.gt(12)
    day_first = rest & ~month_first
    parsed.loc[month_first] = pd.to_datetime(values.loc[month_first], errors="coerce", dayfirst=False)
    parsed.loc[day_first] = pd.to_datetime(values.loc[day_first], errors="coerce", dayfirst=True)
    return parsed

def clean_data(raw):
    log = []
    df = raw.copy()
    mapping = _column_map(df.columns)
    missing = [x for x in ALIASES if x not in mapping]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")
    df = df.rename(columns={source: target for target, source in mapping.items()})
    for col in ["case_id", "category"]:
        df[f"{col}_raw"] = df[col]
        df[col] = df[col].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    df["case_id"] = df["case_id"].str.upper()
    df["category"] = df["category"].str.casefold()
    category_map = {"billing": "Billing", "technical": "Technical", "account": "Account",
                    "complaint": "Complaint", "request": "Request"}
    df["category"] = df["category"].map(category_map).fillna(df["category"].str.title())
    df.loc[df["category"].isin(["<NA>", "Nan", "None", ""]), "category"] = "Unknown"
    df["intake_date_raw"] = df["intake_date"]
    df["closure_date_raw"] = df["closure_date"]
    df["intake_date"] = parse_dates(df["intake_date"])
    df["closure_date"] = parse_dates(df["closure_date"])
    df["date_parse_failed"] = (df["intake_date"].isna() & df["intake_date_raw"].notna()) | (df["closure_date"].isna() & df["closure_date_raw"].notna())
    df["invalid_interval"] = df["intake_date"].notna() & df["closure_date"].notna() & (df["closure_date"] < df["intake_date"])
    df["closure_duration_days"] = (df["closure_date"] - df["intake_date"]).dt.days
    df.loc[df["invalid_interval"] | df["date_parse_failed"], "closure_duration_days"] = np.nan
    df["_exact_duplicate"] = df.duplicated(keep="first")
    df["_duplicate_case_id"] = df["case_id"].notna() & df["case_id"].duplicated(keep="first")
    reasons = []
    for idx, row in df.iterrows():
        r = []
        if row["_exact_duplicate"]: r.append("exact duplicate row")
        elif row["_duplicate_case_id"]: r.append("duplicate case_id; representative retained")
        if pd.isna(row["case_id"]): r.append("missing case_id")
        if row["date_parse_failed"]: r.append("unparseable date")
        if row["invalid_interval"]: r.append("closure before intake")
        reasons.append("; ".join(r) or "retained")
    log = pd.DataFrame({"source_row": np.arange(1, len(df)+1), "case_id": df["case_id"], "action": reasons})
    analysis = df[~df["_exact_duplicate"] & ~df["_duplicate_case_id"] & df["case_id"].notna()].copy()
    return analysis, log, mapping