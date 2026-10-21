# Results — use case 1 (topology)

| Use case · scenario | Documented | Variance-Distance Spanning Tree | Random forest (Liu) | Combination |
|---|---|---|---|---|
| SimBench LV | 69.8 / 79.8 / 90.2 | 92.6 / 94.8 / 97.6 | 76.2 / 80.2 / 86.9 | 93.6 / 95.1 / 97.6 |
| Far West (80% only) | 79.6 | 82.1 | 98.2 | 99.4 |

## Reading the table

- **SimBench LV**: 6 feeders, personalized customer profiles, one month at 15 min, |V| Class 0.5, no phase angle; 72 cases per level. Every cable of the register is in doubt.
- **Far West**: ACTIVSg2000 area 1 (91 buses, 108 branches), 93 configurations with 0–6 branches out, one month at 1 h. The network is meshed, so a spanning tree does not fit (82%). The forest is trained on other configurations of the same network (switching history) and reaches 98%; the combination adds about one point.
- **Random forest (Liu)**: on LV, without a switching history of the same network and without the radial constraint, it stays near or below the register.

## Minimum requirements

| Data | Source |
|---|---|
| Old topology, with errors; every physically existing cable listed | Asset register |
| Cable types and lengths | Asset register |
| \|V\| Class 0.5, no phase angle | Smart meters, SCADA |
| P, Q per customer (bus), 1% | Smart meters, SCADA |
| One month, 15 min (TSO: 1 h) | — |
| Training examples | Feeders with known state (LV, leave one feeder out), or the SCADA switching history (TSO) |

## Limits

- Simulated data only; synthetic customer profiles; no field validation.
- LV simulated as balanced; every customer metered, synchronised, without gaps.
- The refinement thresholds (gate 0.05–0.95, 1% residual drop) were chosen on the same simulations.
