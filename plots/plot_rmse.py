"""
plot_rmse.py
------------
Self-contained script – no functions.py needed.

Generates a 4-panel figure:
  a) Covered Variance        vs. Representative Days
  b) Correlation Error       vs. Representative Days
  c) Offshore Wind Capacity Factor duration curve
  d) Wind Duration Tail Error vs. Representative Days

Usage
-----
    python plot_rmse.py

Adjust the CONFIG section to match your paths and data files.
"""

import numpy as np
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# CONFIG – edit these to match your setup
# ---------------------------------------------------------------------------

RESULT_DIR = "../results/Input_Data/"
INPUT_DIR  = "../input/"

# Countries to include when computing the full reference time series
COUNTRIES = ["DE"]

# Cluster size string used to select the right column from Duration_*.csv
CLUSTER = "5"

# DTW-VD window to display (filters pca_v and pca_corr)
PCA_VARIANCE_WINDOW  = 5
PCA_CORR_WINDOW      = 4
PCA_DURATION_COL     = "5_4"   # column name in Duration_DTW.csv

# Input Excel file for the full reference wind time series
TIMESERIES_EXCEL = "Timeseries_renewable_ninja_2018.xlsx"
SHEET_WIND_OFF   = "TS_WIND_OFFSHORE_DEEP"
SHEET_WIND_ON    = "TS_WIND_ONSHORE_AVG"

OUTPUT_FILE = "variance2.pdf"

# ---------------------------------------------------------------------------
# Colours and method labels
# ---------------------------------------------------------------------------

# One blue shade per DTW-VD window entry (extend if you have more windows)
BLUES = [
    "rgb(230,245,255)", "rgb(210,235,250)", "rgb(190,225,245)",
    "rgb(170,215,240)", "rgb(150,205,235)", "rgb(140,195,230)",
    "rgb(131,185,225)", "rgb(121,175,220)", "rgb(111,159,204)",
    "rgb(101,153,199)", "rgb(91,147,194)",  "rgb(81,141,189)",
    "rgb(71,135,184)",  "rgb(61,129,179)",  "rgb(51,123,174)",
    "rgb(41,117,169)",  "rgb(31,111,164)",  "rgb(21,105,159)",
    "rgb(11,99,154)",   "rgb(0,93,149)",    "rgb(0,87,144)",
    "rgb(0,81,139)",    "rgb(0,75,134)",    "rgb(0,69,129)",
]

# Override to a single colour when only one window is shown
BLUES = ["#22579C"]

COLOR_PALETTE = ["#008080", "grey", "#D6695B", "#22579C"]
METHODS       = ["kmeans-c", "HC-c", "HC-m", "DTW-VD"]

THICKNESS  = 2
TICKFONT   = 13
FONTSIZE   = 14
COLORLEGEND = False   # set True to add a DTW window colour-bar legend

# ---------------------------------------------------------------------------
# 1. Read data
# ---------------------------------------------------------------------------

print("Reading distribution CSVs …")
kmeans_dis  = pd.read_csv(RESULT_DIR + "Distribution_Kmeans.csv")
centroid_dis = pd.read_csv(RESULT_DIR + "Distribution_Centroid.csv")
medoid_dis  = pd.read_csv(RESULT_DIR + "Distribution_Medoid.csv")
pca_dis     = pd.read_csv(RESULT_DIR + "Distribution_DTW.csv")
# Notebook had a typo: renamed "Maxval" → "Minval" for pca_dis
pca_dis.rename(columns={"Maxval": "Minval"}, inplace=True)

print("Reading correlation CSVs …")
kmeans_corr  = pd.read_csv(RESULT_DIR + "Correlation_Kmeans.csv")
hcc_corr     = pd.read_csv(RESULT_DIR + "Correlation_Centroid.csv")
medoid_corr  = pd.read_csv(RESULT_DIR + "Correlation_Medoid.csv")
pca_corr     = pd.read_csv(RESULT_DIR + "Correlation_DTW.csv")
pca_corr     = pca_corr[pca_corr["Window"] == PCA_CORR_WINDOW]

print("Reading duration CSVs …")
kmeans = pd.read_csv(RESULT_DIR + "Duration_Kmeans.csv")
hcc    = pd.read_csv(RESULT_DIR + "Duration_Centroid.csv")
hcc.columns = [c.split("_")[0] for c in hcc.columns]   # strip suffixes
medoid = pd.read_csv(RESULT_DIR + "Duration_Medoid.csv")
pca    = pd.read_csv(RESULT_DIR + "Duration_DTW.csv")
pca    = pca[[PCA_DURATION_COL]]

