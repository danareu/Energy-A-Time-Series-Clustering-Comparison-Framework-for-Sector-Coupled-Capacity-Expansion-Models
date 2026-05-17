"""
plot_ens_co2_tsc.py
-------------------
Generates a 3-panel line plot:
  a) Lost Load (% of total demand)
  b) Excess CO2 Emissions (% relative to capacity-run)
  c) Estimated TSC (M€, dispatch-scaled)

Usage
-----
    python plot_ens_co2_tsc.py

Adjust the CONFIG section below to match your paths and scenario keys.
"""

import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import functions

pd.options.mode.chained_assignment = None

# ---------------------------------------------------------------------------
# CONFIG – edit these to match your setup
# ---------------------------------------------------------------------------

PATH = "../results/Basecase/"

KEYS = [
    "00_Kmeans_Centroid",
    "01_Centroid",
    "02_Medoid",
    "04_PCA",
]

REGIONS = ["DE", "UK", "BE", "NL", "DK", "NO", "SE", "FR"]

RENAMING = {
    KEYS[0]: "kmeans-c",
    KEYS[1]: "HC-c",
    KEYS[2]: "HC-m",
    KEYS[3]: "DTW-VD",
}

COLOR_PALETTE = {
    KEYS[0]: "#008080",
    KEYS[1]: "grey",
    KEYS[2]: "#D6695B",
    KEYS[3]: "#22579c",
}

# Path to the Excel input file used to compute total demand
DEMAND_EXCEL = "/cluster/home/danare/git/oceangrid_case/Input/Eight_Nodes_Gradual_De_20250801.xlsx"
DEMAND_SHEET = "Par_SpecifiedAnnualDemand"
DEMAND_YEAR  = 2050

# Cluster sizes to exclude from all plots
EXCLUDE_CLUSTER_SIZES = [25]

OUTPUT_FILE = "ens.pdf"

# ---------------------------------------------------------------------------
# 1. Read data
# ---------------------------------------------------------------------------

print("Reading total demand …")
demand = pd.read_excel(DEMAND_EXCEL, sheet_name=DEMAND_SHEET)
tot_demand = (
    demand[(demand["Year"] == DEMAND_YEAR) & (demand["Region"].isin(REGIONS))]["Value"].sum()
    / 3.6
)

print("Reading lost load (ENS) …")
df_list_ens = [
    functions.read_capacities(
        path=PATH, key=k,
        w="ProductionByTechnologyAnnual[2050,Infeasibility",
        counting=False,
    )
    for k in KEYS
]
# Convert to % of total demand
for df in df_list_ens:
    df["Value"] = (df["Value"] / tot_demand) * 100

print("Reading CO2 emissions (dispatch) …")
df_list_co2_dispatch = [
    functions.read_co2_emission(path=PATH, key=k, dispatch=True)
    for k in KEYS
]

print("Reading CO2 emissions (capacity run) …")
df_list_co2_cap = [
    functions.read_co2_emission(path=PATH, key=k, dispatch=False)
    for k in KEYS
]

# Excess CO2: % deviation of dispatch emissions vs capacity-run emissions
df_list_co2_excess = []
for df_d, df_c in zip(df_list_co2_dispatch, df_list_co2_cap):
    merged = df_d.merge(df_c[["ClusterSize", "Value"]], on="ClusterSize", suffixes=("", "_cap"))
    merged["Value"] = ((merged["Value"] - merged["Value_cap"]) / merged["Value_cap"]) * 100
    merged.drop(columns="Value_cap", inplace=True)
    df_list_co2_excess.append(merged)

print("Reading dispatch costs …")
COST_KEYWORDS = [
    "DiscountedAnnualTotalTradeCosts[2050",
    "DiscountedAnnualCurtailmentCost[2050",
    "TotalDiscountedCost[2050",
]
costs_inv_dispatch = [
    functions.read_capacities(path=PATH, key=k, counting=False, w=COST_KEYWORDS, dispatch=True)
    for k in KEYS
]
costs_inv_cap = [
    functions.read_capacities(path=PATH, key=k, counting=False, w=COST_KEYWORDS, dispatch=False)
    for k in KEYS
]

