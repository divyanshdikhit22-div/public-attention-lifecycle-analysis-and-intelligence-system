import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import quote
from datetime import date

# =========================================================
# PUBLIC ATTENTION LIFECYCLE ANALYSIS & INTELLIGENCE SYSTEM | Streamlit dashboard updated
# =========================================================
st.set_page_config(
    page_title="Public Attention Lifecycle Analysis & Intelligence System",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Topic configuration ----------
TOPICS = {
    "Chandrayaan-3": {"article": "Chandrayaan-3", "start": "20230701", "end": "20231031", "group": "Science"},
    "ChatGPT": {"article": "ChatGPT", "start": "20221201", "end": "20231231", "group": "Technology"},
    "2022 FIFA World Cup": {"article": "2022 FIFA World Cup", "start": "20221001", "end": "20230131", "group": "Sports"},
    "COVID-19 Pandemic": {"article": "COVID-19 pandemic", "start": "20200101", "end": "20231231", "group": "Health"},
    "2024 Summer Olympics": {"article": "2024 Summer Olympics", "start": "20240701", "end": "20240930", "group": "Sports"},
    "2024 Indian General Election": {"article": "2024 Indian general election", "start": "20240401", "end": "20240630", "group": "Politics"},
    "BGMI": {"article": "Battlegrounds Mobile India", "start": "20210501", "end": "20231231", "group": "Gaming"},
    "Tesla": {"article": "Tesla, Inc.", "start": "20200101", "end": "20231231", "group": "Business"},
    "Dangal Movie": {"article": "Dangal (2016 film)", "start": "20161001", "end": "20171231", "group": "Entertainment"},
}

# ---------- Polished dark theme ----------
st.markdown("""
<style>
:root {
  --bg: #0b1020; --panel: #121a2d; --panel2: #17223a;
  --text: #f4f7ff; --muted: #9ba9c7; --line: rgba(148,163,184,.20);
  --cyan: #38bdf8; --violet: #a78bfa; --mint: #34d399; --pink: #f472b6;
}
.stApp { background:
  radial-gradient(ellipse at 8% 0%, rgba(56,189,248,.10), transparent 34%),
  radial-gradient(ellipse at 95% 8%, rgba(167,139,250,.12), transparent 32%),
  #0b1020; color: var(--text); }
.block-container { padding-top: 1.35rem; padding-bottom: 3rem; max-width: 1500px; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#111a2e 0%,#0c1324 100%); border-right: 1px solid var(--line); }
[data-testid="stSidebar"] * { color: #e6edff; }
h1,h2,h3 { letter-spacing: -.025em; }
h1 { font-weight: 800 !important; }
h2,h3 { font-weight: 700 !important; }
p, label, .stCaption { color: #c3cce0; }
.hero {
  padding: 1.55rem 1.7rem; border-radius: 22px; margin-bottom: 1rem;
  background: linear-gradient(115deg,rgba(20,31,55,.98),rgba(27,24,58,.95));
  border: 1px solid rgba(148,163,184,.25);
  box-shadow: 0 18px 50px rgba(0,0,0,.20);
}
.eyebrow { color: #67e8f9; font-size: .78rem; font-weight: 800; letter-spacing: .15em; text-transform: uppercase; }
.hero-title { font-size: clamp(1.8rem,3vw,2.7rem); line-height: 1.12; font-weight: 850; margin: .45rem 0 .6rem; color: #f8fbff; }
.hero-copy { color: #bac8e5; max-width: 850px; font-size: 1rem; }
.pill { display:inline-block; padding:.32rem .65rem; border:1px solid rgba(56,189,248,.35); border-radius:999px; background:rgba(56,189,248,.09); color:#a5f3fc; font-size:.76rem; margin:.15rem .2rem .1rem 0; }
[data-testid="stMetric"] {
  background: linear-gradient(145deg,rgba(22,33,56,.95),rgba(17,25,43,.96));
  border: 1px solid rgba(148,163,184,.22); border-radius: 16px;
  padding: 15px 17px; box-shadow: 0 8px 24px rgba(0,0,0,.13);
}
[data-testid="stMetricLabel"] { color: #a9b8d5 !important; font-weight: 600; }
[data-testid="stMetricValue"] { color: #f8fbff !important; font-weight: 800; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-color: rgba(148,163,184,.22) !important; border-radius: 16px; }
.stButton > button, .stDownloadButton > button {
  border-radius: 10px; border: 1px solid rgba(56,189,248,.35);
  font-weight: 700; transition: all .15s ease;
}
.stButton > button[kind="primary"] { background: linear-gradient(100deg,#0891b2,#7c3aed); color: white; border: 0; }
.stButton > button:hover, .stDownloadButton > button:hover { border-color: #67e8f9; transform: translateY(-1px); }
.stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { background: rgba(18,26,45,.8); border-radius: 10px 10px 0 0; padding: 10px 17px; }
.stTabs [aria-selected="true"] { background: rgba(56,189,248,.14) !important; color: #a5f3fc !important; }
div[data-testid="stAlert"] { border-radius: 12px; }
hr { border-color: rgba(148,163,184,.18); }
.small-muted { color:#94a3b8; font-size:.85rem; }
.section-kicker { color:#67e8f9; font-size:.75rem; text-transform:uppercase; letter-spacing:.13em; font-weight:800; }
</style>
""", unsafe_allow_html=True)

PLOTLY_TEMPLATE = "plotly_dark"
PLOTLY_LAYOUT = dict(
    template=PLOTLY_TEMPLATE,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#dce6fb", family="Inter, Arial, sans-serif"),
    margin=dict(l=18, r=18, t=52, b=18),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    hovermode="x unified",
)

# ---------- Data collection ----------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_data(article: str, start: str, end: str) -> pd.DataFrame:
    """Fetch daily English Wikipedia pageviews for a selected article."""
    encoded_article = quote(article.replace(" ", "_"), safe="")
    url = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"en.wikipedia.org/all-access/user/{encoded_article}/daily/{start}/{end}"
    )
    response = requests.get(
        url,
        headers={"User-Agent": "PublicAttentionIntelligenceStudentProject/2.0 (educational research)"},
        timeout=30,
    )
    if response.status_code == 404:
        raise ValueError("Wikipedia returned no article data for this title/date range. Try another topic or period.")
    response.raise_for_status()
    items = response.json().get("items", [])
    if not items:
        raise ValueError("No Wikipedia pageview records were returned. Try another topic or date range.")
    df = pd.DataFrame(items)
    if not {"timestamp", "views"}.issubset(df.columns):
        raise ValueError("The Wikipedia API response did not contain the expected fields.")
    df = df[["timestamp", "views"]].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y%m%d%H", errors="coerce")
    df["views"] = pd.to_numeric(df["views"], errors="coerce")
    df = df.dropna(subset=["timestamp", "views"]).drop_duplicates("timestamp")
    df = df.sort_values("timestamp").reset_index(drop=True)
    if len(df) < 8:
        raise ValueError("Too few records for trend analysis. Select a longer date range.")
    return df

