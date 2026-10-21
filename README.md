# Topology identification (D2.2 use case 1) — three methods on SimBench and Far West

EnerTEF TEF DSO node · D2.2 §2.6.7 · DSS Lab, NTUA

Which lines of a network are really connected, given an asset register that is partly wrong and one month of smart-meter or SCADA measurements. Three methods, on SimBench LV distribution networks and on the ACTIVSg2000 Far West transmission area:

| Method | Idea | Uses |
|---|---|---|
| **Variance-Distance Spanning Tree** (ours) | Voltages at the two ends of a connected cable move together; Kruskal on the variance distance gives a radial tree | cable list, voltage magnitude |
| **Random forest** (Dong Liu, TU Delft) | His classifier, per line, on voltage correlation and the documented state; settings of his public code | voltage magnitude, register |
| **Combination** | Builds on Liu's forest: five indications per line (variance distance, spanning tree, power-flow residual, correlation, register), radial constraint, physics refinement | + P, Q per customer, cable types and lengths |

## Results (share of lines in the right state)

| Use case · scenario | Documented | Variance-Distance Spanning Tree | Random forest (Liu) | Combination |
|---|---|---|---|---|
| SimBench LV | 69.8 / 79.8 / 90.2 | 92.6 / 94.8 / 97.6 | 76.2 / 80.2 / 86.9 | 93.6 / 95.1 / 97.6 |
| Far West (80% only) | 79.6 | 82.1 | 98.2 | 99.4 |

Documentation 70 / 80 / 90% correct. No line of the register is trusted. Details: [`RESULTS.md`](RESULTS.md), method: [`METHOD.md`](METHOD.md).

All results are on simulated data; there is no field validation.

## Layout

| Path | Content |
|---|---|
| `variance_distance_spanning_tree/topology/` | the Variance-Distance Spanning Tree package (network loading, error model, variance distance, Kruskal, metrics) |
| `combined_method/simbench/` | SimBench LV: power flow (`sb_sim.py`, personalized profiles `indiv_profiles.py`), features (`exp_lv_pipeline.py`, `exp_liu_features.py`), the three methods (`exp_final_lv.py`) |
| `combined_method/far_west/` | Far West: network (`build_net.py`, `parse_mpc.py`), time series (`extract_far_west.py`), configurations (`generate.py`, `gen_multi.py`, `configs.json`), AC model and features (`fw_ac.py`, `pipeline.py`, `detect.py`), the three methods (`exp_final_fw.py`) |
| `combined_method/results/` | per-case results behind the table |
| `combined_method/run_all.py`, `make_tables.py` | reproduce the runs, print the table |

## Setup and reproduce

```bash
pip install -r combined_method/requirements.txt
cd combined_method
python make_tables.py                                # the table from the shipped results (seconds)
python run_all.py --stage lv --workers 2             # SimBench LV, 70/80/90%
python run_all.py --stage far_west --workers 2       # Far West 80%, full mode (about a day on 2 cores)
python run_all.py --stage collect && python run_all.py --stage tables
```

SimBench networks and profiles come with the `simbench` package. **Far West data**: from the Texas A&M Electric Grid Test Case Repository (ACTIVSg2000), put `case_ACTIVSg2000.m` in `combined_method/far_west/data/` and cut the time series to the area with `python far_west/extract_far_west.py "<folder with the ACTIVSg2000 time series>"`. Steps whose output exists are skipped; all random choices are seeded.

Part of the full Service 7 repository (all four use cases, MV, phase identification, further realism checks): `enertef_dso_service_7`.