print("Reading objective function values …")
df_list_obj = [
    functions.read_obj_function(path=PATH, key=k, dispatch=False)
    for k in KEYS
]

# TSC scaled: ratio of (cap obj / cap cost) × dispatch cost
costs_ratio = []
for df_obj, df_cap in zip(df_list_obj, costs_inv_cap):
    merged = df_obj.merge(df_cap[["ClusterSize", "Value"]], on="ClusterSize", suffixes=("", "_cap"))
    merged["Value"] = merged["Value"] / merged["Value_cap"]
    merged.drop(columns="Value_cap", inplace=True)
    costs_ratio.append(merged)

tsc_scaled = []
for df_ratio, df_disp in zip(costs_ratio, costs_inv_dispatch):
    merged = df_ratio.merge(df_disp[["ClusterSize", "Value"]], on="ClusterSize", suffixes=("", "_disp"))
    merged["Value"] = merged["Value"] * merged["Value_disp"]
    merged.drop(columns="Value_disp", inplace=True)
    tsc_scaled.append(merged)
# ---------------------------------------------------------------------------
# 2. Build figure
# ---------------------------------------------------------------------------

TICKFONT  = 14
FONTSIZE  = 16

fig = make_subplots(
    rows=1, cols=3,
    horizontal_spacing=0.09,
    subplot_titles=[
        "a) Lost Load (%)",
        "b) Excess CO<sub>2</sub> Emissions (%)",
        "c) Estimated TSC (M€)",
    ],
)

panel_data = [df_list_ens, df_list_co2_excess, tsc_scaled]

for col, df_list in enumerate(panel_data, start=1):
    for j, df in enumerate(df_list):
        df = df[~df["ClusterSize"].isin(EXCLUDE_CLUSTER_SIZES)]
        fig.add_trace(
            go.Scatter(
                x=df["ClusterSize"],
                y=df["Value"],
                name=RENAMING[KEYS[j]],
                mode="lines",
                marker=dict(color=COLOR_PALETTE[KEYS[j]], size=7, symbol="diamond"),
                legendgroup=KEYS[j],
                showlegend=(col == 1),  # show legend only once
            ),
            row=1, col=col,
        )

# ---------------------------------------------------------------------------
# 3. Layout
# ---------------------------------------------------------------------------

fig.update_layout(
    font=dict(size=FONTSIZE, family="Arial", color="black"),
    height=410,
    width=1000,
    plot_bgcolor="white",
    legend=dict(orientation="h", x=0.27, y=-0.3),
)

fig.update_xaxes(
    mirror=False,
    ticks="outside",
    showline=True,
    linecolor="black",
    gridcolor="white",
    range=[0, 40],
    tickfont_size=TICKFONT,
    title=dict(font=dict(size=FONTSIZE)),
)

fig.update_yaxes(
    mirror=False,
    ticks="outside",
    showline=True,
    linecolor="black",
    tickfont_size=TICKFONT,
    title=dict(font=dict(size=FONTSIZE)),
    title_standoff=0.09,
)

# Per-panel y-axis ranges
fig.update_yaxes(range=[0, 30],   col=1, row=1)
fig.update_yaxes(range=[0, 400],  col=2, row=1)

# Shared x-axis label centred across all panels
fig.add_annotation(
    x=0.49, y=-0.33,
    text="Representative Days",
    showarrow=False,
    xref="paper", yref="paper",
    font=dict(size=FONTSIZE),
)

# Nudge subplot titles up slightly
for annotation in fig["layout"]["annotations"]:
    annotation["y"] += 0.08

fig.update_annotations(font_size=FONTSIZE)
fig.layout.legend.tracegroupgap = 0

# ---------------------------------------------------------------------------
# 4. Show and save
# ---------------------------------------------------------------------------

fig.show()
fig.write_image(OUTPUT_FILE, height=450, width=1100)
print(f"Saved to {OUTPUT_FILE}")
