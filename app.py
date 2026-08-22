from pathlib import Path
from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.analysis import summarize
from src.cleaning import clean_data, generate_sample
from src.quality_check import assess

ROOT = Path(__file__).parent
SAMPLE_PATH = ROOT / "data/raw/sample_cases.csv"

st.set_page_config(page_title="Dirty Data, Real Decisions", page_icon="D", layout="wide")


def read_sample():
    if not SAMPLE_PATH.exists():
        generate_sample(SAMPLE_PATH)
    return pd.read_csv(SAMPLE_PATH)


def analyze(raw):
    cleaned, log, mapping = clean_data(raw)
    quality = assess(raw, cleaned, log)
    by_year, by_category = summarize(cleaned)
    return {
        "raw": raw,
        "cleaned": cleaned,
        "log": log,
        "quality": quality,
        "by_year": by_year,
        "by_category": by_category,
        "mapping": mapping,
    }


def chart_trend(data):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(data["year"], data["median_days"], marker="o", linewidth=2)
    ax.set(title="Median closure time by intake year", xlabel="Intake year", ylabel="Days")
    fig.tight_layout()
    return fig


def chart_counts(data):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(data["year"].astype(str), data["cases"])
    ax.set(title="Case count by intake year", xlabel="Intake year", ylabel="Cases")
    fig.tight_layout()
    return fig


def chart_categories(data):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ordered = data.sort_values("median_days")
    ax.barh(ordered["category"], ordered["median_days"])
    ax.set(title="Median closure time by category", xlabel="Days", ylabel="")
    fig.tight_layout()
    return fig


def render_quality(result):
    st.title("Data Quality")
    quality = result["quality"]
    cols = st.columns(5)
    values = {
        "Total rows": len(result["raw"]),
        "Total columns": len(result["raw"].columns),
        "Missing values": int(result["raw"].isna().sum().sum()),
        "Duplicate records": int(result["quality"].loc[result["quality"]["check"] == "Exact duplicate rows", "count"].iloc[0]),
        "Invalid date records": int(result["quality"].loc[result["quality"]["check"].isin(["Date parse failures", "Impossible intervals"]), "count"].sum()),
    }
    for col, (label, value) in zip(cols, values.items()):
        col.metric(label, f"{value:,}")
    st.subheader("Data quality summary")
    st.dataframe(quality, use_container_width=True, hide_index=True)


def render_trend(result):
    st.title("Closure Trend")
    by_year = result["by_year"]
    if by_year.empty:
        st.warning("There are no valid closure durations to chart.")
        return
    st.pyplot(chart_trend(by_year), clear_figure=True)
    st.pyplot(chart_counts(by_year), clear_figure=True)
    first, last = by_year.iloc[0], by_year.iloc[-1]
    direction = "increased" if last["median_days"] > first["median_days"] else "did not increase"
    st.info(
        f"Median closure time {direction} from {first['median_days']:.1f} days in "
        f"{int(first['year'])} to {last['median_days']:.1f} days in {int(last['year'])}. "
        "This is descriptive evidence, not proof of a cause."
    )


def render_categories(result):
    st.title("Category Analysis")
    categories = result["by_category"]
    if categories.empty:
        st.warning("There are no valid closure durations to summarize.")
        return
    st.pyplot(chart_categories(categories), clear_figure=True)
    st.subheader("Category summary")
    st.dataframe(categories, use_container_width=True, hide_index=True)


def render_questions(result):
    st.title("Operational Questions")
    by_year, categories = result["by_year"], result["by_category"]
    st.subheader("Question 1")
    st.write("Have case closure times increased over the years?")
    if len(by_year) >= 2:
        direction = "increased" if by_year.iloc[-1]["median_days"] > by_year.iloc[0]["median_days"] else "did not increase"
        st.success(f"Answer: closure times {direction}. Confidence: moderate.")
    else:
        st.warning("Insufficient valid year-level data to answer this question.")
    st.subheader("Question 2")
    st.write("Which case categories take the longest time to close?")
    if not categories.empty:
        top = categories.iloc[0]
        st.success(f"Answer: {top['category']} has the highest median closure time at {top['median_days']:.1f} days. Confidence: moderate.")
    else:
        st.warning("No valid category durations are available.")
    st.subheader("Question 3")
    st.write("What caused the increase in closure time?")
    st.error("Cannot be answered reliably from the available data.")
    st.caption(
        "The export contains dates, identifiers, and categories, but no staffing, "
        "workload/backlog, priority, policy, or process-change fields."
    )


def render_reports(result):
    st.title("Reports")
    quality_md = result["quality"].to_markdown(index=False)
    categories = result["by_category"]
    by_year = result["by_year"]
    trend = "increased" if len(by_year) >= 2 and by_year.iloc[-1]["median_days"] > by_year.iloc[0]["median_days"] else "did not increase"
    top = categories.iloc[0]["category"] if not categories.empty else "unavailable"
    answers_md = (
        "# Operational answers\n\n"
        f"## Question 1\n\nClosure times **{trend}** over the years.\n\n"
        f"## Question 2\n\nThe category with the longest median closure time is **{top}**.\n\n"
        "## Question 3\n\n**Cannot be answered reliably from the available data.**\n"
    )
    st.subheader("Data Quality Report")
    st.markdown(quality_md)
    st.subheader("Operational Answers")
    st.markdown(answers_md)
    csv_bytes = result["cleaned"].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download cleaned CSV",
        data=csv_bytes,
        file_name="cleaned_cases.csv",
        mime="text/csv",
        type="primary",
    )


def main():
    st.sidebar.title("Dirty Data")
    st.sidebar.caption("Real decisions need honest evidence.")
    page = st.sidebar.radio(
        "Navigate",
        ["Home", "Data Quality", "Closure Trend", "Category Analysis", "Operational Questions", "Reports"],
    )
    uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if uploaded is not None:
        st.sidebar.caption(f"Selected: {uploaded.name}")
    if st.sidebar.button("Run Analysis", type="primary", use_container_width=True):
        try:
            raw = pd.read_csv(uploaded) if uploaded is not None else read_sample()
            st.session_state["result"] = analyze(raw)
            st.session_state["source_name"] = uploaded.name if uploaded is not None else "sample_cases.csv"
            st.session_state["is_sample"] = uploaded is None
            st.sidebar.success("Analysis complete")
        except Exception as exc:
            st.sidebar.error(f"Could not analyze this CSV: {exc}")
    result = st.session_state.get("result")
    if page == "Home":
        st.title("Dirty Data, Real Decisions")
        st.write(
            "Assess a messy case-management export, make the cleaning decisions visible, "
            "and answer operational questions about case closure times."
        )
        st.info("Upload a CSV in the sidebar, then select Run Analysis. With no upload, the documented synthetic sample is used.")
        if result:
            st.success(f"Showing results from {st.session_state['source_name']}.")
            if st.session_state.get("is_sample"):
                st.caption("This is synthetic sample data, not production evidence.")
        else:
            st.markdown("Use the sidebar to start an analysis.")
    elif result is None:
        st.title(page)
        st.info("Run an analysis from the sidebar to populate this page.")
    elif page == "Data Quality":
        render_quality(result)
    elif page == "Closure Trend":
        render_trend(result)
    elif page == "Category Analysis":
        render_categories(result)
    elif page == "Operational Questions":
        render_questions(result)
    elif page == "Reports":
        render_reports(result)


if __name__ == "__main__":
    main()