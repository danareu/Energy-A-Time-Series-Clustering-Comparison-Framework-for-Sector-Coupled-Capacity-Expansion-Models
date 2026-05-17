import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import glob
import os
import re


def read_obj_function(path, key, dispatch, year=2018):
    files = glob.glob(os.path.join(f"{path}{key}/", '*.txt'))
    list_cluster =  []
    list_values = []
    if dispatch:
        files = [f for f in files if any(keyword in f for keyword in ["dispatch"])]
    else:
        files = [f for f in files if not any(keyword in f for keyword in ["dispatch", "all"])]

    for i in files:
        with open(i, 'r') as file:
            val = float(file.readline().strip().split("=")[-1])
            #val = float(re.findall("\d+\.\d+", file.readline())[0])
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
    df["Year"] = year
    df.sort_values(by=["ClusterSize"], inplace=True)
    return df


def read_capacities(path, key, w, counting=False, dispatch=True, infeasibility=True, year=2018):
    list_values = []
    list_cluster = []
    
    files = glob.glob(os.path.join(f"{path}{key}/", '*.txt'))
    if dispatch:
        files =[f for f in files if "dispatch_" in f]
    else:
        files = [f for f in files if not any(keyword in f for keyword in ["dispatch", "all"])]
    for i in files:
        with open(i, 'r') as file:
            val = 0
            tmp_ts = []
            for line in file:
                if isinstance(w, list):
                    w = tuple(w)
                if line.startswith(w):
                    if counting:
                        if "Infeasibility" in line:
                            ts = float(line.split(",")[1])
                            if ts not in tmp_ts:
                                val += 1
                                tmp_ts.append(ts)
                    else:
                        if infeasibility:
                             if line.startswith("DiscountedSalvageValue"):
                                val -= float(line.split("= ")[-1])
                             else:
                                val += float(line.split("= ")[-1])
                        else:
                            if "Infeasibility" not in line:
                                val += float(line.split("= ")[-1])
        if dispatch:
            try:
                c = float(i.split("/")[-1].split("_")[1])
            except ValueError:
                c = float(i.split("/")[-1].split("_")[1].split(".")[0])
        else:
            c = float(i.split("/")[-1].split("_")[0])
        list_cluster.append(c)
        list_values.append(val)
                
                
    df = pd.DataFrame({"ClusterSize": list_cluster, "Value": list_values})
    df["Scenario"] = key
    df["Year"] = year
    df.sort_values(by=["ClusterSize"], inplace=True)
    
    return df

def read_txt_file(path, key):
    with open(path, "r") as f:
        lines = f.read().splitlines()
        data_list = []
        for i, l in enumerate(lines, start=-1):
            if l.startswith(key):
                m = l.split('[', 1)[1].split(']')[0].split(",")
                m.append(l.split(" ")[-1])
                data_list.append(m)
                if not lines[i + 1].startswith(key):
                    break
    return data_list

def read_co2_emission(path, key, dispatch=False, year=2018):
    files = glob.glob(os.path.join(f"{path}{key}/", '*.txt'))
    list_cluster =  []
    scenario_lst = []
    list_values = []

    if dispatch:
        files = [f for f in files if any(keyword in f for keyword in ["dispatch"])]
    else:
        files = [f for f in files if not any(keyword in f for keyword in ["dispatch", "all"])]
    for i in files:
        val = 0
        with open(i, 'r') as file:
            for line in file:
                if line.startswith("AnnualTechnologyEmission[2050"):
                    val += float(line.split("= ")[-1])
        if dispatch:
            try:
                c = float(i.split("/")[-1].split("_")[1])
            except ValueError:
                c = float(i.split("/")[-1].split("_")[1].split(".")[0])
        else:         
            c = float(i.split("/")[-1].split("_")[0])
        scen = i.split("/")[-2]
                
        list_cluster.append(c)
        list_values.append(val)
        scenario_lst.append(scen)
                
    df = pd.DataFrame({"ClusterSize": list_cluster, "Value": list_values, "Scenario": scenario_lst})      
    df.sort_values(by=["ClusterSize"], inplace=True)
    df["Scenario"] = key
    df["Year"] = year
    return df
    