def analyze_data(raw_df: pd.DataFrame):
    df = raw_df.copy().sort_values("timestamp").reset_index(drop=True)
    df["moving_avg"] = df["views"].rolling(window=7, min_periods=1).mean()
    df["attention_change"] = df["moving_avg"].diff()
    df["phase"] = np.select(
        [df["attention_change"] > 0, df["attention_change"] < 0],
        ["Growth", "Decline"], default="Stable"
    )
    if len(df):
        df.loc[0, "phase"] = "Insufficient Data"
    peak_idx = df["views"].idxmax()
    peak_views = int(df.loc[peak_idx, "views"])
    peak_date = df.loc[peak_idx, "timestamp"]
    before = df.loc[df["timestamp"] < peak_date, "moving_avg"].dropna()
    after = df.loc[df["timestamp"] > peak_date, "moving_avg"].dropna()

    def pct_change(series):
        if len(series) < 2 or pd.isna(series.iloc[0]) or series.iloc[0] == 0:
            return None
        return float((series.iloc[-1] - series.iloc[0]) / series.iloc[0] * 100)

    return {
        "df": df, "peak_views": peak_views, "peak_date": peak_date,
        "growth": pct_change(before), "decline": pct_change(after),
        "total_views": int(df["views"].sum()), "average_views": float(df["views"].mean()),
        "median_views": float(df["views"].median()),
        "growth_days": int((df["phase"] == "Growth").sum()),
        "decline_days": int((df["phase"] == "Decline").sum()),
    }