print("Reading variability CSVs …")
kmeans_v = pd.read_csv(RESULT_DIR + "Variability_Kmeans.csv")
hcc_v    = pd.read_csv(RESULT_DIR + "Variability_Centroid.csv")
medoid_v = pd.read_csv(RESULT_DIR + "Variability_Medoid.csv")
pca_v    = pd.read_csv(RESULT_DIR + "Variability_DTW.csv")
pca_v    = pca_v[pca_v["Window"] == PCA_VARIANCE_WINDOW]

print("Reading reference wind time series …")
wind_off = pd.read_excel(
    INPUT_DIR + TIMESERIES_EXCEL, sheet_name=SHEET_WIND_OFF
)[COUNTRIES]
wind_on = pd.read_excel(
    INPUT_DIR + TIMESERIES_EXCEL, sheet_name=SHEET_WIND_ON
)[COUNTRIES]
full_ts = np.array(wind_off.mean(axis=1) + wind_on.mean(axis=1)) * 0.5
full_ts.sort()   # ascending; reversed when plotting the duration curve

# ---------------------------------------------------------------------------
# 2. Build figure
# ---------------------------------------------------------------------------

# Unique sorted windows for DTW-VD variance/correlation multi-line traces
pca_windows = np.sort(pca_v["Window"].unique())
norm_windows = (
    (pca_windows - pca_windows.min()) / max(pca_windows.max() - pca_windows.min(), 1)
)

fig = make_subplots(
    rows=1, cols=4,
    subplot_titles=[
        "a) Covered Variance",
        "b) Correlation Error",
        "c) Offshore Wind Capacity Factor",
        "d) Wind Duration Tail Error",
    ],
    horizontal_spacing=0.04,
)

# --- Panel a: Covered Variance ------------------------------------------------

# kmeans-c, HC-c, HC-m
for i, df in enumerate([kmeans_v, hcc_v, medoid_v], start=1):
    fig.add_trace(go.Scatter(
        x=df["Cluster"], y=df["Value"],
        name=METHODS[i - 1],
        legendgroup=METHODS[i - 1],
        showlegend=True,
        mode="lines",
        line=dict(width=THICKNESS),
        marker=dict(color=COLOR_PALETTE[i - 1], size=6),
    ), row=1, col=1)

# DTW-VD – one line per window
for i, (w, _) in enumerate(zip(pca_windows, norm_windows)):
    df_w = pca_v[pca_v["Window"] == w]
    fig.add_trace(go.Scatter(
        x=df_w["Cluster"], y=df_w["Value"],
        name="DTW-VD",
        legendgroup=f"DTW_{w}",
        showlegend=True,
        mode="lines",
        line=dict(width=THICKNESS),
        marker=dict(color=BLUES[i % len(BLUES)], size=6),
    ), row=1, col=1)

# --- Panel b: Correlation Error -----------------------------------------------

# DTW-VD – one line per window
corr_windows = np.sort(pca_corr["Window"].unique())
for i, w in enumerate(corr_windows):
    df_w = pca_corr[pca_corr["Window"] == w]
    fig.add_trace(go.Scatter(
        x=df_w["Cluster"], y=df_w["Value"],
        name=f"{w}",
        legendgroup=w,
        showlegend=False,
        mode="lines",
        line=dict(width=THICKNESS),
        marker=dict(color=BLUES[i % len(BLUES)], size=6),
    ), row=1, col=2)

# kmeans-c, HC-c, HC-m
for i, df in enumerate([kmeans_corr, hcc_corr, medoid_corr], start=1):
    fig.add_trace(go.Scatter(
        x=df["Cluster"], y=df["Value"],
        name=METHODS[i - 1],
        legendgroup=METHODS[i - 1],
        showlegend=False,
        mode="lines",
        line=dict(width=THICKNESS),
        marker=dict(color=COLOR_PALETTE[i - 1], size=6),
    ), row=1, col=2)

# --- Panel c: Offshore Wind Capacity Factor duration curve -------------------

# DTW-VD columns (one line per column, sorted descending = duration curve)
for i, col in enumerate(pca.columns):
    fig.add_trace(go.Scatter(
        x=list(range(1, 8761)),
        y=pca[col].sort_values(ascending=False),
        name="DTW-VD",
        legendgroup="DTW-VD",
        showlegend=False,
        mode="lines",
        line=dict(width=THICKNESS),
        marker=dict(color=BLUES[i % len(BLUES)], size=6),
    ), row=1, col=3)