def read_capacities_cl(path, key, param, dispatch=False):
    
    df = pd.DataFrame(columns=["ClusterSize", "Region", "Technology", "Value", "Scenario"])
    
    files_rw = glob.glob(os.path.join(f"{path}{key}/", '*.txt'))
    
    if dispatch:
        files = [i for i in files_rw if "dispatch_" in i]
    else:
        files = [i for i in files_rw if not any(keyword in i for keyword in ["dispatch", "all"]) and not i.endswith("txt.txt")]

    files.sort()

    for i in files:

        val = 0
        with open(i, 'r') as file:
            if dispatch:
                c = float(i.split("/")[-1].split("_")[1])
            else:
                try:
                    c = float(i.split("/")[-1].split("_")[0])
                except ValueError:
                    c = float(i.split("/")[-1].split(".")[0])
                
            # iterate through lines to get capacitites
            for line in file:
                if param == "TotalCapacityAnnual" or param == "CurtailedEnergyAnnual" or param == "TotalTechnologyAnnualActivity" or param == "ProductionByTechnologyAnnual" or param == "AnnualTechnologyEmissionByMode":
                    if line.startswith(f"{param}[2050"):
                        val = float(line.split("= ")[-1])
                        tech = line.split(",")[1]
                        region = line.split(",")[-1][0:2]
                        df.loc[len(df)] = [c, region, tech, val, key]
                elif param == "ProductionByTechnology":
                    if line.startswith(f"{param}[2050"):
                        val = float(line.split("= ")[-1])
                        tech = line.split(",")[2]
                        region = line.split(",")[-1][0:2]
                        df.loc[len(df)] += [c, region, tech, val, key]
                else:
                    if line.startswith(f"{param}"):
                        if int(line.split("]")[0].split(",")[-1]) == 2050:
                            val = float(line.split("= ")[-1])
                            tech = line.split(",")[1]
                            region = line.split("[")[-1][0:2]
                            df.loc[len(df)] = [c, region, tech, val, key]
                
    if key == "03_Old":
        df["ClusterSize"] = df["ClusterSize"]/24
    df.sort_values(by=["ClusterSize"], inplace=True, ignore_index=True)
    
    if param == "TotalCapacityAnnual" and dispatch==False:
        df = df.groupby(by=["ClusterSize", "Technology", "Scenario"], as_index=False).sum()

    return df


def read_trade_capacities(path, key):
    
    files_rw = glob.glob(os.path.join(f"{path}{key}/", '*.txt'))
    df = pd.DataFrame(columns=["ClusterSize", "Fuel", "Value", "Scenario", "Region1", "Region2"])
    files = [i for i in files_rw if not any(keyword in i for keyword in ["dispatch", "all"]) and not i.endswith("txt.txt")]
    files.sort()
    
    for i in files:
        with open(i, 'r') as file:
            try:
                c = float(i.split("/")[-1].split("_")[0])
            except ValueError:
                c = float(i.split("/")[-1].split(".")[0])
            for line in file:
                 if line.startswith(f"TotalTradeCapacity[2050"):
                    val = float(line.split("= ")[-1])
                    fuel = line.split(",")[1]
                    r1 = line.split(",")[2]
                    r2 = line.split("]")[0].split(",")[-1] 
                    df.loc[len(df)] = [c, fuel, val, key, r1, r2]
    return df