def show_error(error, context="Analysis"):
    if isinstance(error, requests.Timeout):
        st.error(f"{context} timed out while contacting Wikipedia. Please retry in a moment.")
    elif isinstance(error, requests.HTTPError):
        st.error(f"{context} could not retrieve Wikipedia data (HTTP {error.response.status_code if error.response is not None else 'error'}). Check the article title and date range.")
    elif isinstance(error, requests.RequestException):
        st.error(f"{context} could not connect to Wikipedia. Check the deployment/network and retry.")
    else:
        st.error(f"{context} could not be completed: {error}")

def build_insights(topic_name, result):
    df = result["df"]
    insights = [
        ("Peak readership", f"{topic_name} reached its highest daily pageviews on {result['peak_date']:%d %B %Y}, with {result['peak_views']:,} views."),
        ("Typical daily readership", f"The selected period averaged {result['average_views']:,.0f} pageviews per day; the median was {result['median_views']:,.0f}."),
    ]
    counts = df["phase"].value_counts()
    growth, decline = int(counts.get("Growth", 0)), int(counts.get("Decline", 0))
    if growth > decline:
        phase_msg = f"Daily moving-average direction was upward more often ({growth} growth records vs {decline} decline records)."
    elif decline > growth:
        phase_msg = f"Daily moving-average direction was downward more often ({decline} decline records vs {growth} growth records)."
    else:
        phase_msg = f"Growth and decline records were balanced ({growth} each)."
    insights.append(("Attention pattern", phase_msg))
    if result["growth"] is not None:
        insights.append(("Before the peak", f"The 7-record moving average changed by {result['growth']:+.1f}% across the measured pre-peak period."))
    if result["decline"] is not None:
        insights.append(("After the peak", f"The 7-record moving average changed by {result['decline']:+.1f}% across the measured post-peak period."))
    return insights

def plot_trend(result, topic_name):
    df = result["df"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["views"], name="Daily pageviews",
        mode="lines", line=dict(color="#38bdf8", width=1.3),
        fill="tozeroy", fillcolor="rgba(56,189,248,.08)",
        hovertemplate="%{x|%d %b %Y}<br>Views: %{y:,.0f}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["moving_avg"], name="7-record moving average",
        mode="lines", line=dict(color="#f472b6", width=3),
        hovertemplate="%{x|%d %b %Y}<br>Moving average: %{y:,.1f}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=[result["peak_date"]], y=[result["peak_views"]], name="Peak",
        mode="markers", marker=dict(size=12, color="#34d399", line=dict(width=2, color="#eafff7")),
        hovertemplate="Peak: %{y:,.0f}<br>%{x|%d %b %Y}<extra></extra>"
    ))
    fig.update_layout(**PLOTLY_LAYOUT, title=f"{topic_name} · daily pageviews")
    fig.update_xaxes(title="", showgrid=False, rangeslider=dict(visible=True, thickness=0.07))
    fig.update_yaxes(title="Pageviews", gridcolor="rgba(148,163,184,.12)", rangemode="tozero")
    return fig

