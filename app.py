
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from urllib.parse import quote

# ---------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------

st.set_page_config(
    page_title="Public Attention Intelligence",
    page_icon="📊",
    layout="wide"
)

# ---------------------------------
# 2. TOPIC CONFIGURATION
# ---------------------------------

topics = {
    "Chandrayaan-3": {
        "article": "Chandrayaan-3",
        "start": "20230701",
        "end": "20231031"
    },
    "ChatGPT": {
        "article": "ChatGPT",
        "start": "20221201",
        "end": "20231231"
    },
    "2022 FIFA World Cup": {
        "article": "2022 FIFA World Cup",
        "start": "20221001",
        "end": "20230131"
    }
}

# ---------------------------------
# 3. DATA COLLECTION
# ---------------------------------

@st.cache_data(ttl=3600)
def fetch_data(article, start, end):

    encoded_article = quote(article, safe="")

    url = (
        "https://wikimedia.org/api/rest_v1/"
        "metrics/pageviews/per-article/"
        "en.wikipedia.org/all-access/user/"
        f"{encoded_article}/daily/{start}/{end}"
    )

    response = requests.get(
        url,
        headers={
            "User-Agent":
            "PublicAttentionLifecycleStudentProject/1.0 "
            "(Educational Research)"
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if "items" not in data or not data["items"]:
        raise ValueError("No pageview records available.")

    df = pd.DataFrame(data["items"])

    df = df[["timestamp", "views"]].copy()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        format="%Y%m%d%H"
    )

    df["views"] = pd.to_numeric(
        df["views"], errors="coerce"
    )

    df = df.dropna(subset=["timestamp", "views"])

    df = df.drop_duplicates(subset=["timestamp"])

    df = df.sort_values("timestamp").reset_index(drop=True)

    if len(df) < 8:
        raise ValueError("Insufficient data for analysis.")

    return df


# ---------------------------------
# 4. DATA ANALYSIS
# ---------------------------------

def analyze_data(df):

    df = df.copy()

    df["moving_avg"] = (
        df["views"].rolling(window=7).mean()
    )

    df["attention_change"] = df["moving_avg"].diff()

    def detect_phase(change):
        if pd.isna(change):
            return "Insufficient Data"
        elif change > 0:
            return "Growth"
        elif change < 0:
            return "Decline"
        else:
            return "Stable"

    df["phase"] = df["attention_change"].apply(detect_phase)

    peak_index = df["views"].idxmax()

    peak_views = int(df.loc[peak_index, "views"])
    peak_date = df.loc[peak_index, "timestamp"]

    before_peak = df[
        df["timestamp"] < peak_date
    ]["moving_avg"].dropna()

    after_peak = df[
        df["timestamp"] > peak_date
    ]["moving_avg"].dropna()

    def percentage_change(values):
        if len(values) < 2 or values.iloc[0] == 0:
            return None

        return (
            (values.iloc[-1] - values.iloc[0])
            / values.iloc[0]
        ) * 100

    growth = percentage_change(before_peak)
    decline = percentage_change(after_peak)

    return df, peak_views, peak_date, growth, decline


# ---------------------------------
# 5. AUTOMATIC INSIGHTS
# ---------------------------------

def generate_insights(peak_views, peak_date, growth, decline):

    insights = []

    insights.append(
        f"Peak attention was recorded on "
        f"{peak_date.strftime('%d %B %Y')} "
        f"with {peak_views:,} Wikipedia pageviews."
    )

    if growth is not None:
        if growth > 0:
            insights.append(
                f"Pre-peak moving average increased "
                f"by {growth:.2f}%."
            )
        elif growth < 0:
            insights.append(
                f"Pre-peak moving average decreased "
                f"by {abs(growth):.2f}%."
            )
        else:
            insights.append(
                "No net pre-peak moving average change."
            )

    if decline is not None:
        if decline < 0:
            insights.append(
                f"Post-peak moving average decreased "
                f"by {abs(decline):.2f}%."
            )
        elif decline > 0:
            insights.append(
                f"Post-peak moving average increased "
                f"by {decline:.2f}%."
            )
        else:
            insights.append(
                "No net post-peak moving average change."
            )

    return insights


# ---------------------------------
# 6. WEBSITE HEADER
# ---------------------------------

st.title("📊 Public Attention Lifecycle Analysis & Intelligence System")

st.write(
    "Explore Wikipedia-based public attention trends, "
    "lifecycle patterns and automatic analytical insights."
)

# ---------------------------------
# 7. SIDEBAR CONTROLS
# ---------------------------------

with st.sidebar:

    st.header("Analysis Controls")

    topic = st.selectbox(
        "Select Topic",
        list(topics.keys())
    )

    st.info(
        "Data Source: English Wikipedia Pageviews API"
    )

    analyze_button = st.button(
        "Analyze Attention",
        type="primary",
        use_container_width=True
    )

# ---------------------------------
# 8. SAVE SELECTED ANALYSIS
# ---------------------------------

if "selected_analysis" not in st.session_state:
    st.session_state.selected_analysis = None

if analyze_button:

    config = topics[topic]

    try:
        with st.spinner("Fetching and analyzing data..."):

            df = fetch_data(
                config["article"],
                config["start"],
                config["end"]
            )

            df, peak_views, peak_date, growth, decline = (
                analyze_data(df)
            )

            insights = generate_insights(
                peak_views,
                peak_date,
                growth,
                decline
            )

            st.session_state.selected_analysis = {
                "topic": topic,
                "df": df,
                "peak_views": peak_views,
                "peak_date": peak_date,
                "growth": growth,
                "decline": decline,
                "insights": insights
            }

    except (requests.RequestException, ValueError,
            KeyError, TypeError) as error:

        st.session_state.selected_analysis = None
        st.error(f"Analysis failed: {error}")

# ---------------------------------
# 9. DISPLAY RESULTS
# ---------------------------------

result = st.session_state.selected_analysis

if result is None:

    st.info("Select a topic and click Analyze Attention.")

else:

    df = result["df"]
    topic_name = result["topic"]
    peak_views = result["peak_views"]
    peak_date = result["peak_date"]
    growth = result["growth"]
    decline = result["decline"]
    insights = result["insights"]

    st.header(f"Attention Analysis: {topic_name}")

    # METRIC CARDS

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Peak Daily Views",
            f"{peak_views:,}"
        )

    with col2:
        st.metric(
            "Peak Date",
            peak_date.strftime("%d %b %Y")
        )

    with col3:
        st.metric(
            "Total Records",
            len(df)
        )

    col4, col5 = st.columns(2)

    with col4:
        st.metric(
            "Pre-Peak Change",
            f"{growth:+.2f}%" if growth is not None else "N/A"
        )

    with col5:
        st.metric(
            "Post-Peak Change",
            f"{decline:+.2f}%" if decline is not None else "N/A"
        )

    st.caption(
        "Percentage changes compare starting and ending "
        "7-day moving averages of each period."
    )

    # ---------------------------------
    # 10. ATTENTION TREND GRAPH
    # ---------------------------------

    st.subheader("📈 Public Attention Trend")

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(
        df["timestamp"],
        df["views"],
        label="Daily Views",
        color="blue",
        alpha=0.7
    )

    ax.plot(
        df["timestamp"],
        df["moving_avg"],
        label="7-Day Moving Average",
        color="red",
        linewidth=2
    )

    ax.scatter(
        peak_date,
        peak_views,
        color="green",
        s=100,
        label="Peak Attention",
        zorder=5
    )

    ax.set_title(f"{topic_name} Attention Lifecycle")
    ax.set_xlabel("Date")
    ax.set_ylabel("Daily Wikipedia Pageviews")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.autofmt_xdate()

    st.pyplot(fig)
    plt.close(fig)

    # ---------------------------------
    # 11. PHASE DISTRIBUTION
    # ---------------------------------

    st.subheader("Attention Phase Distribution")

    phase_counts = df["phase"].value_counts()

    st.bar_chart(phase_counts)

    st.caption(
        "Phases show daily changes in the 7-day "
        "moving average, not continuous lifecycle periods."
    )

    # ---------------------------------
    # 12. AUTOMATIC INSIGHTS
    # ---------------------------------

    st.subheader("🧠 Automatic Insights")

    for insight in insights:
        st.write("•", insight)

    st.info(
        "These are rule-based analytical insights, "
        "not machine-learning predictions."
    )

    # ---------------------------------
    # 13. DATASET AND DOWNLOAD
    # ---------------------------------

    with st.expander("View Processed Dataset"):

        st.dataframe(
            df,
            use_container_width=True
        )

    csv_data = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Analysis CSV",
        data=csv_data,
        file_name=f"{topic_name.replace(' ', '_')}_analysis.csv",
        mime="text/csv"
    )

    st.caption(
        "Wikipedia pageviews indicate article readership, "
        "not unique people or actual product usage."
    )
