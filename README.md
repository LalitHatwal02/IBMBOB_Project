# ▶ YouTube Trending Video Analytics Dashboard

An interactive analytics dashboard for YouTube trending video data, built in a **single Python file** using Streamlit, Plotly, Pandas, and SQLite3.

---

## 🔧 Backend

The backend is entirely Python-based and runs inside the same `app.py` file — no separate server or API layer.

### Core Backend Components

| Component | Library / Tool | Role |
|---|---|---|
| **Data Ingestion** | `pandas` | Reads `*_Trending.csv` with UTF-8 encoding, coerces bad values, drops unparseable rows |
| **Date Parsing** | `pandas.to_datetime` | Parses ISO 8601 `publish_time` as UTC; extracts date, day name, hour |
| **Feature Engineering** | `pandas` | Computes `engagement_rate`, `likes_size`, `tag_count`, `title_len`, `title_bucket` |
| **SQL Aggregations** | `sqlite3` (stdlib) | 19 SQL queries run on an in-memory table called `videos`; results returned as DataFrames |
| **Caching** | `@st.cache_data` | `load_and_clean()` runs once per session; re-runs only when the CSV path changes |
| **CSV Auto-Detection** | `glob` + `os` | Scans working directory for `*_Trending.csv`; derives region label from filename prefix |
| **Filtering Logic** | `pandas` boolean masks | Category, date range, year quick-select, and free-text search applied sequentially |
| **Percentile Comparison** | `pandas.median` | Compares filtered avg views and engagement against full-dataset median for insight arrows |

### SQL Query Summary (19 queries via `sqlite3`)

```sql
-- KPI aggregation
SELECT COUNT(*) AS total_videos,
       SUM(views) AS total_views,
       ROUND(AVG(engagement_rate)*100, 3) AS avg_eng_pct,
       COUNT(DISTINCT channel_title) AS unique_channels
FROM videos

-- Top 25 channels
SELECT channel_title, SUM(views) AS total_views,
       ROUND(AVG(engagement_rate)*100, 3) AS avg_eng
FROM videos
GROUP BY channel_title
ORDER BY total_views DESC LIMIT 25

-- Category x Hour heatmap
SELECT category, publish_hour, ROUND(AVG(views), 0) AS avg_views
FROM videos
GROUP BY category, publish_hour
```

All queries are scoped to the **currently filtered DataFrame** — every filter change re-runs only the affected queries.

---

## 🎨 Frontend

The frontend combines Streamlit widgets, Plotly charts, and custom HTML/CSS/JS injected via `streamlit.components.v1`.

### UI Stack

| Layer | Tool | What it Does |
|---|---|---|
| **App Framework** | `streamlit` | Page layout, tabs, sidebar, widgets, state management |
| **Charts** | `plotly.express` + `plotly.graph_objects` | 27 interactive charts — bar, area, scatter, heatmap, treemap, radar, histogram, pie |
| **Custom HTML** | `components.html()` | Hero banner, CSS word cloud, category table, footer |
| **Inline CSS** | `st.markdown(unsafe_allow_html=True)` | Full dark theme, KPI hover effects, tab styles, scrollbar, section titles, progress bars |
| **Theme Config** | `.streamlit/config.toml` | Native dark mode with `primaryColor=#e50914`, no CSS flash on load |
| **Session State** | `st.session_state` | Persists year quick-select across reruns |

### Key UI Components

| Component | Description |
|---|---|
| **Hero Banner** | Gradient background, radial red glow, Inter font, live video count badge |
| **KPI Cards (x6)** | Dark gradient cards with red top-border, hover lift animation, auto B/M/K scaling |
| **Sidebar** | Logo block, category multiselect, date picker, year buttons, search box |
| **7 Tabs** | Overview · Trends · Categories · Channels · Tags · Correlations · Raw Data |
| **CSS Word Cloud** | Pure HTML spans — font-size proportional to tag frequency, 10 accent colours |
| **Progress Bar Table** | Categories table with inline red div progress bars via `components.html` |
| **Empty-State Card** | Styled error block with dataset date range hint when filters return 0 rows |
| **Key Insights Panel** | 8 auto-generated cards in a 2-column grid, refreshed on every filter change |
| **Radar Chart** | Top 8 categories plotted across 4 normalised metrics (0–100 scale) |

### Chart Types Used (27 total)

