"""
plot_capacities.py
------------------
Generates a stacked-bar capacity plot (Installed Capacities vs. Representative Days)
with an optional overlaid TSC scatter on a secondary y-axis.

Usage
-----
    python plot_capacities.py

Adjust the CONFIG section below to match your paths and scenario keys.
"""

import pandas as pd
import plotly.graph_objects as go
import functions  # functions.py must be on the Python path

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

VRES = [
    "RES_Wind_Offshore_Deep",
    "RES_Hydro_Small",
    "RES_PV_Utility_Avg",
    "RES_Wind_Onshore_Avg",
]

# Technologies to drop from the capacity data before plotting
EXCLUDE_TECHS = [
    "HLR_Convert_DH", "HLI_Convert_DH", "X_Biofuel",
    "RES_Wood", "RES_Grass", "X_Gasifier",
]

SORTED_TECHS = [
    "Hydroelectricity", "Biomass", "Natural Gas", "Wind",
    "Wind Onshore", "Wind Offshore", "PV", "Battery Li-Ion",
    "Heat Pump", "Electric Heat", "Biomass Boiler", "Geothermal",
    "Gas Boiler", "Methanation", "Nuclear", "Fossil Oil and Coal",
    "H<sub>2</sub> (electrolysis, fuel cells, <br> storage, and network)",
    "DAC & CCS",
]

RENAMING = {
    KEYS[1]: "HC-c",
    KEYS[2]: "HC-m",
    KEYS[3]: "DTW-VD",
    KEYS[0]: "kmeans-c",
}

# Set to True to overlay TSC (Total System Cost) markers on a secondary y-axis
ADD_TSC = True

# y-axis range for TSC secondary axis (adjust to your data)
TSC_YAXIS_RANGE = [5_430_000, 5_560_000]

# Separator line x-positions between scenario groups (adjust to your data)
SEPARATOR_X_POSITIONS = [6.5, 13.5, 19.5]