# kmeans-c, HC-c, HC-m
for i, df in enumerate([kmeans, hcc, medoid], start=1):
    fig.add_trace(go.Scatter(
        x=list(range(1, 8761)),
        y=df[CLUSTER].sort_values(ascending=False),
        name=METHODS[i - 1],
        legendgroup=METHODS[i - 1],
        showlegend=False,
        mode="lines",
        line=dict(width=THICKNESS),
        marker=dict(color=COLOR_PALETTE[i - 1], size=6),
    ), row=1, col=3)

# Full reference time series (plotted descending = duration curve)
fig.add_trace(go.Scatter(
    x=list(range(1, 8761)),
    y=full_ts[::-1],
    name="Full TS",
    legendgroup="Full TS",
    showlegend=True,
    mode="lines",
    marker=dict(color="#bc203e", size=6),
), row=1, col=3)

# --- Panel d: Wind Duration Tail Error ----------------------------------------

for i, df in enumerate([kmeans_dis, centroid_dis, medoid_dis, pca_dis], start=1):
    fig.add_trace(go.Scatter(
        x=df["Cluster"], y=df["Minval"],
        name=METHODS[i - 1],
        legendgroup=METHODS[i - 1],
        showlegend=False,
        mode="lines",
        line=dict(width=THICKNESS),
        marker=dict(color=COLOR_PALETTE[i - 1], size=6),
    ), row=1, col=4)

# Optional colour-bar legend for DTW window scale
if COLORLEGEND:
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="markers",
        showlegend=False,
        hoverinfo="none",
        marker=dict(
            size=0,
            color=np.linspace(pca_windows.min(), pca_windows.max(), 100),
            cmin=pca_windows.min(),
            cmax=pca_windows.max(),
            colorscale=BLUES,
            showscale=True,
            colorbar=dict(
                outlinewidth=0,
                title=dict(text="DTW<br>Window<br>", font=dict(size=16)),
                tickfont=dict(size=16),
                thickness=13,
                tickvals=[1, 2, 3, 4],
                ticktext=[str(w) for w in [1, 4]],
                len=0.9,
                x=1.03,
                y=0.6,
            ),
        ),
    ))

# ---------------------------------------------------------------------------
# 3. Layout
# ---------------------------------------------------------------------------

fig.update_layout(
    font=dict(color="black", size=FONTSIZE, family="Arial"),
    height=420,
    width=1300,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        orientation="h",
        yanchor="top",
        y=-0.35,
        xanchor="center",
        x=0.5,
        tracegroupgap=2,
    ),
    yaxis=dict(
        mirror=False, ticks="outside", tickfont_size=TICKFONT,
        showline=True, linecolor="black",
        range=[0, 1.2], tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1, 1.2],
    ),
    yaxis2=dict(
        mirror=False, ticks="outside", tickfont_size=TICKFONT,
        showline=True, linecolor="black",
        range=[-0.01, 0.4],
    ),
    yaxis3=dict(
        mirror=False, ticks="outside", tickfont_size=TICKFONT,
        showline=True, linecolor="black",
        range=[0, 1],
    ),
    yaxis4=dict(
        mirror=False, ticks="outside", tickfont_size=TICKFONT,
        showline=True, linecolor="black",
        range=[-0.01, 0.3],
    ),
    xaxis=dict(
        mirror=False, ticks="outside", dtick=25,
        showline=True, linecolor="black",
        title=dict(text="Representative Days", font=dict(size=FONTSIZE)),
        tickfont_size=FONTSIZE,
        range=[0, 100],
    ),
    xaxis2=dict(
        mirror=False, ticks="outside", dtick=25, tickfont_size=TICKFONT,
        showline=True, linecolor="black",
        title=dict(text="Representative Days", font=dict(size=FONTSIZE)),
        range=[0, 100],
    ),
    xaxis3=dict(
        mirror=False, ticks="outside", tickfont_size=TICKFONT,
        showline=True, linecolor="black",
        title=dict(text="Duration (h)", font=dict(size=FONTSIZE)),
        range=[0, 8760],
    ),
    xaxis4=dict(
        mirror=False, ticks="outside", dtick=25, tickfont_size=TICKFONT,
        showline=True, linecolor="black",
        title=dict(text="Representative Days", font=dict(size=FONTSIZE)),
        range=[0, 100],
    ),
)

fig.update_yaxes(title_standoff=5)
fig.update_annotations(font_size=FONTSIZE + 1)

for annotation in fig["layout"]["annotations"]:
    annotation["y"] += 0.08

# ---------------------------------------------------------------------------
# 4. Show and save
# ---------------------------------------------------------------------------

fig.show()
fig.write_image(OUTPUT_FILE)
print(f"Saved to {OUTPUT_FILE}")
