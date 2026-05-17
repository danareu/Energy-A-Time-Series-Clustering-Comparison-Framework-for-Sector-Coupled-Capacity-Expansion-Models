"""
plot_objective_function.py
--------------------------
Self-contained script – no functions.py needed.

Generates a 2-panel line plot of relative TSC deviation (Δ TSC %) vs.
Representative Days:
  a) DTW-VD vs. Traditional Clustering
  b) DTW-VD Components

A horizontal dashed reference line at 0 % i

s drawn if a full-hourly
benchmark file is found at:
    {PATH}full_hourly_solution_pca.txt

Usage
-----
    python plot_objective_function.py

Adjust the CONFIG section to match your paths and scenario keys.
"""

import glob
import os
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

pd.options.mode.chained_assignment = None

# ---------------------------------------------------------------------------
# CONFIG – edit these to match your setup
# ---------------------------------------------------------------------------

PATH = "../results/Sensitivity_One_Node/"

# Keys are ordered intentionally: first 4 go to panel a), last 3 to panel b)
KEYS = [
    "04_PCA",
    "02_Medoid",
    "01_Centroid",
    "00_Kmeans_Centroid",
    "07_Only_VD",
    "05_Only_PCA",
    "06_Only_DTW",
]

RENAMING = {
    "04_PCA":             "DTW-VD",
    "02_Medoid":          "HC-m",
    "01_Centroid":        "HC-c",
    "00_Kmeans_Centroid": "kmeans-c",
    "07_Only_VD":         "VD",
    "05_Only_PCA":        "PCA",
    "06_Only_DTW":        "DTW",
}

COLOR_PALETTE = {
    "04_PCA":             "#22579c",
    "02_Medoid":          "#D6695B",
    "01_Centroid":        "grey",
    "00_Kmeans_Centroid": "#008080",
    "07_Only_VD":         "#c64e50",
    "05_Only_PCA":        "#c59ba0",
    "06_Only_DTW":        "#6B4F6B",
}

# Filename of the full-hourly benchmark (relative to PATH).
# If missing, the 0 % reference line is not drawn.
BENCHMARK_FILE = "full_hourly_solution_pca.txt"

OUTPUT_FILE = "model_components.pdf"

# ---------------------------------------------------------------------------
# I/O function
# ---------------------------------------------------------------------------

def read_obj_function(path, key, dispatch):
    files = glob.glob(os.path.join(f"{path}{key}/", "*.txt"))
    if dispatch:
        files = [f for f in files if "dispatch" in f]
    else:
        files = [f for f in files if not any(kw in f for kw in ["dispatch", "all"])]
    list_cluster, list_values = [], []
    for i in files:
        with open(i) as fh:
            val = float(fh.readline().strip().split("=")[-1])
        if dispatch:
            c = float(i.split("/")[-1].split("_")[1])
        else:
            try:
                c = float(i.split("/")[-1].split("_")[0])
            except ValueError:
                c = float(i.split("/")[-1].split(".")[0])
        list_cluster.append(c)
        list_values.append(val)
    df = pd.DataFrame({"ClusterSize": list_cluster, "Value": list_values})
    df["Scenario"] = key
    df.sort_values("ClusterSize", inplace=True)
    return df

# ---------------------------------------------------------------------------
# 1. Read data
# ---------------------------------------------------------------------------

print("Reading objective function values …")
df_list_obj = [
    read_obj_function(path=PATH, key=k, dispatch=False)
    for k in KEYS
]

# Try to load the full-hourly benchmark for the 0 % reference line
benchmark_path = os.path.join(PATH, BENCHMARK_FILE)
try:
    with open(benchmark_path) as fh:
        obj_value = float(fh.readline().split("=")[-1])
    show_line = True
    print(f"Benchmark loaded: {obj_value:.2f}")
except FileNotFoundError:
    print("No full-hourly benchmark found – reference line will not be drawn.")
    obj_value = None
    show_line = False

# Normalise to % deviation from benchmark
if obj_value is not None:
    for i, df in enumerate(df_list_obj):
        try:
            df["Value"] = ((df["Value"] - obj_value) / obj_value) * 100
        except (IndexError, ZeroDivisionError):
            pass
        df_list_obj[i] = df

# ---------------------------------------------------------------------------
# 2. Build figure
# ---------------------------------------------------------------------------

fig = make_subplots(
    cols=2, rows=1,
    subplot_titles=["a) DTW-VD vs. Traditional Clustering", "b) DTW-VD Components"],
    y_title="Δ TSC (%)",
    x_title="Representative Days",
)

for j, df in enumerate(df_list_obj):
    # First 4 scenarios → panel 1; remaining → panel 2
    col = 2 if j >= 4 else 1
    k   = KEYS[j]

    # Actual data line (hidden from legend)
    fig.add_trace(go.Scatter(
        x=df["ClusterSize"],
        y=df["Value"],
        name=RENAMING[k],
        mode="lines",
        marker=dict(color=COLOR_PALETTE[k], size=8, symbol="diamond"),
        line=dict(dash="solid"),
        legendgroup=k,
        showlegend=False,
    ), row=1, col=col)

    # Invisible proxy trace for the legend entry (square marker)
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        name=RENAMING[k],
        mode="markers",
        marker=dict(color=COLOR_PALETTE[k], size=8, symbol="square"),
        legendgroup=k,
        showlegend=True,
    ), row=1, col=col)

# 0 % reference line in both panels
if show_line:
    x_ref = list(range(-5, 250))
    for col in [1, 2]:
        fig.add_trace(go.Scatter(
            x=x_ref,
            y=[0] * len(x_ref),
            mode="lines",
            line=dict(color="grey", width=1, dash="dash"),
            showlegend=False,
        ), row=1, col=col)

# ---------------------------------------------------------------------------
# 3. Layout
# ---------------------------------------------------------------------------

fig.update_layout(
    font=dict(size=16, family="Arial", color="black"),
    height=500,
    width=860,
    plot_bgcolor="white",
    legend=dict(
        orientation="h",
        borderwidth=0,
        bordercolor="rgba(0,0,0,0)",
        tracegroupgap=0,
        itemwidth=30,
        x=0.35,
        y=-0.25,
    ),
)

fig.update_xaxes(
    mirror=False, ticks="outside", showline=True,
    linecolor="black", gridcolor="white",
    range=[0, 100],
    tickvals=[0, 25, 50, 75, 100],
    title=dict(font=dict(size=16)),
)

fig.update_yaxes(
    mirror=False, ticks="outside", showline=True,
    linecolor="black",
    range=[-1.3, 0.1],
    title=dict(font=dict(size=16)),
    title_standoff=15,
)

# Nudge shared axis titles and subplot titles
fig.layout.annotations[0].y += 0.06   # subplot title a)
fig.layout.annotations[1].y += 0.06   # subplot title b)
fig.layout.annotations[2].y -= 0.07   # shared y-title
fig.layout.annotations[3].x -= 0.02   # shared x-title

fig.update_annotations(font_size=16)

# ---------------------------------------------------------------------------
# 4. Show and save
# ---------------------------------------------------------------------------

fig.show()
fig.write_image(OUTPUT_FILE)
print(f"Saved to {OUTPUT_FILE}")