def fetch_analyzed(topic_name, start_date, end_date):
    if start_date >= end_date:
        raise ValueError("The start date must be earlier than the end date.")
    config = TOPICS[topic_name]
    raw = fetch_data(config["article"], start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d"))
    return analyze_data(raw)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 📡 Attention Lab")
    st.caption("PUBLIC ATTENTION LIFECYCLE ANALYSIS & INTELLIGENCE SYSTEM ")
    st.divider()
    st.markdown("### 🎯 Analysis controls")
    topic = st.selectbox("Choose a topic", list(TOPICS.keys()), key="topic_select")
    topic_cfg = TOPICS[topic]
    start_default = pd.to_datetime(topic_cfg["start"], format="%Y%m%d").date()
    end_default = pd.to_datetime(topic_cfg["end"], format="%Y%m%d").date()
    date_range = st.date_input(
        "Analysis period", value=(start_default, end_default),
        min_value=date(2001, 1, 1), max_value=date.today(),
        key=f"date_range_{topic}",
        help="Choose a start and end date for the Wikipedia pageview series."
    )
    run_analysis = st.button("⚡ Analyze attention", type="primary", use_container_width=True)
    st.divider()
    st.markdown("### 🧭 What this dashboard does")
    st.markdown("- Tracks daily Wikipedia readership\n- Finds peak attention dates\n- Labels short-term trend direction\n- Compares topics on a relative index")
    st.caption("Data: Wikimedia Pageviews API")
    st.caption("Pageviews are not unique people or a complete measure of public attention.")

# ---------- Hero header ----------
st.markdown("""
<div class="hero">
  <div class="eyebrow">Student research dashboard · Live API data</div>
  <div class="hero-title">Public Attention Lifecycle Analysis & <span style="color:#67e8f9">Intelligence System </span></div>
  <div class="hero-copy">Explore how attention around major events, technology, entertainment and gaming changes over time. Find peaks, inspect trends and compare topics with interactive charts.</div>
  <div style="margin-top:.85rem">
    <span class="pill">📈 Trend analysis</span>
    <span class="pill">🧠 Auto insights</span>
    <span class="pill">⚖️ Topic comparison</span>
    <span class="pill">⬇️ CSV export</span>
  </div>
</div>
""", unsafe_allow_html=True)

# Persist most recent successful analysis
if "selected_analysis" not in st.session_state:
    st.session_state.selected_analysis = None

if run_analysis:
    try:
        if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
            raise ValueError("Please select both a start date and an end date.")
        with st.spinner("Connecting to Wikipedia and calculating attention patterns…"):
            result = fetch_analyzed(topic, date_range[0], date_range[1])
            result.update({
                "topic": topic, "article": topic_cfg["article"],
                "start": date_range[0], "end": date_range[1],
            })
            st.session_state.selected_analysis = result
    except (requests.RequestException, ValueError, KeyError, TypeError, IndexError) as error:
        st.session_state.selected_analysis = None
        show_error(error)

result = st.session_state.selected_analysis

if result is None:
    st.markdown("### 👋 Start exploring")
    left, right = st.columns([1.25, 1])
    with left:
        st.markdown("""
        <div style="background:rgba(18,26,45,.82);border:1px solid rgba(148,163,184,.2);border-radius:18px;padding:1.25rem">
          <div class="section-kicker">Quick start</div>
          <h3 style="margin:.45rem 0">Your research workspace is ready</h3>
          <p style="color:#b9c7e3">Choose a topic and date range in the sidebar, then press <b>Analyze attention</b>. The dashboard will build interactive charts and calculated insights from the fetched data.</p>
          <p style="color:#67e8f9;margin-bottom:0">Tip: use a date range that includes the event you want to study.</p>
        </div>
        """, unsafe_allow_html=True)
    with right:
        st.markdown("#### Topic collection")
        topic_df = pd.DataFrame([{"Topic": name, "Category": val["group"]} for name, val in TOPICS.items()])
        st.dataframe(topic_df, use_container_width=True, hide_index=True, height=285)
else:
    df = result["df"]
    topic_name = result["topic"]
    st.markdown(f"### 🔎 Analysis workspace <span style='color:#67e8f9'>/ {topic_name}</span>", unsafe_allow_html=True)
    st.caption(f"Article: **{result['article']}**  ·  Period: **{result['start']:%d %b %Y} – {result['end']:%d %b %Y}**  ·  Category: **{TOPICS[topic_name]['group']}**")

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Peak daily views", f"{result['peak_views']:,}", help="Highest single-day pageview count in the selected period.")
    k2.metric("Total pageviews", f"{result['total_views']:,}")
    k3.metric("Daily average", f"{result['average_views']:,.0f}")
    k4.metric("Peak date", result["peak_date"].strftime("%d %b %Y"))
    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Median daily views", f"{result['median_views']:,.0f}")
    k6.metric("Growth records", f"{result['growth_days']:,}")
    k7.metric("Decline records", f"{result['decline_days']:,}")
    k8.metric("Data points", f"{len(df):,}")

    overview_tab, insights_tab, dataset_tab, compare_tab, methodology_tab = st.tabs([
        "📊 Overview", "🧠 Insights", "🗂️ Data explorer", "⚖️ Compare topics", "ℹ️ Methodology"
    ])

    with overview_tab:
        st.markdown("#### Attention timeline")
        st.caption("Hover over the chart for exact values. Use the range slider under the chart to zoom into a period.")
        st.plotly_chart(plot_trend(result, topic_name), use_container_width=True, config={"displaylogo": False, "scrollZoom": True})
        chart_l, chart_r = st.columns([1, 1])
        with chart_l:
            st.markdown("#### Attention phase distribution")

            
            counts = df["phase"].value_counts().reindex(["Growth", "Decline", "Stable", "Insufficient Data"], fill_value=0).reset_index()
            counts.columns = ["Phase", "Records"]
            phase_fig = px.pie(counts, names="Phase", values="Records", hole=.62,
                               color="Phase", color_discrete_map={
                                   "Growth": "#34d399", "Decline": "#fb7185",
                                   "Stable": "#60a5fa", "Insufficient Data": "#a78bfa"})
            phase_fig.update_layout(**PLOTLY_LAYOUT, legend_title_text="")
            phase_fig.update_traces(textposition="inside", textinfo="percent+label", hole=0.62)
            st.plotly_chart(phase_fig, use_container_width=True, config={"displaylogo": False})
        with chart_r:
            st.markdown("#### Day-to-day readership")
            day_df = df.copy()
            day_df["weekday"] = day_df["timestamp"].dt.day_name()
            weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            weekday_df = day_df.groupby("weekday", as_index=False)["views"].mean()
            weekday_df["weekday"] = pd.Categorical(weekday_df["weekday"], categories=weekday_order, ordered=True)
            weekday_df = weekday_df.sort_values("weekday")
            weekday_fig = px.bar(weekday_df, x="weekday", y="views", color="views",
                                 color_continuous_scale=["#164e63", "#22d3ee", "#a78bfa"],
                                 labels={"weekday": "Day", "views": "Average pageviews"})
            weekday_fig.update_layout(**PLOTLY_LAYOUT, title="Average pageviews by weekday", coloraxis_showscale=False)
            st.plotly_chart(weekday_fig, use_container_width=True, config={"displaylogo": False})
        st.caption("The weekday chart is descriptive; it does not establish why readership differs.")

    with insights_tab:
        st.markdown("#### What the data suggests")
        st.caption("These are transparent rule-based observations, not AI predictions or causal explanations.")
        insights = build_insights(topic_name, result)
        for i in range(0, len(insights), 2):
            cols = st.columns(2)
            for j, item in enumerate(insights[i:i+2]):
                with cols[j]:
                    with st.container(border=True):
                        st.markdown(f"<div class='section-kicker'>Finding {i+j+1:02d}</div>", unsafe_allow_html=True)
                        st.markdown(f"### {item[0]}")
                        st.write(item[1])
        st.info("Interpretation note: Wikipedia pageviews indicate article readership. They do not directly measure unique individuals, sentiment, product usage or all public discussion.")
        st.markdown("#### Quick interpretation guide")
        st.markdown("- **Peak daily views:** the busiest single day in this data window.\n- **Moving average:** smooths short-term daily variation using up to seven records.\n- **Growth/decline records:** indicate the direction of the moving average compared with the previous record.\n- **Pre/post-peak change:** compares the first and last available moving averages on either side of the peak; it is not a forecast.")

    with dataset_tab:
        st.markdown("#### Explore the processed records")
        filter_col1, filter_col2 = st.columns([1, 1])
        with filter_col1:
            phase_filter = st.multiselect("Filter by phase", options=["Growth", "Decline", "Stable", "Insufficient Data"], default=["Growth", "Decline", "Stable", "Insufficient Data"])
        with filter_col2:
            min_views = st.slider("Minimum daily pageviews", min_value=0, max_value=max(1, int(df["views"].max())), value=0)
        filtered = df[df["phase"].isin(phase_filter) & (df["views"] >= min_views)]
        st.caption(f"Showing {len(filtered):,} of {len(df):,} records")
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        csv_data = df.to_csv(index=False).encode("utf-8")
        safe_topic = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in topic_name)
        st.download_button("⬇️ Download full analysis CSV", data=csv_data, file_name=f"{safe_topic}_analysis.csv", mime="text/csv", key="download_main_analysis")
        st.download_button("⬇️ Download filtered CSV", data=filtered.to_csv(index=False).encode("utf-8"), file_name=f"{safe_topic}_filtered.csv", mime="text/csv", key="download_filtered_analysis")

    with compare_tab:
        st.markdown("#### Compare two topics")
        st.write("Each line is indexed to 100 on its first available day, making relative change easier to compare. It does not compare absolute readership.")
        compare_cols = st.columns(2)
        names = list(TOPICS.keys())
        with compare_cols[0]:
            topic_a = st.selectbox("First topic", names, index=names.index(topic_name), key="compare_a")
        with compare_cols[1]:
            default_b = names[1] if names[0] == topic_a else names[0]
            topic_b = st.selectbox("Second topic", names, index=names.index(default_b), key="compare_b")
        d1, d2 = st.columns(2)
        with d1:
            cmp_start = st.date_input("Comparison start", value=max(date(2001, 1, 1), result["start"]), key="cmp_start")
        with d2:
            cmp_end = st.date_input("Comparison end", value=min(date.today(), result["end"]), key="cmp_end")
        if st.button("🚀 Run comparison", type="primary", key="run_comparison"):
            try:
                if topic_a == topic_b:
                    raise ValueError("Select two different topics to compare.")
                if cmp_start >= cmp_end:
                    raise ValueError("Comparison start date must be earlier than end date.")
                with st.spinner("Fetching both topic series…"):
                    a = fetch_data(TOPICS[topic_a]["article"], cmp_start.strftime("%Y%m%d"), cmp_end.strftime("%Y%m%d"))
                    b = fetch_data(TOPICS[topic_b]["article"], cmp_start.strftime("%Y%m%d"), cmp_end.strftime("%Y%m%d"))
                a = a[["timestamp", "views"]].copy()
                b = b[["timestamp", "views"]].copy()
                a["index"] = a["views"] / a["views"].iloc[0] * 100 if a["views"].iloc[0] else np.nan
                b["index"] = b["views"] / b["views"].iloc[0] * 100 if b["views"].iloc[0] else np.nan
                comp = pd.merge(a[["timestamp", "index"]].rename(columns={"index": topic_a}),
                                b[["timestamp", "index"]].rename(columns={"index": topic_b}),
                                on="timestamp", how="inner").dropna()
                if comp.empty:
                    st.warning("There are no overlapping records for this comparison. Try another date range.")
                else:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=comp["timestamp"], y=comp[topic_a], name=topic_a, mode="lines", line=dict(width=2.7, color="#38bdf8")))
                    fig.add_trace(go.Scatter(x=comp["timestamp"], y=comp[topic_b], name=topic_b, mode="lines", line=dict(width=2.7, color="#f472b6")))
                    fig.add_hline(y=100, line_dash="dash", line_color="#94a3b8", opacity=.65)
                    fig.update_layout(**PLOTLY_LAYOUT, title="Relative attention index (first available day = 100)")
                    fig.update_xaxes(title="")
                    fig.update_yaxes(title="Indexed pageviews", gridcolor="rgba(148,163,184,.12)")
                    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "scrollZoom": True})
                    st.caption("An index of 200 means twice the topic's own baseline readership. Different starting volumes are normalized.")
                    st.dataframe(comp, use_container_width=True, hide_index=True)
                    st.download_button("⬇️ Download comparison CSV", data=comp.to_csv(index=False).encode("utf-8"), file_name="topic_comparison.csv", mime="text/csv", key="download_comparison")
            except (requests.RequestException, ValueError, KeyError, TypeError, IndexError) as error:
                show_error(error, context="Topic comparison")

    with methodology_tab:
        st.markdown("#### How the analysis works")
        st.markdown("""
        1. **Fetch:** request daily English Wikipedia pageviews from the Wikimedia Pageviews API.
        2. **Clean:** parse dates and view counts, remove invalid/duplicate records and sort chronologically.
        3. **Smooth:** calculate a rolling average over up to seven records.
        4. **Classify:** label each record Growth, Decline or Stable based on the change in the moving average.
        5. **Measure:** calculate total, average, median and peak daily pageviews, plus pre-/post-peak changes when possible.
        6. **Explain:** generate rule-based findings from the calculated values.
        """)
        st.markdown("#### Important limitations")
        st.markdown("""
        - Pageviews are not unique people and do not measure sentiment.
        - One Wikipedia article cannot represent every conversation about a topic.
        - Seven records may not equal seven calendar days if API records are missing.
        - Growth/Decline labels are descriptive, not machine-learning predictions.
        - The comparison chart measures relative movement from each series' first available day, not absolute popularity.
        """)
        st.markdown("#### Data source")
        st.link_button("Open Wikimedia Pageviews API documentation", "https://wikimedia.org/api/rest_v1/")

st.divider()
footer_left, footer_right = st.columns([2, 1])
with footer_left:
    st.markdown("<div class='small-muted'>PUBLIC ATTENTION INTELLIGENCE · Student project</div>", unsafe_allow_html=True)
with footer_right:
    st.markdown("<div class='small-muted' style='text-align:right'>Built with Streamlit, Plotly & Wikimedia data</div>", unsafe_allow_html=True)
