import pandas as pd

def assess(raw, cleaned, log):
    issues = [
        ("Rows loaded", len(raw), "all source rows"),
        ("Columns loaded", len(raw.columns), "source schema"),
        ("Exact duplicate rows", int(raw.duplicated().sum()), "excluded from analysis"),
        ("Repeated case IDs", int(log["action"].str.contains("duplicate case_id", na=False).sum()), "representative retained"),
        ("Missing values", int(raw.isna().sum().sum()), "retained where possible; not imputed"),
        ("Date parse failures", int(cleaned["date_parse_failed"].sum()), "no duration calculated"),
        ("Impossible intervals", int(cleaned["invalid_interval"].sum()), "no duration calculated"),
        ("Rows used for case analysis", len(cleaned), "deduplicated, identified cases"),
        ("Valid duration records", int(cleaned["closure_duration_days"].notna().sum()), "used for duration metrics"),
    ]
    return pd.DataFrame(issues, columns=["check", "count", "interpretation"])