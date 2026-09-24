"""
YouTube Trending Video Analytics Dashboard — India
Backend (SQL via sqlite3) + Frontend (Streamlit + Plotly + custom HTML/CSS/JS)
Single file — no modules split.
"""

import glob
import os
import sqlite3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

# ─────────────────────────────────────────────────────────────────────────────
# 0. PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YT Trending India",
    page_icon="▶️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. GLOBAL CSS  — dark theme, cards, sidebar, tabs, scrollbar, animations
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── root palette ── */
:root {
  --bg:       #0a0a0f;
  --surface:  #13131f;
  --card:     #1a1a2e;
  --border:   #252540;
  --red:      #e50914;
  --red-dim:  #8b000a;
  --blue:     #3b82f6;
  --muted:    #8b8fa8;
  --text:     #e2e2f0;
}

/* ── page background ── */
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main { background: var(--bg) !important; }

/* ── sidebar ── */
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── all text ── */
h1,h2,h3,h4,h5,h6,p,li,span,div,label,
[data-testid="stMarkdownContainer"] *  { color: var(--text) !important; }

/* ── subheader style ── */
.section-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text) !important;
  border-left: 3px solid var(--red);
  padding-left: 10px;
  margin: 18px 0 10px;
}

/* ── KPI card ── */
.kpi-card {
  background: linear-gradient(145deg, #1a1a2e 0%, #0f0f1e 100%);
  border: 1px solid var(--border);
  border-top: 2px solid var(--red);
  border-radius: 12px;
  padding: 18px 14px 14px;
  text-align: center;
  transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
  cursor: default;
}
.kpi-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(229,9,20,.4);
  border-color: var(--red) !important;
}
.kpi-icon  { font-size: 1.5rem; line-height: 1; margin-bottom: 6px; }
.kpi-label { font-size: .7rem !important; color: var(--muted) !important;
             letter-spacing: .08em; text-transform: uppercase; }
.kpi-val   { font-size: 1.75rem; font-weight: 800;
             color: var(--red) !important; margin: 4px 0 2px; line-height: 1.1; }
.kpi-sub   { font-size: .7rem !important; color: var(--blue) !important; }

/* ── tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface);
  border-radius: 8px;
  gap: 3px;
  padding: 4px;
  border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
  border-radius: 6px;
  color: var(--muted) !important;
  font-size: .85rem;
  padding: 8px 16px;
  font-weight: 500;
}
.stTabs [aria-selected="true"] {
  background: var(--red) !important;
  color: #fff !important;
}

/* ── dataframe ── */
.stDataFrame            { border-radius: 10px; overflow: hidden; }
.stDataFrame thead th   { background: #1a1a2e !important; color: #e2e2f0 !important; }
.stDataFrame tbody tr:hover { background: #1f1f35 !important; }

/* ── inputs ── */
.stTextInput input, .stMultiSelect, .stDateInput input {
  background: var(--surface) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
}

/* ── download button ── */
.stDownloadButton button {
  background: var(--red) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
}
.stDownloadButton button:hover { background: #c00010 !important; }

/* ── scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb { background: #333355; border-radius: 4px; }

/* ── insight card ── */
.insight-box {
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 3px solid var(--red);
  border-radius: 10px;
  padding: 14px 18px;
  margin-bottom: 10px;
  font-size: .9rem;
  line-height: 1.6;
}

/* ── progress bar in table ── */
.prog-wrap { background:#252540; border-radius:4px; height:6px; }
.prog-bar  { background:var(--red); border-radius:4px; height:6px; }

/* ── hide streamlit branding ── */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 2. YOUTUBE CATEGORY MAP
# ─────────────────────────────────────────────────────────────────────────────
CATEGORY_MAP = {
    1:  "Film & Animation",
    2:  "Autos & Vehicles",
    10: "Music",
    15: "Pets & Animals",
    17: "Sports",
    19: "Travel & Events",
    20: "Gaming",
    22: "People & Blogs",
    23: "Comedy",
    24: "Entertainment",
    25: "News & Politics",
    26: "Howto & Style",
    27: "Education",
    28: "Science & Technology",
    29: "Nonprofits & Activism",
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. AUTO-DETECT CSV  (works for any *_Trending.csv in the working directory)
# ─────────────────────────────────────────────────────────────────────────────
def find_csv() -> str:
    """Return the path of the first *_Trending.csv found, preferring IN_ then BR_."""
    candidates = glob.glob("*_Trending.csv")
    if not candidates:
        st.error("No *_Trending.csv file found in the working directory.")
        st.stop()
    # Prefer IN_ > BR_ > alphabetical
    for prefix in ("IN_", "BR_"):
        for c in candidates:
            if os.path.basename(c).startswith(prefix):
                return c
    return sorted(candidates)[0]

CSV_PATH = find_csv()
# Derive region label from filename (e.g. "IN_Trending.csv" → "India")
_REGION_CODES = {"IN": "India", "BR": "Brazil", "US": "USA", "GB": "UK",
                 "DE": "Germany", "FR": "France", "JP": "Japan", "CA": "Canada"}
_code = os.path.basename(CSV_PATH).split("_")[0].upper()
REGION_LABEL = _REGION_CODES.get(_code, _code)

# ─────────────────────────────────────────────────────────────────────────────
# 4. DATA LOADING & CLEANING
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="⏳ Loading & cleaning data…")
def load_and_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")

    # Numeric coercion — handle any stray non-numeric values
    for col in ("views", "likes", "dislikes", "comments"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Parse ISO-8601 publish_time
    df["publish_time"] = pd.to_datetime(df["publish_time"], utc=True, errors="coerce")
    df = df.dropna(subset=["publish_time"])          # drop rows with unparseable dates
    df["publish_date"] = df["publish_time"].dt.date
    df["publish_day"]  = df["publish_time"].dt.day_name()
    df["publish_hour"] = df["publish_time"].dt.hour

    # Category name
    df["category_id"] = pd.to_numeric(df["category_id"], errors="coerce")
    df["category"]    = df["category_id"].map(CATEGORY_MAP).fillna("Unknown")

    # Engagement rate — guard zero-view rows
    df["engagement_rate"] = (
        (df["likes"] + df["comments"]) / df["views"].replace(0, 1)
    ).round(6)

    # likes_floor: used as bubble size (px.scatter needs > 0)
    df["likes_size"] = df["likes"].clip(lower=1)

    return df


df_full = load_and_clean(CSV_PATH)

# ─────────────────────────────────────────────────────────────────────────────
# 5. SQL HELPER
# ─────────────────────────────────────────────────────────────────────────────
def run_sql(query: str, data: pd.DataFrame) -> pd.DataFrame:
    """Run SQL on an in-memory SQLite table called 'videos'."""
    con = sqlite3.connect(":memory:")
    data.to_sql("videos", con, if_exists="replace", index=False)
    result = pd.read_sql_query(query, con)
    con.close()
    return result

# ─────────────────────────────────────────────────────────────────────────────
# 6. SIDEBAR FILTERS
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Hero logo block
    components.html("""
    <div style="text-align:center;padding:16px 0 8px">
      <div style="font-size:2.4rem;line-height:1">▶️</div>
      <div style="font-size:1.1rem;font-weight:800;color:#e50914;
                  letter-spacing:.04em;margin-top:4px">YT TRENDING</div>
      <div style="font-size:.75rem;color:#8b8fa8;margin-top:2px">""" + REGION_LABEL + """</div>
    </div>
    <hr style="border:none;border-top:1px solid #252540;margin:8px 0 16px"/>
    """, height=110)

    st.markdown("**📂 Category**")
    all_cats = sorted(df_full["category"].unique())
    selected_cats = st.multiselect(
        label="Category",
        options=all_cats,
        default=all_cats,
        label_visibility="collapsed",
    )

    st.markdown("**📅 Publish Date Range**")
    min_date = df_full["publish_date"].min()
    max_date = df_full["publish_date"].max()
    # Default to last 90 days so sparse early dates don't show 0-row views
    _default_start = max(min_date, (pd.Timestamp(max_date) - pd.Timedelta(days=90)).date())
    date_range = st.date_input(
        label="Date range",
        value=(_default_start, max_date),
        min_value=min_date,
        max_value=max_date,
        label_visibility="collapsed",
    )

    st.markdown("**🔍 Search**")
    search_q = st.text_input(
        label="Search",
        placeholder="Channel or video title…",
        label_visibility="collapsed",
    )

    # ── Year quick-select buttons ──
    st.markdown("**⚡ Quick Year Filter**")
    _all_years = sorted(
        set(pd.Timestamp(d).year for d in df_full["publish_date"].unique()),
        reverse=True
    )
    _year_cols = st.columns(min(len(_all_years), 4))
    _selected_year = None
    for _i, _yr in enumerate(_all_years[:8]):   # show at most 8 recent years
        with _year_cols[_i % 4]:
            if st.button(str(_yr), key=f"yr_{_yr}", use_container_width=True):
                _selected_year = _yr
    # Store chosen year in session state so it persists
    if _selected_year:
        st.session_state["_quick_year"] = _selected_year
    if "_quick_year" in st.session_state:
        st.caption(f"⚡ Quick year active: **{st.session_state['_quick_year']}** — adjust date picker above to change.")

    st.markdown("---")
    st.caption(
        f"📁 {os.path.basename(CSV_PATH)}  ·  {len(df_full):,} rows\n\n"
        f"📆 {df_full['publish_date'].min()} → {df_full['publish_date'].max()}"
    )

# ─────────────────────────────────────────────────────────────────────────────
# 7. APPLY FILTERS  (all three are independent — applied in sequence)
# ─────────────────────────────────────────────────────────────────────────────
df = df_full.copy()

# 7a. Category
if selected_cats:
    df = df[df["category"].isin(selected_cats)]

# 7b. Date range — apply quick-year override first, then picker.
#     st.date_input returns a tuple of 2 when both ends are set,
#     or a tuple of 1 / single date when user is mid-selection. Guard both.
if "_quick_year" in st.session_state:
    _qy = st.session_state["_quick_year"]
    import datetime as _dt2
    _qs = _dt2.date(_qy, 1, 1)
    _qe = _dt2.date(_qy, 12, 31)
    df = df[(df["publish_date"] >= _qs) & (df["publish_date"] <= _qe)]
elif isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    s_date, e_date = date_range
    df = df[(df["publish_date"] >= s_date) & (df["publish_date"] <= e_date)]

# 7c. Search
if search_q.strip():
    sq = search_q.strip()
    df = df[
        df["channel_title"].str.contains(sq, case=False, na=False)
        | df["title"].str.contains(sq, case=False, na=False)
    ]

# ─────────────────────────────────────────────────────────────────────────────
# 8. HERO HEADER  (pure HTML component — not subject to Streamlit CSS stripping)
# ─────────────────────────────────────────────────────────────────────────────
components.html(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
  .hero {{
    background: linear-gradient(135deg,#0a0a0f 0%,#12001a 50%,#0a0a0f 100%);
    border: 1px solid #252540;
    border-radius: 14px;
    padding: 28px 32px 22px;
    text-align: center;
    font-family: 'Inter', sans-serif;
    position: relative;
    overflow: hidden;
  }}
  .hero::before {{
    content:'';
    position:absolute; inset:0;
    background: radial-gradient(ellipse at 50% -20%, rgba(229,9,20,.18) 0%, transparent 65%);
    pointer-events: none;
  }}
  .hero-tag  {{ font-size:.75rem; color:#e50914; letter-spacing:.15em;
               text-transform:uppercase; font-weight:700; margin-bottom:8px; }}
  .hero-title{{ font-size:2rem; font-weight:900; color:#e2e2f0;
               line-height:1.15; margin:0 0 8px; }}
  .hero-title span {{ color:#e50914; }}
  .hero-sub  {{ font-size:.9rem; color:#8b8fa8; margin:0; }}
  .hero-badge{{
    display:inline-block; margin-top:12px;
    background:#1a1a2e; border:1px solid #252540;
    border-radius:999px; padding:4px 16px;
    font-size:.75rem; color:#8b8fa8;
  }}
  .hero-badge b {{ color:#3b82f6; }}
</style>
<div class="hero">
  <div class="hero-tag">▶ YouTube Analytics Dashboard</div>
  <div class="hero-title">Trending Videos — <span>{REGION_LABEL}</span></div>
  <div class="hero-sub">Interactive insights from trending YouTube data</div>
  <div class="hero-badge">
    Showing <b>{len(df):,}</b> of {len(df_full):,} videos
  </div>
</div>
""", height=175)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 9. KPI CARDS  (SQL aggregation → animated HTML counters via JS)
# ─────────────────────────────────────────────────────────────────────────────
if len(df) == 0:
    components.html(f"""
    <div style="background:#1a0005;border:1px solid #5a0010;border-radius:12px;
                padding:28px 32px;text-align:center;font-family:sans-serif;margin:16px 0">
      <div style="font-size:2rem;margin-bottom:8px">⚠️</div>
      <div style="font-size:1.1rem;font-weight:700;color:#ff4d6d;margin-bottom:6px">
        No videos match the current filters
      </div>
      <div style="font-size:.85rem;color:#8b8fa8">
        Try widening the date range, selecting more categories, or clearing the search box.
        <br>The dataset spans <b style="color:#e2e2f0">
        {df_full['publish_date'].min()} → {df_full['publish_date'].max()}
        </b> with <b style="color:#e2e2f0">{len(df_full):,}</b> total videos.
      </div>
    </div>
    """, height=160)
    st.stop()

kpi = run_sql("""
SELECT
    COUNT(*)                               AS total_videos,
    SUM(views)                             AS total_views,
    SUM(likes)                             AS total_likes,
    SUM(comments)                          AS total_comments,
    ROUND(AVG(engagement_rate)*100, 3)     AS avg_eng_pct,
    COUNT(DISTINCT channel_title)          AS unique_channels
FROM videos
""", df).iloc[0]

def fmt_big(n: float) -> str:
    """Format large numbers as B / M / K."""
    n = float(n)
    if n >= 1e9:  return f"{n/1e9:.2f}B"
    if n >= 1e6:  return f"{n/1e6:.1f}M"
    if n >= 1e3:  return f"{n/1e3:.1f}K"
    return f"{int(n):,}"

cards_data = [
    ("🎬", "Videos",         fmt_big(kpi.total_videos),   "trending titles"),
    ("👁️", "Total Views",    fmt_big(kpi.total_views),    "across all videos"),
    ("👍", "Total Likes",    fmt_big(kpi.total_likes),    "likes received"),
    ("💬", "Comments",       fmt_big(kpi.total_comments), "total comments"),
    ("💥", "Avg Engagement", f"{kpi.avg_eng_pct:.2f}%",   "(likes+comments)/views"),
    ("📡", "Channels",       fmt_big(kpi.unique_channels), "unique creators"),
]

kpi_html = '<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:4px">'
for icon, label, value, sub in cards_data:
    kpi_html += f"""
    <div class="kpi-card">
      <div class="kpi-icon">{icon}</div>
      <div class="kpi-label">{label}</div>
      <div class="kpi-val">{value}</div>
      <div class="kpi-sub">{sub}</div>
    </div>"""
kpi_html += "</div>"

# Inject alongside the CSS already on-page
st.markdown(kpi_html, unsafe_allow_html=True)
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 10. TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_ov, tab_tr, tab_cat, tab_ch, tab_tags, tab_corr, tab_raw = st.tabs(
    ["📊  Overview", "📈  Trends", "🗂  Categories", "📡  Channels",
     "🏷  Tags", "🔬  Correlations", "🗃  Raw Data"]
)

# ── shared Plotly layout defaults ──
DARK_LAYOUT = dict(
    plot_bgcolor="#0d0d18",
    paper_bgcolor="#0d0d18",
    font_color="#c0c0d8",
    margin=dict(l=12, r=12, t=20, b=12),
    legend=dict(bgcolor="#13131f", bordercolor="#252540", borderwidth=1,
                font_color="#c0c0d8"),
    hoverlabel=dict(bgcolor="#1a1a2e", font_color="#e2e2f0",
                    bordercolor="#e50914"),
)

def apply_dark(fig, height=380):
    fig.update_layout(**DARK_LAYOUT, height=height)
    fig.update_xaxes(gridcolor="#1e1e30", zerolinecolor="#1e1e30")
    fig.update_yaxes(gridcolor="#1e1e30", zerolinecolor="#1e1e30")
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab_ov:

    # ── Top 10 videos by views ──
    top10 = run_sql("""
        SELECT title, channel_title, category, views, likes, comments,
               ROUND(engagement_rate*100,2) AS eng_pct
        FROM videos ORDER BY views DESC LIMIT 10
    """, df)

    st.markdown('<div class="section-title">🏆 Top 10 Videos by Views</div>',
                unsafe_allow_html=True)
    fig_t10 = px.bar(
        top10, x="views", y="title", orientation="h",
        color="eng_pct", color_continuous_scale="Reds",
        hover_data=["channel_title", "category", "likes", "comments"],
        labels={"views": "Views", "title": "", "eng_pct": "Engage %"},
        template="plotly_dark",
    )
    fig_t10.update_layout(yaxis={"categoryorder": "total ascending"},
                          coloraxis_colorbar=dict(title="Engage %",
                                                  tickfont_color="#ccc"))
    apply_dark(fig_t10, 430)
    st.plotly_chart(fig_t10, use_container_width=True)

    col_l, col_r = st.columns(2)

    # ── Scatter: Views vs Engagement ──
    with col_l:
        st.markdown('<div class="section-title">📌 Views vs Engagement Rate</div>',
                    unsafe_allow_html=True)
        sample_df = df.sample(min(2500, len(df)), random_state=7)
        fig_sc = px.scatter(
            sample_df, x="views", y="engagement_rate",
            color="category", size="likes_size",
            size_max=20, log_x=True,
            hover_data=["title", "channel_title"],
            labels={"views": "Views (log scale)", "engagement_rate": "Engagement Rate"},
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Vivid,
        )
        apply_dark(fig_sc, 370)
        st.plotly_chart(fig_sc, use_container_width=True)

    # ── Heatmap: Publish hour vs day ──
    with col_r:
        st.markdown('<div class="section-title">🕐 Publish Hour × Day of Week</div>',
                    unsafe_allow_html=True)
        DAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        heat = (
            df.groupby(["publish_day", "publish_hour"])["views"]
            .mean().reset_index(name="avg_views")
        )
        if len(heat) >= 2:
            pivot = (
                heat.pivot(index="publish_day", columns="publish_hour", values="avg_views")
                .fillna(0)
                .reindex([d for d in DAY_ORDER if d in heat["publish_day"].values])
            )
            fig_heat = go.Figure(go.Heatmap(
                z=pivot.values,
                x=[f"{h:02d}h" for h in pivot.columns],
                y=pivot.index.tolist(),
                colorscale="Inferno",
                hoverongaps=False,
                hovertemplate="Day:%{y}  Hour:%{x}<br>Avg Views:%{z:,.0f}<extra></extra>",
            ))
            apply_dark(fig_heat, 370)
            fig_heat.update_layout(
                xaxis_tickfont_size=8,
                yaxis_tickfont_size=10,
            )
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("Not enough data to build the heatmap for the current filter.")

    # ── Likes vs Comments bubble ──
    st.markdown('<div class="section-title">🫧 Likes vs Comments (bubble = views)</div>',
                unsafe_allow_html=True)
    bub_df = df.sample(min(1500, len(df)), random_state=99)
    fig_bub = px.scatter(
        bub_df, x="likes", y="comments",
        size="likes_size", color="category",
        hover_data=["title", "channel_title", "views"],
        log_x=True, log_y=True, size_max=22,
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Bold,
        labels={"likes": "Likes (log)", "comments": "Comments (log)"},
    )
    apply_dark(fig_bub, 360)
    st.plotly_chart(fig_bub, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TRENDS
# ══════════════════════════════════════════════════════════════════════════════
with tab_tr:

    daily = run_sql("""
        SELECT publish_date,
               COUNT(*)   AS video_count,
               SUM(views) AS total_views,
               SUM(likes) AS total_likes,
               ROUND(AVG(engagement_rate)*100,3) AS avg_eng
        FROM videos
        GROUP BY publish_date
        ORDER BY publish_date
    """, df)
    daily["publish_date"] = pd.to_datetime(daily["publish_date"], format="mixed", dayfirst=False)

    st.markdown('<div class="section-title">📈 Daily Total Views</div>',
                unsafe_allow_html=True)
    fig_dv = px.area(
        daily, x="publish_date", y="total_views",
        template="plotly_dark",
        color_discrete_sequence=["#e50914"],
        labels={"total_views": "Total Views", "publish_date": "Date"},
    )
    fig_dv.update_traces(fillcolor="rgba(229,9,20,.18)", line_width=2)
    apply_dark(fig_dv, 290)
    st.plotly_chart(fig_dv, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-title">📅 Daily Video Count</div>',
                    unsafe_allow_html=True)
        fig_dc = px.bar(
            daily, x="publish_date", y="video_count",
            color="video_count", color_continuous_scale="Blues",
            template="plotly_dark",
            labels={"video_count": "# Videos", "publish_date": "Date"},
        )
        apply_dark(fig_dc, 290)
        st.plotly_chart(fig_dc, use_container_width=True)

    with c2:
        st.markdown('<div class="section-title">💥 Daily Avg Engagement (%)</div>',
                    unsafe_allow_html=True)
        fig_de = px.line(
            daily, x="publish_date", y="avg_eng",
            template="plotly_dark",
            color_discrete_sequence=["#3b82f6"],
            markers=True,
            labels={"avg_eng": "Avg Engagement %", "publish_date": "Date"},
        )
        fig_de.update_traces(line_width=2.5, marker_size=5)
        apply_dark(fig_de, 290)
        st.plotly_chart(fig_de, use_container_width=True)

    # Hour-of-day avg views
    st.markdown('<div class="section-title">🕐 Avg Views by Publish Hour (UTC)</div>',
                unsafe_allow_html=True)
    hour_df = run_sql("""
        SELECT publish_hour,
               ROUND(AVG(views),0) AS avg_views,
               COUNT(*) AS n
        FROM videos GROUP BY publish_hour ORDER BY publish_hour
    """, df)
    fig_hr = px.bar(
        hour_df, x="publish_hour", y="avg_views",
        color="avg_views", color_continuous_scale="Plasma",
        template="plotly_dark",
        text_auto=".2s",
        labels={"publish_hour": "Hour (UTC)", "avg_views": "Avg Views"},
    )
    fig_hr.update_traces(textfont_color="#e2e2f0")
    apply_dark(fig_hr, 290)
    st.plotly_chart(fig_hr, use_container_width=True)

    # Day-of-week avg views
    st.markdown('<div class="section-title">📆 Avg Views by Day of Week</div>',
                unsafe_allow_html=True)
    day_df = run_sql("""
        SELECT publish_day,
               ROUND(AVG(views),0) AS avg_views,
               ROUND(AVG(engagement_rate)*100,3) AS avg_eng
        FROM videos GROUP BY publish_day
    """, df)
    DAY_ORDER_SHORT = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    day_df["day_num"] = day_df["publish_day"].apply(
        lambda d: DAY_ORDER_SHORT.index(d) if d in DAY_ORDER_SHORT else 7
    )
    day_df = day_df.sort_values("day_num")
    fig_dw = px.bar(
        day_df, x="publish_day", y="avg_views",
        color="avg_eng", color_continuous_scale="Turbo",
        template="plotly_dark",
        labels={"publish_day": "Day", "avg_views": "Avg Views", "avg_eng": "Avg Engage %"},
        text_auto=".2s",
    )
    fig_dw.update_traces(textfont_color="#e2e2f0")
    apply_dark(fig_dw, 290)
    st.plotly_chart(fig_dw, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CATEGORIES
# ══════════════════════════════════════════════════════════════════════════════
with tab_cat:

    cat_df = run_sql("""
        SELECT category,
               COUNT(*)                          AS video_count,
               SUM(views)                        AS total_views,
               SUM(likes)                        AS total_likes,
               SUM(comments)                     AS total_comments,
               ROUND(AVG(engagement_rate)*100,3) AS avg_eng,
               ROUND(AVG(views),0)               AS avg_views
        FROM videos
        GROUP BY category
        ORDER BY total_views DESC
    """, df)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="section-title">🍩 Views Share by Category</div>',
                    unsafe_allow_html=True)
        fig_pie = px.pie(
            cat_df, values="total_views", names="category",
            template="plotly_dark", hole=0.38,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_pie.update_traces(
            textinfo="label+percent", textfont_size=10,
            hovertemplate="<b>%{label}</b><br>Views: %{value:,}<br>Share: %{percent}<extra></extra>",
        )
        apply_dark(fig_pie, 410)
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        st.markdown('<div class="section-title">💥 Avg Engagement by Category</div>',
                    unsafe_allow_html=True)
        fig_ceng = px.bar(
            cat_df.sort_values("avg_eng", ascending=True),
            x="avg_eng", y="category", orientation="h",
            color="avg_eng", color_continuous_scale="Turbo",
            template="plotly_dark", text_auto=".2f",
            labels={"avg_eng": "Avg Engage %", "category": ""},
        )
        fig_ceng.update_traces(textfont_color="#e2e2f0")
        apply_dark(fig_ceng, 410)
        st.plotly_chart(fig_ceng, use_container_width=True)

    # Treemap
    st.markdown('<div class="section-title">🌳 Category Treemap (size=views, color=engagement)</div>',
                unsafe_allow_html=True)
    fig_tree = px.treemap(
        cat_df, path=["category"], values="total_views",
        color="avg_eng", color_continuous_scale="RdYlGn",
        template="plotly_dark",
        hover_data={"video_count": True, "avg_views": True},
        labels={"avg_eng": "Avg Engage %"},
    )
    apply_dark(fig_tree, 360)
    st.plotly_chart(fig_tree, use_container_width=True)

    # Summary table with inline HTML progress bars
    st.markdown('<div class="section-title">📊 Category Summary</div>',
                unsafe_allow_html=True)
    max_tv = cat_df["total_views"].max()
    rows_html = ""
    for _, row in cat_df.iterrows():
        pct = int(row["total_views"] / max_tv * 100) if max_tv > 0 else 0
        rows_html += f"""
        <tr>
          <td style="padding:8px 12px;color:#e2e2f0">{row['category']}</td>
          <td style="padding:8px 12px;color:#3b82f6;text-align:right">{int(row['video_count']):,}</td>
          <td style="padding:8px 12px;min-width:160px">
            <div style="color:#e2e2f0;margin-bottom:3px">{fmt_big(row['total_views'])}</div>
            <div class="prog-wrap"><div class="prog-bar" style="width:{pct}%"></div></div>
          </td>
          <td style="padding:8px 12px;color:#a8e6cf;text-align:right">{fmt_big(row['total_likes'])}</td>
          <td style="padding:8px 12px;color:#e50914;text-align:right">{row['avg_eng']:.2f}%</td>
          <td style="padding:8px 12px;color:#8b8fa8;text-align:right">{fmt_big(row['avg_views'])}</td>
        </tr>"""

    components.html(f"""
    <style>
      .cat-table {{ width:100%;border-collapse:collapse;font-family:sans-serif;font-size:.85rem; }}
      .cat-table thead th {{ background:#1a1a2e;color:#8b8fa8;padding:10px 12px;
                             text-align:left;font-weight:600;letter-spacing:.05em;
                             text-transform:uppercase;font-size:.72rem; }}
      .cat-table tbody tr {{ background:#13131f;border-bottom:1px solid #252540; }}
      .cat-table tbody tr:hover {{ background:#1c1c30; }}
      .prog-wrap {{ background:#252540;border-radius:4px;height:5px; }}
      .prog-bar  {{ background:#e50914;border-radius:4px;height:5px; }}
    </style>
    <table class="cat-table">
      <thead>
        <tr>
          <th>Category</th><th>Videos</th><th>Total Views</th>
          <th>Total Likes</th><th>Avg Engage %</th><th>Avg Views</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    """, height=min(45 * len(cat_df) + 55, 600), scrolling=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — CHANNELS
# ══════════════════════════════════════════════════════════════════════════════
with tab_ch:

    chan25 = run_sql("""
        SELECT channel_title, category,
               COUNT(*) AS video_count,
               SUM(views) AS total_views,
               SUM(likes) AS total_likes,
               ROUND(AVG(engagement_rate)*100,3) AS avg_eng,
               ROUND(AVG(views),0) AS avg_views
        FROM videos
        GROUP BY channel_title
        ORDER BY total_views DESC
        LIMIT 25
    """, df)

    st.markdown('<div class="section-title">📡 Top 25 Channels by Total Views</div>',
                unsafe_allow_html=True)
    fig_ch25 = px.bar(
        chan25, x="total_views", y="channel_title", orientation="h",
        color="avg_eng", color_continuous_scale="Viridis",
        hover_data=["category", "video_count", "total_likes"],
        template="plotly_dark",
        labels={"total_views": "Total Views", "channel_title": "",
                "avg_eng": "Avg Engage %"},
    )
    fig_ch25.update_layout(yaxis={"categoryorder": "total ascending"})
    apply_dark(fig_ch25, 600)
    st.plotly_chart(fig_ch25, use_container_width=True)

    cl, cr = st.columns(2)

    with cl:
        st.markdown('<div class="section-title">🔥 Top 15 by Avg Engagement (≥3 videos)</div>',
                    unsafe_allow_html=True)
        eng15 = run_sql("""
            SELECT channel_title,
                   ROUND(AVG(engagement_rate)*100,3) AS avg_eng,
                   COUNT(*) AS n
            FROM videos
            GROUP BY channel_title
            HAVING n >= 3
            ORDER BY avg_eng DESC
            LIMIT 15
        """, df)
        fig_e15 = px.bar(
            eng15, x="avg_eng", y="channel_title", orientation="h",
            color="avg_eng", color_continuous_scale="Hot",
            text_auto=".2f", template="plotly_dark",
            labels={"avg_eng": "Avg Engage %", "channel_title": ""},
        )
        fig_e15.update_layout(yaxis={"categoryorder": "total ascending"})
        fig_e15.update_traces(textfont_color="#e2e2f0")
        apply_dark(fig_e15, 410)
        st.plotly_chart(fig_e15, use_container_width=True)

    with cr:
        st.markdown('<div class="section-title">📈 Top 15 by Avg Views/Video (≥3 videos)</div>',
                    unsafe_allow_html=True)
        avg15 = run_sql("""
            SELECT channel_title,
                   ROUND(AVG(views),0) AS avg_views,
                   COUNT(*) AS n
            FROM videos
            GROUP BY channel_title
            HAVING n >= 3
            ORDER BY avg_views DESC
            LIMIT 15
        """, df)
        fig_a15 = px.bar(
            avg15, x="avg_views", y="channel_title", orientation="h",
            color="avg_views", color_continuous_scale="Teal",
            text_auto=".2s", template="plotly_dark",
            labels={"avg_views": "Avg Views / Video", "channel_title": ""},
        )
        fig_a15.update_layout(yaxis={"categoryorder": "total ascending"})
        fig_a15.update_traces(textfont_color="#e2e2f0")
        apply_dark(fig_a15, 410)
        st.plotly_chart(fig_a15, use_container_width=True)

    # Category distribution of top-50 channels
    st.markdown('<div class="section-title">🗂 Category Mix — Top 50 Channels</div>',
                unsafe_allow_html=True)
    cat_mix = run_sql("""
        SELECT category, COUNT(*) AS n
        FROM (
          SELECT channel_title, category, SUM(views) AS tv
          FROM videos GROUP BY channel_title
          ORDER BY tv DESC LIMIT 50
        )
        GROUP BY category ORDER BY n DESC
    """, df)
    fig_mix = px.pie(
        cat_mix, values="n", names="category", template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig_mix.update_traces(textinfo="label+percent")
    apply_dark(fig_mix, 320)
    st.plotly_chart(fig_mix, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — TAGS
# ══════════════════════════════════════════════════════════════════════════════
with tab_tags:
    # Build a flat list of all tags from the filtered DataFrame
    all_tags_series = (
        df["tags"]
        .fillna("")
        .str.split(r"[|;]")          # tags separated by | or ;
        .explode()
        .str.strip()
        .str.lower()
        .replace("", pd.NA)
        .dropna()
    )
    tag_counts = all_tags_series.value_counts().reset_index()
    tag_counts.columns = ["tag", "count"]

    if tag_counts.empty:
        st.info("No tag data available for the current filter.")
    else:
        c1, c2 = st.columns([2, 1])

        with c1:
            st.markdown('<div class="section-title">🔝 Top 40 Tags by Frequency</div>',
                        unsafe_allow_html=True)
            fig_tags = px.bar(
                tag_counts.head(40),
                x="count", y="tag", orientation="h",
                color="count", color_continuous_scale="Reds",
                template="plotly_dark",
                labels={"count": "Frequency", "tag": ""},
                text_auto=True,
            )
            fig_tags.update_layout(yaxis={"categoryorder": "total ascending"})
            fig_tags.update_traces(textfont_color="#e2e2f0", textposition="outside")
            apply_dark(fig_tags, 700)
            st.plotly_chart(fig_tags, use_container_width=True)

        with c2:
            st.markdown('<div class="section-title">☁️ Tag Word Cloud</div>',
                        unsafe_allow_html=True)
            # Build a CSS-only word cloud using font-size scaled to frequency
            top_wc = tag_counts.head(60)
            max_c = top_wc["count"].max()
            min_c = top_wc["count"].min()
            import random as _rnd
            _rnd.seed(42)
            COLORS = ["#e50914","#3b82f6","#10b981","#f59e0b","#8b5cf6",
                      "#06b6d4","#f97316","#84cc16","#ec4899","#64748b"]
            cloud_html = '<div style="line-height:2.2;padding:8px">'
            for _, row in top_wc.iterrows():
                sz = 0.7 + 1.8 * (row["count"] - min_c) / max(max_c - min_c, 1)
                col = _rnd.choice(COLORS)
                _cnt = int(row["count"])
                _tag = row["tag"]
                cloud_html += (
                    f'<span style="font-size:{sz:.2f}rem;color:{col};'
                    f'margin:3px 5px;display:inline-block;font-weight:600;'
                    f'cursor:default" title="{_cnt} videos">'
                    f'{_tag}</span>'
                )
            cloud_html += "</div>"
            components.html(
                f'<div style="background:#13131f;border:1px solid #252540;'
                f'border-radius:10px;padding:14px;min-height:460px">{cloud_html}</div>',
                height=500, scrolling=True,
            )

        # Tag count per category (heatmap)
        st.markdown('<div class="section-title">🗂 Tag Frequency by Category</div>',
                    unsafe_allow_html=True)
        # Join tags back with category
        tag_cat = (
            df[["category", "tags"]].copy()
            .assign(tags=df["tags"].fillna("").str.split(r"[|;]"))
            .explode("tags")
            .assign(tags=lambda x: x["tags"].str.strip().str.lower())
            .query("tags != ''")
        )
        # Top 20 tags × category pivot
        top20_tags = tag_counts.head(20)["tag"].tolist()
        tc_pivot = (
            tag_cat[tag_cat["tags"].isin(top20_tags)]
            .groupby(["category", "tags"])
            .size()
            .reset_index(name="n")
            .pivot(index="category", columns="tags", values="n")
            .fillna(0)
        )
        if not tc_pivot.empty:
            fig_tch = go.Figure(go.Heatmap(
                z=tc_pivot.values,
                x=tc_pivot.columns.tolist(),
                y=tc_pivot.index.tolist(),
                colorscale="Reds",
                hovertemplate="Category:%{y}<br>Tag:%{x}<br>Count:%{z:.0f}<extra></extra>",
            ))
            apply_dark(fig_tch, 360)
            fig_tch.update_layout(
                xaxis_tickangle=-35,
                xaxis_tickfont_size=9,
            )
            st.plotly_chart(fig_tch, use_container_width=True)

        # Tags per video vs engagement
        st.markdown('<div class="section-title">🏷 Tag Count vs Engagement Rate</div>',
                    unsafe_allow_html=True)
        df_tc = df.copy()
        df_tc["tag_count"] = (
            df_tc["tags"].fillna("").str.split(r"[|;]")
            .apply(lambda x: len([t for t in x if t.strip()]))
        )
        tc_eng = run_sql("""
            SELECT tag_count,
                   ROUND(AVG(engagement_rate)*100, 3) AS avg_eng,
                   ROUND(AVG(views), 0) AS avg_views,
                   COUNT(*) AS n
            FROM videos
            GROUP BY tag_count
            HAVING n >= 3
            ORDER BY tag_count
        """, df_tc)
        fig_tce = px.scatter(
            tc_eng, x="tag_count", y="avg_eng",
            size="n", color="avg_views",
            color_continuous_scale="Viridis",
            template="plotly_dark",
            labels={"tag_count": "Number of Tags", "avg_eng": "Avg Engagement %",
                    "n": "Video Count", "avg_views": "Avg Views"},
            hover_data=["n", "avg_views"],
        )
        apply_dark(fig_tce, 320)
        st.plotly_chart(fig_tce, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — CORRELATIONS / PERFORMANCE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab_corr:
    st.markdown('<div class="section-title">🔬 What Drives Views & Engagement?</div>',
                unsafe_allow_html=True)

    # ── Title length vs views + engagement ──
    df_tl = df.copy()
    df_tl["title_len"] = df_tl["title"].str.len().fillna(0).astype(int)
    # Bucket into ranges
    df_tl["title_bucket"] = pd.cut(
        df_tl["title_len"],
        bins=[0, 30, 50, 70, 90, 110, 300],
        labels=["<30", "30-50", "50-70", "70-90", "90-110", "110+"],
    )
    tl_agg = run_sql("""
        SELECT title_bucket,
               COUNT(*) AS n,
               ROUND(AVG(views), 0) AS avg_views,
               ROUND(AVG(engagement_rate)*100, 3) AS avg_eng
        FROM videos
        GROUP BY title_bucket
        ORDER BY title_bucket
    """, df_tl)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-title">📝 Title Length vs Avg Views</div>',
                    unsafe_allow_html=True)
        fig_tl_v = px.bar(
            tl_agg, x="title_bucket", y="avg_views",
            color="avg_views", color_continuous_scale="Blues",
            text_auto=".2s", template="plotly_dark",
            labels={"title_bucket": "Title Length (chars)", "avg_views": "Avg Views"},
        )
        fig_tl_v.update_traces(textfont_color="#e2e2f0")
        apply_dark(fig_tl_v, 300)
        st.plotly_chart(fig_tl_v, use_container_width=True)

    with c2:
        st.markdown('<div class="section-title">📝 Title Length vs Avg Engagement</div>',
                    unsafe_allow_html=True)
        fig_tl_e = px.bar(
            tl_agg, x="title_bucket", y="avg_eng",
            color="avg_eng", color_continuous_scale="Reds",
            text_auto=".2f", template="plotly_dark",
            labels={"title_bucket": "Title Length (chars)", "avg_eng": "Avg Engagement %"},
        )
        fig_tl_e.update_traces(textfont_color="#e2e2f0")
        apply_dark(fig_tl_e, 300)
        st.plotly_chart(fig_tl_e, use_container_width=True)

    # ── Category × Hour heatmap (avg views) ──
    st.markdown('<div class="section-title">🗂 Avg Views: Category × Publish Hour</div>',
                unsafe_allow_html=True)
    cat_hour = run_sql("""
        SELECT category, publish_hour,
               ROUND(AVG(views), 0) AS avg_views
        FROM videos
        GROUP BY category, publish_hour
    """, df)
    if len(cat_hour) >= 2:
        ch_pivot = (
            cat_hour
            .pivot(index="category", columns="publish_hour", values="avg_views")
            .fillna(0)
        )
        fig_ch = go.Figure(go.Heatmap(
            z=ch_pivot.values,
            x=[f"{h:02d}h" for h in ch_pivot.columns],
            y=ch_pivot.index.tolist(),
            colorscale="Plasma",
            hovertemplate="Category:%{y}<br>Hour:%{x}<br>Avg Views:%{z:,.0f}<extra></extra>",
        ))
        apply_dark(fig_ch, 380)
        fig_ch.update_layout(xaxis_tickfont_size=8)
        st.plotly_chart(fig_ch, use_container_width=True)

    # ── Views distribution (log histogram) ──
    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="section-title">📊 Views Distribution (log scale)</div>',
                    unsafe_allow_html=True)
        fig_vdist = px.histogram(
            df[df["views"] > 0], x="views",
            nbins=60, log_x=True, log_y=True,
            template="plotly_dark",
            color_discrete_sequence=["#e50914"],
            labels={"views": "Views (log)"},
        )
        apply_dark(fig_vdist, 300)
        st.plotly_chart(fig_vdist, use_container_width=True)

    with c4:
        st.markdown('<div class="section-title">📊 Engagement Rate Distribution</div>',
                    unsafe_allow_html=True)
        fig_edist = px.histogram(
            df[df["engagement_rate"] < df["engagement_rate"].quantile(0.99)],
            x="engagement_rate",
            nbins=60, template="plotly_dark",
            color_discrete_sequence=["#3b82f6"],
            labels={"engagement_rate": "Engagement Rate"},
        )
        apply_dark(fig_edist, 300)
        st.plotly_chart(fig_edist, use_container_width=True)

    # ── Category performance radar ──
    st.markdown('<div class="section-title">🕸 Category Performance Radar</div>',
                unsafe_allow_html=True)
    radar_df = run_sql("""
        SELECT category,
               ROUND(AVG(views)/1e6, 3)              AS avg_views_m,
               ROUND(AVG(likes)/1000, 3)             AS avg_likes_k,
               ROUND(AVG(comments)/1000, 3)          AS avg_comments_k,
               ROUND(AVG(engagement_rate)*100, 3)    AS avg_eng_pct,
               COUNT(*)                              AS video_count
        FROM videos
        GROUP BY category
        ORDER BY avg_views_m DESC
    """, df)
    # Normalise each metric 0–1 for radar
    radar_metrics = ["avg_views_m", "avg_likes_k", "avg_comments_k", "avg_eng_pct"]
    radar_norm = radar_df.copy()
    for m in radar_metrics:
        col_max = radar_norm[m].max()
        radar_norm[m] = (radar_norm[m] / col_max * 100).round(1) if col_max > 0 else 0
    fig_radar = go.Figure()
    for _, row in radar_norm.head(8).iterrows():
        vals = [row[m] for m in radar_metrics]
        vals.append(vals[0])  # close polygon
        fig_radar.add_trace(go.Scatterpolar(
            r=vals,
            theta=["Avg Views", "Avg Likes", "Avg Comments", "Avg Engage %", "Avg Views"],
            fill="toself", opacity=0.55,
            name=row["category"],
        ))
    apply_dark(fig_radar, 450)
    fig_radar.update_layout(
        polar=dict(
            bgcolor="#0d0d18",
            radialaxis=dict(visible=True, range=[0, 100], color="#555",
                            gridcolor="#252540"),
            angularaxis=dict(color="#8b8fa8", gridcolor="#252540"),
        ),
        legend=dict(font_size=10),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — RAW DATA
# ══════════════════════════════════════════════════════════════════════════════
with tab_raw:
    st.markdown('<div class="section-title">🗃 Filtered Dataset</div>',
                unsafe_allow_html=True)

    # ── Column selector ──
    ALL_DISPLAY_COLS = [
        "title", "channel_title", "category", "views", "likes",
        "comments", "dislikes", "engagement_rate",
        "publish_date", "publish_day", "publish_hour",
    ]
    sel_cols = st.multiselect(
        "📋 Columns to display",
        options=ALL_DISPLAY_COLS,
        default=["title", "channel_title", "category", "views", "likes",
                 "comments", "engagement_rate", "publish_date"],
        key="raw_col_sel",
    )
    if not sel_cols:
        sel_cols = ALL_DISPLAY_COLS

    # ── Sort control ──
    sort_col, sort_dir_col = st.columns([3, 1])
    with sort_col:
        sort_by = st.selectbox(
            "⬆️ Sort by",
            options=sel_cols,
            index=sel_cols.index("views") if "views" in sel_cols else 0,
            key="raw_sort_col",
        )
    with sort_dir_col:
        sort_asc = st.radio("Order", ["↓ Desc", "↑ Asc"],
                            index=0, key="raw_sort_dir", horizontal=True)

    raw = df[sel_cols].copy()
    if "engagement_rate" in raw.columns:
        raw["engagement_rate"] = raw["engagement_rate"].round(4)

    # ── Row search ──
    ts = st.text_input("🔍 Filter rows by title / channel",
                       placeholder="Type to filter…", key="raw_tab_search")
    if ts.strip():
        masks = []
        if "title" in raw.columns:
            masks.append(raw["title"].str.contains(ts, case=False, na=False))
        if "channel_title" in raw.columns:
            masks.append(raw["channel_title"].str.contains(ts, case=False, na=False))
        if masks:
            raw = raw[masks[0] if len(masks) == 1 else (masks[0] | masks[1])]

    # ── Apply sort ──
    raw = raw.sort_values(sort_by, ascending=(sort_asc == "↑ Asc")).reset_index(drop=True)

    st.caption(f"Showing **{len(raw):,}** rows  ·  sorted by **{sort_by}** ({sort_asc})")
    st.dataframe(raw, use_container_width=True, height=480)

    # ── Download ──
    dl_c1, dl_c2 = st.columns(2)
    with dl_c1:
        csv_out = raw.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️  Download filtered CSV",
            data=csv_out,
            file_name="yt_trending_filtered.csv",
            mime="text/csv",
        )
    with dl_c2:
        # Full dataset export
        full_csv = df[ALL_DISPLAY_COLS].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️  Download full dataset CSV",
            data=full_csv,
            file_name="yt_trending_full.csv",
            mime="text/csv",
        )

# ─────────────────────────────────────────────────────────────────────────────
# 11. AUTO-GENERATED KEY INSIGHTS  (outside tabs — always visible)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title">🧠 Auto-Generated Key Insights</div>',
            unsafe_allow_html=True)

ins = run_sql("""
    SELECT COUNT(*) AS n,
           SUM(views) AS tv, MAX(views) AS mx_views,
           ROUND(AVG(views),0) AS avg_views,
           ROUND(AVG(engagement_rate)*100,4) AS avg_eng,
           ROUND(MAX(engagement_rate)*100,2)  AS max_eng,
           ROUND(AVG(likes),0) AS avg_likes,
           COUNT(DISTINCT category)           AS n_cats,
           COUNT(DISTINCT channel_title)      AS n_chans
    FROM videos
""", df).iloc[0]

top_cat     = run_sql("SELECT category, SUM(views) AS v FROM videos GROUP BY category ORDER BY v DESC LIMIT 1", df).iloc[0]
top_chan     = run_sql("SELECT channel_title, SUM(views) AS v FROM videos GROUP BY channel_title ORDER BY v DESC LIMIT 1", df).iloc[0]
top_hour    = run_sql("SELECT publish_hour, COUNT(*) AS n FROM videos GROUP BY publish_hour ORDER BY n DESC LIMIT 1", df).iloc[0]
best_day    = run_sql("SELECT publish_day, ROUND(AVG(engagement_rate)*100,2) AS e FROM videos GROUP BY publish_day ORDER BY e DESC LIMIT 1", df).iloc[0]
top_eng_cat = run_sql("SELECT category, ROUND(AVG(engagement_rate)*100,2) AS e FROM videos GROUP BY category ORDER BY e DESC LIMIT 1", df).iloc[0]

# ── Percentile ranks vs full dataset ──
_full_med_views = float(df_full["views"].median())
_full_med_eng   = float((df_full["engagement_rate"] * 100).median())
_filt_avg_views = float(ins.avg_views)
_filt_avg_eng   = float(ins.avg_eng)
_views_vs = ((_filt_avg_views - _full_med_views) / max(_full_med_views, 1) * 100)
_eng_vs   = ((_filt_avg_eng   - _full_med_eng)   / max(_full_med_eng,   1) * 100)

def _pct_arrow(val: float) -> str:
    if val > 5:   return f'<span style="color:#10b981">▲ {val:+.1f}% vs full dataset</span>'
    if val < -5:  return f'<span style="color:#ef4444">▼ {val:+.1f}% vs full dataset</span>'
    return f'<span style="color:#8b8fa8">≈ inline with full dataset</span>'

# Top tag in this filter
_tags_flat = df["tags"].fillna("").str.split(r"[|;]").explode().str.strip().str.lower()
_tags_flat = _tags_flat[_tags_flat != ""]
_top_tag   = _tags_flat.value_counts().index[0] if len(_tags_flat) > 0 else "—"

insight_points = [
    (f"📹 <b>{int(ins.n):,} videos</b> from <b>{int(ins.n_chans):,} channels</b> across "
     f"<b>{int(ins.n_cats)} categories</b> match the current filters."),

    (f"👁️ Combined views: <b>{fmt_big(ins.tv)}</b>. Single highest: <b>{fmt_big(ins.mx_views)}</b>. "
     f"Avg per video: <b>{fmt_big(ins.avg_views)}</b> — {_pct_arrow(_views_vs)}."),

    (f"🏆 Dominant category by views: <b>{top_cat.category}</b> "
     f"({fmt_big(top_cat.v)} total views)."),

    (f"💥 Highest-engaging category: <b>{top_eng_cat.category}</b> "
     f"({top_eng_cat.e:.2f}% avg). Overall avg: <b>{ins.avg_eng:.2f}%</b> — {_pct_arrow(_eng_vs)}."),

    (f"📡 Top channel: <b>{top_chan.channel_title}</b> — <b>{fmt_big(top_chan.v)}</b> views. "
     f"Avg likes per video: <b>{fmt_big(ins.avg_likes)}</b>."),

    (f"🏷 Most frequent tag in this filter: <b>{_top_tag}</b>. "
     f"Best engagement: {ins.max_eng:.2f}% (individual video peak)."),

    (f"⏰ Peak publish hour: <b>{int(top_hour.publish_hour):02d}:00 UTC</b> "
     f"— most creators release content at this time."),

    (f"📅 <b>{best_day.publish_day}</b> yields the highest avg engagement "
     f"({best_day.e:.2f}%) — the best day to publish for interaction."),
]

insight_cols = st.columns(2)
for i, point in enumerate(insight_points):
    with insight_cols[i % 2]:
        st.markdown(f'<div class="insight-box">{point}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 12. FOOTER
# ─────────────────────────────────────────────────────────────────────────────
components.html("""
<div style="text-align:center;padding:24px 0 12px;
            border-top:1px solid #252540;margin-top:32px;
            font-family:sans-serif">
  <span style="font-size:.75rem;color:#555">Made with</span>
  <span style="font-size:.75rem;color:#3b82f6;font-weight:700"> IBM Bob</span>
  <span style="font-size:.75rem;color:#555"> · YouTube Trending Analytics Dashboard</span>
</div>
""", height=55)
