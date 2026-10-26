import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from urllib.parse import quote
from datetime import date

# ---------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------
st.set_page_config(
    page_title="Public Attention Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------
# 2. TOPIC CONFIGURATION
# ---------------------------------
topics = {
    "Chandrayaan-3": {"article": "Chandrayaan-3", "start": "20230701", "end": "20231031"},
    "ChatGPT": {"article": "ChatGPT", "start": "20221201", "end": "20231231"},
    "2022 FIFA World Cup": {"article": "2022 FIFA World Cup", "start": "20221001", "end": "20230131"},
    "COVID-19 Pandemic": {"article": "COVID-19 pandemic", "start": "20200101", "end": "20231231"},
    "2024 Summer Olympics": {"article": "2024 Summer Olympics", "start": "20240701", "end": "20240930"},
    "2024 Indian General Election": {"article": "2024 Indian general election", "start": "20240401", "end": "20240630"},
    "BGMI": {"article": "Battlegrounds Mobile India", "start": "20210501", "end": "20231231"},
    "Tesla": {"article": "Tesla, Inc.", "start": "20200101", "end": "20231231"},
    "Dangal Movie": {"article": "Dangal (2016 film)", "start": "20161001", "end": "20171231"},
}

# ---------------------------------
# 3. VISUAL STYLING
# ---------------------------------
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.7rem; padding-bottom: 2.5rem;}
    [data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.20);
        padding: 14px 16px;
        border-radius: 12px;
    }
    div[data-testid="stAlert"] {border-radius: 10px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------
# 4. DATA COLLECTION
# ---------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_data(article, start, end):
    """Fetch daily English Wikipedia pageviews for one article."""
    encoded_article = quote(article.replace(" ", "_"), safe="")
    url = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"en.wikipedia.org/all-access/user/{encoded_article}/daily/{start}/{end}"
    )
    response = requests.get(
        url,
        headers={"User-Agent": "PublicAttentionLifecycleStudentProject/1.0 (Educational Research)"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    items = payload.get("items", [])
    if not items:
        raise ValueError("No Wikipedia pageview records were returned. Try another topic or date range.")

    df = pd.DataFrame(items)
    if not {"timestamp", "views"}.issubset(df.columns):
        raise ValueError("The Wikipedia API response is missing required fields.")
    df = df[["timestamp", "views"]].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y%m%d%H", errors="coerce")
    df["views"] = pd.to_numeric(df["views"], errors="coerce")
    df = df.dropna(subset=["timestamp", "views"])
    df = df.drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    if len(df) < 8:
        raise ValueError("Too few records for a useful 7-record moving average. Choose a longer date range.")
    return df

# ---------------------------------
# 5. DATA ANALYSIS
# ---------------------------------
def analyze_data(df):
    """Calculate moving average, trend phases, peak, and period changes."""
    df = df.copy().sort_values("timestamp").reset_index(drop=True)
    df["moving_avg"] = df["views"].rolling(window=7, min_periods=7).mean()
    df["attention_change"] = df["moving_avg"].diff()

    def detect_phase(change):
        if pd.isna(change):
            return "Insufficient Data"
        if change > 0:
            return "Growth"
        if change < 0:
            return "Decline"
        return "Stable"

    df["phase"] = df["attention_change"].apply(detect_phase)
    peak_index = df["views"].idxmax()
    peak_views = int(df.loc[peak_index, "views"])
    peak_date = df.loc[peak_index, "timestamp"]
    before_peak = df.loc[df["timestamp"] < peak_date, "moving_avg"].dropna()
    after_peak = df.loc[df["timestamp"] > peak_date, "moving_avg"].dropna()

    def percentage_change(values):
        if len(values) < 2 or pd.isna(values.iloc[0]) or values.iloc[0] == 0:
            return None
        return float((values.iloc[-1] - values.iloc[0]) / values.iloc[0] * 100)

    growth = percentage_change(before_peak)
    decline = percentage_change(after_peak)
    return df, peak_views, peak_date, growth, decline, int(df["views"].sum()), float(df["views"].mean())

# ---------------------------------
# 6. RULE-BASED INSIGHTS
# ---------------------------------
def generate_insights(topic_name, df, peak_views, peak_date, growth, decline):
    insights = [("Peak readership", f"{topic_name} recorded its highest daily Wikipedia pageviews on {peak_date.strftime('%d %B %Y')}: {peak_views:,} views.")]
    if growth is not None:
        if growth > 0:
            msg = f"The moving average increased by {growth:.2f}% across the measured pre-peak period."
        elif growth < 0:
            msg = f"The moving average decreased by {abs(growth):.2f}% across the measured pre-peak period."
        else:
            msg = "There was no net moving-average change across the measured pre-peak period."
        insights.append(("Pre-peak trend", msg))
    if decline is not None:
        if decline < 0:
            msg = f"The moving average decreased by {abs(decline):.2f}% across the measured post-peak period."
        elif decline > 0:
            msg = f"The moving average increased by {decline:.2f}% across the measured post-peak period."
        else:
            msg = "There was no net moving-average change across the measured post-peak period."
        insights.append(("Post-peak trend", msg))

    counts = df["phase"].value_counts()
    up, down, stable = int(counts.get("Growth", 0)), int(counts.get("Decline", 0)), int(counts.get("Stable", 0))
    if up > down:
        msg = f"Growth labels were more frequent than decline labels ({up} growth vs {down} decline records)."
    elif down > up:
        msg = f"Decline labels were more frequent than growth labels ({down} decline vs {up} growth records)."
    else:
        msg = f"Growth and decline labels occurred equally often ({up} each); {stable} records were labelled stable."
    insights.append(("Phase pattern", msg))
    return insights

# ---------------------------------
# 7. COMPARISON HELPER + ERROR DISPLAY
# ---------------------------------
def prepare_comparison(df, topic_name):
    comp = df[["timestamp", "views"]].copy().sort_values("timestamp")
    first_views = comp["views"].iloc[0]
    comp[topic_name] = (comp["views"] / first_views * 100) if first_views > 0 else np.nan
    return comp[["timestamp", topic_name]]


def show_error(error, context="Analysis"):
    if isinstance(error, requests.HTTPError):
        st.error(f"{context} could not fetch data from Wikipedia (HTTP error). Check the topic/date range and try again.")
    elif isinstance(error, requests.RequestException):
        st.error(f"{context} could not connect to Wikipedia. Check your connection and try again.")
    else:
        st.error(f"{context} failed: {error}")

# ---------------------------------
# 8. WEBSITE HEADER
# ---------------------------------
st.title("📊 Public Attention Lifecycle Analysis & Intelligence System")
st.write("Explore Wikipedia article readership over time, identify attention peaks, study trend phases, compare topics, and review rule-based insights.")
st.caption("Data source: English Wikipedia Pageviews API • Daily article pageviews • Rule-based analysis")

# ---------------------------------
# 9. SIDEBAR CONTROLS (ONE MAIN TOPIC SELECTBOX)
# ---------------------------------
with st.sidebar:
    st.header("Analysis Controls")
    topic = st.selectbox("Select Topic", list(topics.keys()), key="main_topic_select")
    config = topics[topic]
    default_start = pd.to_datetime(config["start"], format="%Y%m%d").date()
    default_end = pd.to_datetime(config["end"], format="%Y%m%d").date()
    date_range = st.date_input(
        "Select Analysis Date Range",
        value=(default_start, default_end),
        key=f"main_analysis_date_range_{topic}",
        help="Choose the start and end dates for the selected topic.",
    )
    analyze_button = st.button("Analyze Attention", type="primary", use_container_width=True, key="main_analyze_button")
    st.divider()
    st.caption("Source: Wikimedia Pageviews API")
    st.caption("Pageviews represent article readership, not unique people.")

# ---------------------------------
# 10. RUN AND SAVE MAIN ANALYSIS
# ---------------------------------
if "selected_analysis" not in st.session_state:
    st.session_state.selected_analysis = None

if analyze_button:
    try:
        if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
            raise ValueError("Please select both a start date and an end date.")
        if date_range[0] >= date_range[1]:
            raise ValueError("The start date must be earlier than the end date.")
        start_str = date_range[0].strftime("%Y%m%d")
        end_str = date_range[1].strftime("%Y%m%d")
        with st.spinner("Fetching and analyzing Wikipedia pageviews..."):
            raw_df = fetch_data(config["article"], start_str, end_str)
            df, peak_views, peak_date, growth, decline, total_views, average_views = analyze_data(raw_df)
            insights = generate_insights(topic, df, peak_views, peak_date, growth, decline)
            st.session_state.selected_analysis = {
                "topic": topic, "article": config["article"],
                "start": date_range[0], "end": date_range[1], "df": df,
                "peak_views": peak_views, "peak_date": peak_date,
                "growth": growth, "decline": decline,
                "total_views": total_views, "average_views": average_views,
                "insights": insights,
            }
    except (requests.RequestException, ValueError, KeyError, TypeError, IndexError) as error:
        st.session_state.selected_analysis = None
        show_error(error)

# ---------------------------------
# 11. DISPLAY MAIN ANALYSIS
# ---------------------------------
result = st.session_state.selected_analysis
if result is None:
    st.info("Choose a topic and date range in the sidebar, then click **Analyze Attention**.")
else:
    df = result["df"]
    topic_name = result["topic"]
    peak_views, peak_date = result["peak_views"], result["peak_date"]
    growth, decline, insights = result["growth"], result["decline"], result["insights"]
    st.divider()
    st.header(f"Attention Analysis: {topic_name}")
    st.caption(f"Wikipedia article: **{result['article']}** · Period: **{result['start'].strftime('%d %b %Y')} – {result['end'].strftime('%d %b %Y')}**")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Peak Daily Views", f"{peak_views:,}")
    c2.metric("Peak Date", peak_date.strftime("%d %b %Y"))
    c3.metric("Total Pageviews", f"{result['total_views']:,}")
    c4.metric("Average Daily Views", f"{result['average_views']:,.0f}")
    c5, c6, c7 = st.columns(3)
    c5.metric("Pre-Peak Moving-Average Change", f"{growth:+.2f}%" if growth is not None else "N/A")
    c6.metric("Post-Peak Moving-Average Change", f"{decline:+.2f}%" if decline is not None else "N/A")
    c7.metric("Daily Records", f"{len(df):,}")
    st.caption("Pre/post-peak percentages compare the first and last available 7-day moving averages on each side of the peak. They are not forecasts.")

    st.subheader("📈 Public Attention Trend")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["timestamp"], df["views"], label="Daily Pageviews", color="#3B82F6", alpha=0.55, linewidth=1.2)
    ax.plot(df["timestamp"], df["moving_avg"], label="7-Record Moving Average", color="#F97316", linewidth=2.4)
    ax.scatter(peak_date, peak_views, color="#16A34A", s=75, label="Peak Daily Views", zorder=5)
    ax.set_title(f"{topic_name}: Daily Pageviews and Moving Average")
    ax.set_xlabel("Date")
    ax.set_ylabel("Wikipedia Pageviews")
    ax.grid(True, alpha=0.22)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.subheader("📊 Attention Phase Distribution")
    phase_order = ["Growth", "Decline", "Stable", "Insufficient Data"]
    phase_counts = df["phase"].value_counts().reindex(phase_order, fill_value=0)
    chart_col, info_col = st.columns([1.5, 1])
    with chart_col:
        st.bar_chart(phase_counts)
    with info_col:
        st.markdown("**Phase counts**")
        for phase_name, count in phase_counts.items():
            st.write(f"- **{phase_name}:** {int(count)}")
        st.caption("Labels show record-by-record moving-average direction, not continuous lifecycle segments.")

    st.subheader("🧠 Automatic Insights")
    st.caption("Generated from transparent Python rules and calculations.")
    insight_cols = st.columns(2)
    for i, (heading, message) in enumerate(insights):
        with insight_cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"**{heading}**")
                st.write(message)
    st.info("These are rule-based observations, not machine-learning predictions. Wikipedia pageviews do not directly measure total public attention, unique people, or actual product usage.")

    st.subheader("📁 Dataset and Export")
    with st.expander("View Processed Dataset"):
        st.dataframe(df, use_container_width=True, hide_index=True)
    csv_data = df.to_csv(index=False).encode("utf-8")
    safe_topic = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in topic_name)
    st.download_button("⬇️ Download Analysis CSV", data=csv_data, file_name=f"{safe_topic}_analysis.csv", mime="text/csv", key="download_main_analysis")