aggregation = {
    'P_Nuclear': 'Nuclear',
    'P_Coal_Hardcoal': 'Fossil Oil and Coal',
    'P_Coal_Lignite': 'Fossil Oil and Coal',
    "HLR_Gas_Boiler": "Gas Boiler",
    "HLI_Gas_Boiler": "Gas Boiler",
    "HMI_Gas": "Gas Boiler",
    'HHI_BF_BOF_CCS': "Electric Heat",
    "HMI_Gas_CCS": "Gas Boiler",  
     'HHI_Scrap_EAF': "Electric Heat",
    "HMI_Steam_Electric": "Electric Heat",
     'HHI_Molten_Electrolysis': "Electric Heat",
    'P_Oil': 'Fossil Oil and Coal',
    "HLI_Direct_Electric": "Electric Heat",
    "HLR_Direct_Electric":"Electric Heat",
    'P_Gas_OCGT': 'Natural Gas',
    "HLI_H2_Boiler": "H<sub>2</sub> (electrolysis, fuel cells, <br> storage, and network)",
    "X_Gasifier": "Gasifier",
    "CHP_Gas_CCGT_Natural": "Fossil Oil and Coal",
    'P_Gas_CCGT': 'Natural Gas',
    "HMI_HardCoal_CCS": "Fossil Oil and Coal",
    "X_Electrolysis": "H<sub>2</sub> (electrolysis, fuel cells, <br> storage, and network)",
    'P_Gas_CCS': 'Natural Gas',
    "H2": "H<sub>2</sub> (electrolysis, fuel cells, <br> storage, and network)",
    "X_Methanation": "Methanation",
    "CHP_Biomass_Solid": "Biomass",
    "P_H2_OCGT": "H<sub>2</sub> (electrolysis, fuel cells, <br> storage, and network)",
    'P_Gas_Engines': 'Fossil Oil and Coal',
    'RES_Hydro_Large': 'Hydroelectricity',
    'RES_Hydro_Small': 'Hydroelectricity',
    'RES_Wind_Offshore_Deep': 'Wind Offshore',
    'CHP_Coal_Hardcoal_CCS': 'Fossil Oil and Coal',
    'CHP_Coal_Lignite_CCS': 'Fossil Oil and Coal',
    'CHP_Gas_CCGT_Biogas_CCS': 'Biomass',
    'CHP_Gas_CCGT_Natural_CCS': 'Natural Gas',
    'P_Biomass_CCS': 'Biomass',
    'P_Coal_Hardcoal_CCS': 'Fossil Oil and Coal',
    'P_Coal_Lignite_CCS': 'Fossil Oil and Coal',
    'P_Gas_CCS': 'Fossil Oil and Coal',
    "X_DAC_LT": "DAC & CCS",
    'X_ATR_CCS': "H<sub>2</sub> (electrolysis, fuel cells, <br> storage, and network)", 
    'CHP_Biomass_Solid_CCS': 'Biomass',
    'RES_Wind_Offshore_Transitional': 'Wind Offshore',
    'RES_Wind_Offshore_Shallow': 'Wind Offshore',
    'RES_Wind_Onshore_Opt': 'Wind Onshore',
    'RES_Wind_Onshore_Avg': 'Wind Onshore',
    'RES_Wind_Onshore_Inf': 'Wind Onshore',
    'RES_PV_Utility_Opt': 'PV',
    'RES_PV_Utility_Avg': 'PV',
    "HLR_Heatpump_Aerial": "Heat Pump",
    "HMI_Biomass": "Biomass Boiler",
    'RES_PV_Rooftop_Residential': 'PV',
    'Res_PV_Utility_Tracking': 'PV',
    'RES_PV_Utility_Inf': 'PV',
    'RES_PV_Rooftop_Commercial': 'PV',
    "HLI_Geothermal": "Geothermal",
    "Gas_Natural": "Natural Gas",
    'P_Biomass': 'Biomass',
    "D_Gas_H2": "H<sub>2</sub> (electrolysis, fuel cells, <br> storage, and network)",
    'P_Biomass_CCS': 'Biomass',
    'D_PHS': "Hydroelectricity",
    'D_Battery_Li-Ion': 'Battery Li-Ion',
    'D_PHS_Residual': "Hydroelectricity",
    "CHP_Oil": "Fossil Oil and Coal",
    "HLR_Lignite": "Fossil Oil and Coal",
    "R_Nuclear": "Nuclear",
    "Biofuel": "Biomass",
    "Gas_Synth": "Methane",
}