| Type | Count | Used For |
|---|---|---|
| Horizontal Bar | 8 | Top videos, top channels, category engagement, tag frequency, title length |
| Heatmap | 4 | Publish hour x day, tag x category, category x hour, daily engagement |
| Scatter / Bubble | 3 | Views vs engagement, likes vs comments, tag count vs engagement |
| Area / Line | 3 | Daily views, daily engagement, daily video count |
| Pie / Donut | 3 | Category views share, channel category mix, top-50 channel mix |
| Histogram | 2 | Views distribution (log), engagement rate distribution |
| Treemap | 1 | Category performance (size=views, color=engagement) |
| Radar | 1 | Category performance across 4 metrics |
| HTML Table | 2 | Category summary with progress bars, Raw Data sortable table |

---

## 📂 Dataset

**File:** `IN_Trending.csv` — https://www.kaggle.com/datasets/bsthere/youtube-trending-videos-stats-2026?select=IN_Trending.csv

| Property | Value |
|---|---|
| **Rows** | 16,199 |
| **Columns** | 13 raw + 9 engineered |
| **Date Range** | 2015-12-22 to 2026-02-26 |
| **Unique Videos** | 16,199 (each video appears once) |
| **Unique Channels** | 980 |
| **Unique Categories** | 14 |
| **Total Views** | 22.2 billion |
| **Total Likes** | 651 million |
| **Total Comments** | 21.7 million |
| **Avg Engagement Rate** | 5.35% |
| **Unique Tags** | 61,018 |
| **Avg Tags per Video** | 14.7 |
| **Max Views (single video)** | 274,334,759 |

### Raw Columns

| Column | Type | Description |
|---|---|---|
| `video_id` | string | YouTube video ID |
| `trending_date` | string | Raw trending date string |
| `title` | string | Video title |
| `channel_title` | string | Channel name |
| `channel_id` | string | YouTube channel ID |
| `views` | integer | View count |
| `likes` | integer | Like count |
| `dislikes` | integer | Dislike count (all 0 — API removed) |
| `comments` | integer | Comment count |
| `publish_time` | ISO 8601 | Video publish timestamp (UTC) |
| `category_id` | integer | YouTube category code (1–29) |
| `tags` | string | Pipe-separated tag list |
| `description` | string | Video description (1,347 nulls) |

### Engineered Columns

| Column | Formula | Purpose |
|---|---|---|
| `engagement_rate` | `(likes + comments) / max(views, 1)` | Core performance metric |
| `publish_date` | `publish_time.dt.date` | Date filtering, time-series charts |
| `publish_day` | `publish_time.dt.day_name()` | Day-of-week analysis |
| `publish_hour` | `publish_time.dt.hour` | Hour-of-day analysis |
| `category` | `category_id` mapped via dict | Human-readable category label |
| `likes_size` | `likes.clip(lower=1)` | Bubble chart size (prevents zero-size points) |
| `tag_count` | `len(tags.split('[|;]'))` | Tags correlation analysis |
| `title_len` | `title.str.len()` | Title length correlation |
| `title_bucket` | `pd.cut(title_len, bins=[0,30,50,70,90,110,300])` | Bucketed title length for bar charts |

### YouTube Category ID Map

| ID | Category | ID | Category |
|---|---|---|---|
| 1 | Film & Animation | 17 | Sports |
| 2 | Autos & Vehicles | 19 | Travel & Events |
| 10 | Music | 20 | Gaming |
| 15 | Pets & Animals | 22 | People & Blogs |
| 23 | Comedy | 24 | Entertainment |
| 25 | News & Politics | 26 | Howto & Style |
| 27 | Education | 28 | Science & Technology |

---

## 🤖 ML / Statistical Methods Used

Although this is primarily an analytics dashboard (no predictive model is deployed), several **statistical and ML-adjacent techniques** are used throughout the analysis.

### Methods Applied

| Method | Where Used | Description |
|---|---|---|
| **Engagement Rate** | All tabs, KPI, insights | Composite metric: `(likes + comments) / views` — quantifies audience interaction per view |
| **Median Comparison** | Key Insights panel | Filtered avg views and engagement vs full-dataset **median** — shows relative performance with arrows |
| **Frequency Analysis** | Tags tab | `value_counts()` on exploded tag series — identifies top trending keywords by occurrence |
| **Binning / Bucketing** | Correlations tab | `pd.cut()` divides `title_len` into 6 ordered bins — reveals non-linear performance patterns |
| **Aggregation & Group-By** | All SQL queries | `AVG`, `SUM`, `COUNT`, `MAX` grouped by category, channel, hour, day — descriptive statistics |
| **Normalisation (0–100)** | Correlations radar chart | Each metric scaled as `(value / max) * 100` so disparate units are comparable on one chart |
| **Log Transformation** | Overview scatter, Correlations histograms | `log_x=True` applied to views — makes power-law-distributed data readable |
| **Pivot / Cross-tabulation** | Heatmaps (hour x day, tag x category, category x hour) | 2D cross-tabs via `df.pivot()` — reveals interaction effects between two dimensions |

