import Pkg
Pkg.activate(@__DIR__)
Pkg.add(url="https://github.com/GENeSYS-MOD/GENeSYS_MOD.jl", rev="energy_publication")

using GENeSYS_MOD
using JuMP
using Dates
using Ipopt
using CSV
using XLSX
using HiGHS
using Gurobi

# ── Paths & settings ──────────────────────────────────────────────────────────

const DATA_FILE        = "Eight_Nodes_Gradual_De_20250801"
const INPUT_DIR        = "../input/"
const RESULT_DIR       = "../results/Basecase/04_PCA"
const HOURLY_DATA_FILE = "Timeseries_renewable_ninja_2018"
const CLUSTER_VALUES   = [1]

# ── Accumulator arrays ────────────────────────────────────────────────────────

building_time  = []
solving_time   = []
objective_list = []
n_var          = []
n_constr       = []

# ── Main loop ─────────────────────────────────────────────────────────────────

for c in CLUSTER_VALUES
    Switch = GENeSYS_MOD.Switch(
        2018,                          # year
        Gurobi.Optimizer,              # solver
        Ipopt.Optimizer,               # DNLPsolver
        "minimal",                     # model_region
        "DE",                          # data_base_region
        DATA_FILE,                     # data_file
        HOURLY_DATA_FILE,              # hourly_data_file
        30,                            # threads
        "MinimalExample",              # emissionPathway
        "globalLimit",                 # emissionScenario
        0.05,                          # socialdiscountrate
        INPUT_DIR,                     # inputdir
        RESULT_DIR,                    # resultdir
        0,                             # switch_infeasibility_tech
        0,                             # switch_investLimit
        1,                             # switch_ccs
        0,                             # switch_ramping
        0,                             # switch_weighted_emissions
        0,                             # set_symmetric_transmission
        0,                             # switch_intertemporal
        0,                             # switch_base_year_bounds
        0,                             # switch_base_year_bounds_debugging
        0,                             # switch_peaking_capacity
        0,                             # set_peaking_slack
        0,                             # set_peaking_minrun_share
        0,                             # set_peaking_res_cf
        0,                             # set_peaking_min_thermal
        0,                             # set_peaking_startyear
        0,                             # switch_peaking_with_storages
        0,                             # switch_peaking_with_trade
        0,                             # switch_peaking_minrun
        0,                             # switch_employment_calculation
        0,                             # switch_endogenous_employment
        "None",                        # employment_data_file
        0,                             # switch_dispatch
        1,                             # elmod_nthhour
        1,                             # elmod_starthour
        0,                             # elmod_dunkelflaute
        1,                             # elmod_daystep
        1,                             # elmod_hourstep
        0,                             # switch_raw_results
        0,                             # switch_processed_results
        0,                             # write_reduced_timeserie
        0,                             # switch_LCOE_calc
        c,                             # clusters
        4,                             # warping_window
        true,                         # hoffmann
        0,                             # switch_reserve
        1,                             # switch_emission_penalty
        "true",                            # pca_path
    )

    println("Running clusters=$c, hoffmann=$(Switch.hoffmann)")

    starttime = Dates.now()

    model = JuMP.Model(add_bridges=false)
    Sets, Params, Emp_Sets = GENeSYS_MOD.genesysmod_dataload(Switch)
    println("Timeslice count: ", length(Sets.Timeslice))

    Maps     = GENeSYS_MOD.make_mapping(Sets, Params)
    Vars     = GENeSYS_MOD.genesysmod_dec(model, Sets, Params, Switch, Maps)
    Settings = GENeSYS_MOD.genesysmod_settings(Sets, Params, Switch.socialdiscountrate)

    GENeSYS_MOD.genesysmod_bounds(model, Sets, Params, Vars, Settings, Switch, Maps)
    GENeSYS_MOD.genesysmod_equ(model, Sets, Params, Vars, Emp_Sets, Settings, Switch, Maps)

    set_optimizer(model, Gurobi.Optimizer)
    set_optimizer_attribute(model, "Threads",        30)
    set_optimizer_attribute(model, "Method",         2)
    set_optimizer_attribute(model, "BarHomogeneous", 1)
    set_optimizer_attribute(model, "ResultFile",     "Solution_julia.sol")
    set_optimizer_attribute(model, "Presolve",       2)

    build_time = Dates.now() - starttime
    t_solve_start = Dates.now()
    optimize!(model)
    solve_time = Dates.now() - t_solve_start

    status = termination_status(model)

    if status in (MOI.INFEASIBLE, MOI.INFEASIBLE_OR_UNBOUNDED)
        println("Infeasible (status: $status). Computing IIS...")
        compute_conflict!(model)
        GENeSYS_MOD.print_iis(model)

    elseif status in (MOI.OPTIMAL, MOI.ALMOST_INFEASIBLE)
        VarPar    = GENeSYS_MOD.genesysmod_variable_parameter(model, Sets, Params)
        obj       = objective_value(model)
        n_v       = num_variables(model)
        n_c       = sum(num_constraints(model, F, S) for (F, S) in list_of_constraint_types(model))
        out_file  = joinpath(RESULT_DIR, "$(Switch.clusters)_$(Switch.warping_window)__8nodes_test_withcross_onenode.txt")

        open(out_file, "w") do f
            println(f, "Objective = $obj")

            for v in all_variables(model)
                val = value(v)
                val != 0 && println(f, "$(v) = $val")
            end

            for y in axes(VarPar.ProductionByTechnology, 1),
                l in axes(VarPar.ProductionByTechnology, 2),
                t in axes(VarPar.ProductionByTechnology, 3),
                fv in axes(VarPar.ProductionByTechnology, 4),
                r in axes(VarPar.ProductionByTechnology, 5)

                prod = VarPar.ProductionByTechnology[y, l, t, fv, r]
                use  = VarPar.UseByTechnology[y, l, t, fv, r]
                prod != 0 && println(f, "ProductionByTechnology[$y,$l,$t,$fv,$r] = $prod")
                use  != 0 && println(f, "UseByTechnology[$y,$l,$t,$fv,$r] = $use")
            end

            for s in axes(VarPar.TotalStorageCapacity, 1),
                y in axes(VarPar.TotalStorageCapacity, 2),
                r in axes(VarPar.TotalStorageCapacity, 3)

                println(f, "TotalStorageCapacity[$s,$y,$r] = $(VarPar.TotalStorageCapacity[s, y, r])")
            end

            for y in axes(Params.RateOfDemand, 1),
                l in axes(Params.RateOfDemand, 2),
                fv in axes(Params.RateOfDemand, 3),
                r in axes(Params.RateOfDemand, 4)

                demand = Params.Demand[y, l, fv, r] * Params.YearSplit[l, y]
                if demand != 0
                    println(f, "RateOfDemand[$y,$l,$fv,$r] = $demand")
                    println(f, "Demand[$y,$l,$fv,$r] = $(Params.Demand[y, l, fv, r])")
                end
            end

            for r in axes(Params.TotalAnnualMaxCapacity, 1),
                t in axes(Params.TotalAnnualMaxCapacity, 2),
                y in axes(Params.TotalAnnualMaxCapacity, 3)

                println(f, "TotalAnnualMaxCapacity[$r,$t,$y] = $(Params.TotalAnnualMaxCapacity[r, t, y])")
            end

            println(f, "TimeSeriesMapping: $(Params.Mapping)")
        end

        push!(building_time,  build_time)
        push!(solving_time,   solve_time)
        push!(objective_list, obj)
        push!(n_var,          n_v)
        push!(n_constr,       n_c)
        println("build=$build_time  solve=$solve_time  obj=$obj  vars=$n_v  constraints=$n_c")

    else
        println("Unexpected termination status: $status")
    end
end

# ── Write summary results ─────────────────────────────────────────────────────

open(joinpath(RESULT_DIR, "all_results.txt"), "a") do f
    for (b, s, o, v, c) in zip(building_time, solving_time, objective_list, n_var, n_constr)
        write(f, "$b; $s; $o; $v; $c\n")
    end
end