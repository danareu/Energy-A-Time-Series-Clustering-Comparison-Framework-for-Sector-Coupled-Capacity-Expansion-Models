# Time Series Clustering Comparison Framework for Sector-Coupled Capacity Expansion Models

A research framework for systematically comparing time series aggregation (TSA) methods in energy system capacity expansion modelling. Four clustering approaches are benchmarked using the sector-coupled capacity expansion model built on [GENeSYS-MOD](https://github.com/GENeSYS-MOD/GENeSYS_MOD.jl).

## Repository Structure

```
├── input/           # GENeSYS-MOD input data (.xlsx)
│   ├── Eight_Nodes_Gradual_De_20250801.xlsx
│   ├── Tag_Subsets.xlsx
│   └── Timeseries_renewable_ninja_2010/2015/2018.xlsx
│
├── run_case/        # Julia scripts to run the model with each TSA method
│   ├── kmeans.jl        # K-Means clustering
│   ├── centroid.jl      # Centroid-based clustering
│   ├── medoid.jl        # K-Medoids clustering
│   ├── pca.jl           # PCA-based time series aggregation
│   ├── Project.toml
│   ├── Manifest.toml
│   └── gurobi.opt
│
├── results/         # NOT included — see Data Availability below
│
└── plots/           # Python scripts for generating the paper figures
```

## Clustering Methods

| Script | Method | Description |
|--------|--------|-------------|
| `kmeans.jl` | K-Means | Standard centroid-based clustering of representative days |
| `centroid.jl` | Centroid | Centroid representation of clustered time-series |
| `medoid.jl` | K-Medoids | Uses actual days from the time-series as representatives |
| `pca.jl` | PCA | Principal Component Analysis for dimensionality reduction before aggregation, DTW distance metric and hierarchical clustering with representative selection method according to https://www.sciencedirect.com/science/article/abs/pii/S0306261922004342 |

Each script runs the full GENeSYS-MOD capacity expansion model for a configurable range of cluster counts and writes results to the `results/` folder.
The required dependencies can be accessed in Project.toml.

## Data Availability

The `results/` folder is **not included** in this repository due to file size constraints. The full model results required to reproduce the paper figures are published on Zenodo: 10.5281/zenodo.20274562

> 📦 **[Zenodo dataset link]** ← replace with your DOI

To reproduce the figures, download the Zenodo archive and place the contents into the `results/` directory before running the plotting scripts in `plots/`.

## Requirements

### Julia packages
- `GENeSYS_MOD` — from [GENeSYS-MOD/GENeSYS_MOD.jl](https://github.com/GENeSYS-MOD/GENeSYS_MOD.jl), branch `energy_publication`
- `JuMP`, `Gurobi`, `HiGHS`, 
- `CSV`, `XLSX`, `DataFrames`, `Clustering`, `Distances`
- `MultivariateStats`, `DynamicAxisWarping`, `Statistics`

Install all dependencies by activating the project environment inside `run_case/`:

```julia
using Pkg
Pkg.activate(".")
Pkg.instantiate()
```

### Python (for plots)
- Python ≥ 3.9
- `pandas`, `numpy`, `matplotlib`

## Usage

### Running the model

Navigate to `run_case/` and run one of the method scripts:

```bash
julia pca.jl
julia kmeans.jl
julia centroid.jl
julia medoid.jl
```

Key settings at the top of each script:

```julia
const DATA_FILE        = "Eight_Nodes_Gradual_De_20250801"
const INPUT_DIR        = "../input/"
const RESULT_DIR       = "../results/Basecase/04_PCA"
const HOURLY_DATA_FILE = "Timeseries_renewable_ninja_2018"
const CLUSTER_VALUES   = [5, 10, 15, 20, 25, 30, 40]
```

Adjust `CLUSTER_VALUES` to control how many representative periods are tested. Results are written as `.txt` files to `RESULT_DIR`.

### Reproducing the figures

1. Download the results data from Zenodo and place it in `results/`
2. Run the Python scripts in `plots/`:

```bash
python plots/plot_rmse.py
python plots/plot_capacities.py
python plots/plot_objective_function.py
python plots/plot_ens_co2_tsc.py
```

## Input Data

Renewable energy time series (wind, solar) are sourced from [Renewable Ninja](https://www.renewables.ninja/) for years 2010, 2015, and 2018 across an 8-node European network. Model input data follows the GENeSYS-MOD format (`.xlsx`).

## Reference Model

The optimization model is based on [GENeSYS-MOD](https://github.com/GENeSYS-MOD/GENeSYS_MOD.jl), a sector-coupled open-source capacity expansion model. This framework uses the `energy_publication` branch.