### Potential ML Extensions (not yet implemented)

| Extension | Approach |
|---|---|
| **Trend Prediction** | Time-series forecasting (ARIMA / Prophet) on daily view counts |
| **Viral Video Classifier** | Binary classification using title length, tags, publish hour, category as features |
| **Engagement Regression** | Linear / gradient-boosted regression to predict engagement rate from video metadata |
| **Tag Clustering** | K-Means or TF-IDF clustering of tag sets to discover content niches |
| **Anomaly Detection** | Isolation Forest on daily view spikes |

---

## 📁 Project Structure

```
IBM_Project/
├── app.py                  # Full dashboard — backend + frontend in one file
├── IN_Trending.csv         # YouTube trending dataset (India)
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml         # Dark theme + server config
├── Procfile                # Streamlit Cloud / Heroku deployment
├── setup.sh                # Deployment setup script
└── README.md               # This file
```

---

## ✨ Features

| Feature | Details |
|---|---|
| **Auto CSV detection** | Picks up any `*_Trending.csv` — swap to any region without code changes |
| **SQL backend** | All aggregations via `sqlite3` on in-memory tables |
| **7 interactive tabs** | Overview · Trends · Categories · Channels · Tags · Correlations · Raw Data |
| **Sidebar filters** | Category multi-select, date range picker, free-text search |
| **Year quick-select** | One-click buttons to jump to any year in the dataset |
| **Animated KPI cards** | Views, Likes, Comments, Engagement %, Channels — with hover lift effect |
| **Smart number format** | Auto B / M / K — never shows `0.00B` for small filtered sets |
| **Key Insights panel** | 8 auto-generated insights with ▲/▼ comparison vs full dataset median |
| **Tags analysis** | Top-40 frequency bar, CSS word cloud, tag-category heatmap, tag count vs engagement |
| **Correlations** | Title length buckets, category × hour heatmap, distributions, radar chart |
| **Sortable Raw Data** | Column picker, sort by any column, row search, two CSV download buttons |
| **Dark theme** | Native Streamlit dark theme via `config.toml` — no flash on load |

---

## 📊 Dashboard Tabs

| Tab | Charts |
|---|---|
| 📊 **Overview** | Top-10 bar · Views vs Engagement scatter · Publish hour heatmap · Likes vs Comments bubble |
| 📈 **Trends** | Daily views area · Video count bar · Avg engagement line · Hourly bar · Day-of-week bar |
| 🗂 **Categories** | Views donut · Engagement bar · Treemap · HTML summary table with progress bars |
| 📡 **Channels** | Top-25 views bar · Top-15 engagement · Top-15 avg views · Category mix pie |
| 🏷 **Tags** | Top-40 frequency bar · CSS word cloud · Tag×Category heatmap · Tag count scatter |
| 🔬 **Correlations** | Title length vs views/engagement · Category×Hour heatmap · Distributions · Radar |
| 🗃 **Raw Data** | Column selector · Sort control · Row search · Filtered + full CSV download |

---

## 🧮 Engineered Columns

| Column | Formula |
|---|---|
| `engagement_rate` | `(likes + comments) / max(views, 1)` |
| `publish_date` | Date part of `publish_time` (UTC) |
| `publish_day` | Monday … Sunday |
| `publish_hour` | 0–23 UTC |
| `category` | Mapped from numeric `category_id` |
| `likes_size` | `likes.clip(lower=1)` — prevents zero-size bubbles |

---

## ⚙️ Setup & Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`.

---

## 📦 Requirements

```
streamlit>=1.32.0
pandas>=2.0.0
plotly>=5.18.0
```

`sqlite3` ships with Python's standard library — no extra install needed.

---

## 🌍 Multi-Region Support

Drop any `*_Trending.csv` into the project folder — the app auto-detects it and derives the region label from the filename prefix:

| File | Label |
|---|---|
| `IN_Trending.csv` | India |
| `BR_Trending.csv` | Brazil |
| `US_Trending.csv` | USA |
| `GB_Trending.csv` | UK |

---

## ⚠️ Date Filtering Notes

- The dataset spans 2015–2026 but early years have very sparse data (1–5 videos/day).
- The date picker **defaults to the last 90 days** of data on first load.
- Use **Year quick-select buttons** in the sidebar to jump to any specific year instantly.
- If a filter combination yields 0 results, a styled error card appears with guidance — the app does not crash.

---

## 🚀 Deploy to Streamlit Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Select your repo, branch, and set **Main file path** to `app.py`.
4. Click **Deploy** — the `Procfile` and `.streamlit/config.toml` handle the rest.

---

*Made with IBM Bob*