# ---------------------------------
# 12. TOPIC COMPARISON MODE (UNIQUE KEYS)
# ---------------------------------
st.divider()
st.header("🔍 Topic Comparison Mode")
st.write("Compare two topics over the same date range. Each series is indexed to 100 on its first available day so relative movement is easier to compare.")
with st.container(border=True):
    cmp1, cmp2 = st.columns(2)
    with cmp1:
        topic_a = st.selectbox("First Topic", list(topics.keys()), index=0, key="comparison_topic_a")
    with cmp2:
        topic_b = st.selectbox("Second Topic", list(topics.keys()), index=1, key="comparison_topic_b")
    cmp3, cmp4 = st.columns(2)
    with cmp3:
        compare_start = st.date_input("Comparison Start Date", value=date(2023, 1, 1), key="comparison_start_date")
    with cmp4:
        compare_end = st.date_input("Comparison End Date", value=date(2023, 12, 31), key="comparison_end_date")
    compare_button = st.button("Compare Topics", type="primary", key="compare_topics_button")

if compare_button:
    try:
        if topic_a == topic_b:
            raise ValueError("Please select two different topics.")
        if compare_start >= compare_end:
            raise ValueError("The comparison start date must be earlier than the end date.")
        start_str, end_str = compare_start.strftime("%Y%m%d"), compare_end.strftime("%Y%m%d")
        with st.spinner("Fetching both topics for comparison..."):
            df_a = fetch_data(topics[topic_a]["article"], start_str, end_str)
            df_b = fetch_data(topics[topic_b]["article"], start_str, end_str)
            comp_a, comp_b = prepare_comparison(df_a, topic_a), prepare_comparison(df_b, topic_b)
            comparison_df = pd.merge(comp_a, comp_b, on="timestamp", how="inner").dropna()
            if comparison_df.empty:
                st.warning("No overlapping pageview records are available for this pair and date range. Try another range.")
            else:
                st.subheader(f"{topic_a} vs {topic_b}")
                fig, ax = plt.subplots(figsize=(12, 5))
                ax.plot(comparison_df["timestamp"], comparison_df[topic_a], label=topic_a, linewidth=2.2)
                ax.plot(comparison_df["timestamp"], comparison_df[topic_b], label=topic_b, linewidth=2.2)
                ax.axhline(100, linewidth=1, linestyle="--", alpha=0.5)
                ax.set_title("Normalized Wikipedia Pageview Trends")
                ax.set_xlabel("Date")
                ax.set_ylabel("Attention Index (First Available Day = 100)")
                ax.grid(True, alpha=0.22)
                ax.legend()
                fig.autofmt_xdate()
                fig.tight_layout()
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
                st.caption("An index of 200 means twice that topic's own baseline pageviews on that date. This compares relative change, not absolute pageview volume.")
                with st.expander("View Comparison Dataset"):
                    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
                comparison_csv = comparison_df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download Comparison CSV", data=comparison_csv, file_name="topic_comparison.csv", mime="text/csv", key="download_comparison_csv")
    except (requests.RequestException, ValueError, KeyError, TypeError, IndexError) as error:
        show_error(error, context="Topic comparison")

# ---------------------------------
# 13. METHODOLOGY AND DATA NOTES
# ---------------------------------
st.divider()
with st.expander("ℹ️ Data Source, Methodology and Limitations"):
    st.markdown(
        """
        **Data source**
        - English Wikipedia Pageviews API (daily article pageviews).

        **Method**
        1. Fetch daily pageviews for the selected article and date range.
        2. Clean timestamps and numeric view counts; remove invalid and duplicate records.
        3. Calculate a 7-record rolling average to smooth short-term variation.
        4. Label each record Growth, Decline, Stable, or Insufficient Data from changes in the moving average.
        5. Identify the date with the highest daily pageviews and calculate pre-/post-peak moving-average changes when enough data is available.
        6. Generate rule-based insights from these calculations.

        **Limitations**
        - Pageviews are not unique people or a complete measure of public attention.
        - A Wikipedia article may not represent every discussion or activity about a topic.
        - The rolling average uses seven records; if dates are missing, seven records may not equal seven calendar days.
        - Growth/Decline labels are not machine-learning classifications or predictions.
        - Comparison indices show relative change from each topic's first available day in the selected range, not absolute popularity.
        """
    )
st.caption("Student project • Public Attention Lifecycle Analysis & Intelligence System")