OUTPUT_FILE = "capacities.pdf"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def aggregate_and_add_ccs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Duplicate rows whose Technology ends with 'CCS', label them 'DAC & CCS',
    then apply the standard aggregation mapping from functions.py.
    """
    ccs_rows = df[df["Technology"].str.endswith("CCS")].copy()
    ccs_rows["Technology"] = "DAC & CCS"
    df_extended = pd.concat([df, ccs_rows], ignore_index=True)
    df_extended.replace(functions.aggregation, inplace=True)
    return df_extended


def filter_exclude_techs(df: pd.DataFrame, exclude: list) -> pd.DataFrame:
    """Drop rows whose Technology prefix or name appears in the exclude list."""
    mask = df["Technology"].apply(
        lambda t: (
            t.startswith("PSNG") or
            t.startswith("Z_") or
            t.startswith("FRT") or
            t.startswith("RES_Residues") or
            t in exclude
        )
    )
    return df[~mask]


# ---------------------------------------------------------------------------
# 1. Read data
# ---------------------------------------------------------------------------

print("Reading capacity data …")
df_list_capa = [
    functions.read_capacities_cl(path=PATH, key=k, param="TotalCapacityAnnual", dispatch=False)
    for k in KEYS
]
for df in df_list_capa:
    df.replace(RENAMING, inplace=True)

print("Reading trade capacities …")
df_list_trade_raw = [
    functions.read_trade_capacities(path=PATH, key=k)
    for k in KEYS
]

df_trade = []
for df in df_list_trade_raw:
    df = df.groupby(by=["ClusterSize", "Fuel", "Scenario"], as_index=False).sum()
    df.drop(["Region1", "Region2"], axis=1, inplace=True)
    df.replace(RENAMING, inplace=True)
    df_trade.append(df)

if ADD_TSC:
    print("Reading objective function (TSC) …")
    df_list_obj = [
        functions.read_obj_function(path=PATH, key=k, dispatch=False)
        for k in KEYS
    ]

# ---------------------------------------------------------------------------
# 2. Build figure
# ---------------------------------------------------------------------------

fig = go.Figure()
fig.layout.annotations = []

# --- Trade capacity (El. Transmission Grid) bars ---
for j, df in enumerate(df_trade):
    df_tmp = df[(df["Fuel"] == "Power") & (~df["ClusterSize"].isin([25]))]
    fig.add_trace(go.Bar(
        x=[df_tmp["Scenario"], df_tmp["ClusterSize"]],
        y=df_tmp["Value"],
        name="El. Transmission Grid",
        marker=dict(color=functions.colour_codes["El. Transmission Grid"]),
        showlegend=(j == 1),
        legendgroup="El. Transmission Grid",
        yaxis="y",
    ))

# --- Installed capacity stacked bars ---
number_bars = 0
for j, df in enumerate(df_list_capa):
    df = df[~df["ClusterSize"].isin([25])]
    df = filter_exclude_techs(df, EXCLUDE_TECHS)
    df = aggregate_and_add_ccs(df)
    df = df.groupby(["Technology", "Scenario", "ClusterSize"], as_index=False).sum()
    df.sort_values(by="ClusterSize", inplace=True)
    number_bars += len(df["ClusterSize"].unique())

    for t in [g for g in SORTED_TECHS if g in df["Technology"].unique()]:
        df_tmp = df[df["Technology"] == t]
        fig.add_trace(go.Bar(
            x=[df_tmp["Scenario"], df_tmp["ClusterSize"]],
            y=df_tmp["Value"],
            name=t,
            marker=dict(color=functions.colour_codes.get(t, "grey")),
            showlegend=(j == 1),
            legendgroup=t,
            yaxis="y",
        ))

# --- Optional TSC scatter on secondary y-axis ---
if ADD_TSC:
    for i, df in enumerate(df_list_obj):
        df = df[(df["Value"] > 0) & (~df["ClusterSize"].isin([25]))]
        df = df.copy()
        df["Scenario"] = RENAMING[KEYS[i]]
        fig.add_trace(go.Scatter(
            x=[df["Scenario"], df["ClusterSize"]],
            y=df["Value"],
            mode="markers",
            marker=dict(color="saddlebrown", size=9, symbol="hexagram"),
            yaxis="y2",
            showlegend=False,
        ))

# --- Vertical separators between scenario groups ---
for xpos in SEPARATOR_X_POSITIONS:
    fig.add_shape(
        type="line",
        xref="x", yref="paper",
        x0=xpos, x1=xpos,
        y0=0, y1=1,
        line=dict(color="dimgray", width=0.7, dash="dash"),
    )

# ---------------------------------------------------------------------------
# 3. Layout
# ---------------------------------------------------------------------------

layout_kwargs = dict(
    barmode="stack",
    xaxis=dict(
        mirror=False,
        ticks="outside",
        showline=True,
        range=[-0.75, number_bars - 0.25],
        linecolor="black",
        gridcolor="white",
        title=dict(text="Representative Days", font=dict(size=14)),
        title_standoff=20,
        tickangle=0,
    ),
    yaxis=dict(
        title=dict(text="Installed Capacities (GW)", font=dict(size=14)),
        mirror=False,
        ticks="outside",
        showline=True,
        linecolor="black",
    ),
    font=dict(size=14, family="Arial", color="black"),
    width=890,
    height=680,
    plot_bgcolor="white",
    legend=dict(
        orientation="h",
        y=-0.3,
        xanchor="center",
        x=0.5,
        borderwidth=0,
        bordercolor="white",
        traceorder="normal",
        itemsizing="constant",
        font=dict(size=14),
    ),
)

if ADD_TSC:
    layout_kwargs["yaxis2"] = dict(
        range=TSC_YAXIS_RANGE,
        title=dict(text="TSC (M€)", font=dict(color="saddlebrown", size=14)),
        tickfont=dict(color="saddlebrown"),
        tickcolor="saddlebrown",
        mirror=False,
        ticks="outside",
        showline=True,
        linecolor="saddlebrown",
        overlaying="y",
        side="right",
    )

fig.update_layout(**layout_kwargs)

for annotation in fig["layout"]["annotations"]:
    annotation["y"] += 0.03

fig.layout.legend.tracegroupgap = 0
fig.update_annotations(font_size=16)
fig.update_traces(marker=dict(line=dict(width=0)))

# ---------------------------------------------------------------------------
# 4. Show and save
# ---------------------------------------------------------------------------

fig.show()
fig.write_image(OUTPUT_FILE, width=890, height=680)
print(f"Saved to {OUTPUT_FILE}")