colour_codes = {
    'Nuclear': '#FA6300',
    "Fossil Oil and Coal": "#B9B9B9",
    "Heat Pump": "#2EB335",
    "Gas Boiler": "#D96823",
    "Electric Heat": "#D7F8B8",
    "Biomass Boiler": "#A67A59",
    "Hydroelectricity": "#288A7F",
    "Wind": "#215CBA",
    "H<sub>2</sub> (electrolysis, fuel cells, <br> storage, and network)": "magenta",
    "H<sub>2</sub> Storage": "rgb(191,19,160)",
    "El. Transmission Grid": "#6B9457", 
    "Biomass Boiler": "#A67A59",
    "H<sub>2</sub> network": "pink",
    "Lignite": "grey",
    "X_Biofuel": "blue",
    "DAC & CCS": "#F09CAE",
    'Hardcoal': 'rgb(229,229,229)',
    'Natural Gas': 'rgb(224,91,9)',
    'Pumped Hydro': '#51dbcc',
    "H<sub>2</sub> OCGT": "pink",
    'Oil': 'black',
    'Biomass': 'rgb(186,167,65)',
    'Hydro Reservoir': 'rgb(7,154,136)',
    'Hydro Run-of-River': 'rgb(8,173,151)',
    'PV': 'rgb(249,208,2, 1)',
    'Wind Onshore': 'rgb(35,94,188)',
    'Wind Offshore': 'rgb(104,149,221)',
    'Hydrogen': 'rgb(191,0,191)',
     "Methanation":"#C24AE6",
    'Electrolysis': 'magenta',
    'Battery Li-Ion': "rgb(172,227,127)",
    'solar_rooftop': 'rgb(255,239,96)',
    'solar_tracking': 'rgb(255,246,191)',
    'Transport': 'rgb(37,160,139)',
    'Industry': 'rgb(234,197,99)',
    'Buildings': 'rgb(240,243,190)',
    "Gasifier":"orange",
    "X_SMR": "grey",
    "LNG": "#E597FF",
    'Demand': 'rgb(223,222,220)',  # rgb(166,193,214),
    'DK': 'rgb(42,157,142)',
    'UK': 'rgb(230,111,81)',
    'Power': 'rgb(38,70,83)',
    'NO1': 'rgb(37,160,139)',
    'NO3': 'rgb(234,197,99)',
    "Methane": "#C04FE0",
    'NO4': 'rgb(240,243,190)',
    "X_ATR_CCS": "grey",
    'NO5': 'rgb(199,197,193)',
    "Geothermal": "brown",
    'NO2': 'rgb(230,111,81)',
    "Infeasibility_Power": "grey",

}

def make_layout(fig):
    fig.update_layout(
    font=dict(
        size=14,
        color="black" ),
    legend=dict(
        orientation="h"),
    plot_bgcolor='white',
    paper_bgcolor='white',)

    fig.update_xaxes(
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='white'
    )

    fig.update_yaxes(
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
    )

def read_demand(path, key, year=2018):
    list_values = []
    list_cluster = []
    timesteps = []
    region = []
    fuels = []
    years = []
    
    files = glob.glob(os.path.join(f"{path}{key}/", '*.txt'))
    files = [f for f in files if not any(keyword in f for keyword in ["dispatch", "all"])]
    
    for i in files:
        with open(i, 'r') as file:
            val = 0
            c = float(i.split("/")[-1].split("_")[0])
            for line in file:
                if line.startswith("Demand["):
                    val = float(line.split("= ")[-1])
                    r = line.split("]")[0].split(",")[-1]
                    f = line.split(",")[2]
                    d = line.split(",")[1]
                    y = line.split("[")[-1].split(",")[0]
                    
                    list_cluster.append(c)
                    list_values.append(val)
                    timesteps.append(d)
                    fuels.append(f)
                    region.append(r)
                    years.append(y)
                
                
    df = pd.DataFrame({"ClusterSize": list_cluster, "Value": list_values, "Fuel": fuels, "Region": region, "TimeStep": timesteps})
    df["Scenario"] = key
    df["Year"] = year
    df.sort_values(by=["ClusterSize"], inplace=True)
    df = df.groupby(by=["ClusterSize", "Year", "Scenario"], as_index=False).sum()
    df.drop(["Fuel", "Region", "TimeStep"], axis=1, inplace=True)
    return df


    