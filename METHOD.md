# Method — use case 1 (topology)

The combination: the same four steps on SimBench LV and on Far West:

1. physics features → 2. random forest → 3. decision under physical constraints → 4. physics refinement.

Origin of each part: Variance-Distance Spanning Tree, the power-flow residual, the constraints and the refinement are ours; the random forest classifier and the voltage-correlation features come from Liu et al., *A data-driven approach for topology correction in low voltage networks with DERs* (arXiv 2506.20238). The combination builds on his forest; its settings and his clustering settings follow his public code (github.com/distributionnetworksTUDelft/Data-driven-approach-for-topology-correction-in-LVDNs-).

## Notation and inputs

- Network: buses *i*, elements *e* (lines, cables, transformers, switches) with impedance *z_e = r_e + j x_e* from the asset register.
- Documentation: state *d_e* ∈ {0, 1} per element 70, 80 or 90% correct (Far West: 80%). Truth *s_e*.
- Candidates: elements whose state may be wrong. LV: every cable of the register (no line is trusted); Far West: every branch. Nothing about where the errors are is given.
- Measurements per time step *t*: |V_i(t)| with σ = 0.0025 p.u. (Class 0.5), P_i(t), Q_i(t) with 1% error, P and Q at the boundary (feeder heads or tie lines) with 1% error. No phase angle.

## Step 1 — features

**F1 Variance distance** (Variance-Distance Spanning Tree). With Ṽ the moving average of |V| over about four hours (15 samples at 15 min, 4 at 1 h):

    D_ij = Var_t( Ṽ_i(t) − Ṽ_j(t) )

Neighbouring buses move together, so D is small across a real line. Features: log10(D_e / median D of the candidates) and the rank of D_e among the candidates.

**F2 Variance-Distance Spanning Tree result.** Kruskal on D: candidates in increasing D while no cycle is formed. Feature: 1 if the element is kept. (On the meshed Far West network every element is a candidate, so this is a spanning tree on D.)

**F3 Power-flow residual on the fluctuations** (ours). For a topology hypothesis *s*, predict the voltages from the measured injections and compare:

- Radial LV networks — linearised network equations with the substation bus as reference: Z_s = (Y_s reduced)⁻¹ and ΔV ≈ Re( Z_s · conj(S / |V|) ).
- Meshed Far West — full AC Newton–Raphson for all hours at once, measured injections at every bus, tie-line flows as injections at the boundary buses, one reference bus (measured |V|, angle 0) per electrical island. Single-element changes are evaluated by Newton steps with the reference Jacobian updated by the element's own low-rank contribution (Woodbury); elements documented out of service are evaluated by an exact warm-started solve. Hours in which the reference solution does not converge are excluded. If the documented topology has no power-flow solution in at least half of the hours, the reference topology is "all elements in service".

Residual r_i(t) = |V_i(t)| measured − predicted, with two means removed: the mean over buses at each time (unknown source voltage) and the time mean of each meter (constant model errors such as cable charging, transformer taps, meter bias). Then

    J(s) = Σ_t Σ_i ( r_i(t) / σ )²,      σ = max(meter σ, rms residual of the starting state)

Feature: dJ_e = ( J(d) − J(d with e changed) ) / J(d). Positive means the change explains the measurements better. On Far West two extra features: the reference state of the element.

**F4 Voltage correlation** (Liu): log10(1 − ρ_ij), ρ the Pearson correlation of the smoothed voltages of the two ends.

**F5 Documented state** d_e.


## Step 2 — random forest (Liu)

100 trees with the scikit-learn defaults, as in Liu's code; label = true state, output probability p. Training never sees the case being evaluated:

- LV: leave one feeder out (each feeder has a single topology).
- Far West: other configurations of the same network (5-fold, grouped by true configuration).

## Step 3 — decision under physical constraints

- LV: Kruskal on p — candidates by decreasing p while no cycle is formed (radial result). The forest judges every element on its own and does not know that the network must be radial; this step turns its probabilities into a topology that can exist.
- Far West: Kruskal on p so that every bus is supplied, then every element with p > 0.5.

## Step 4 — physics refinement

Local moves from the step-3 result, accepted while the residual J drops by more than 1%, restricted to decisions the forest is unsure about (0.05 < p < 0.95):

- LV: branch exchange (add a candidate, remove one on the loop it forms), pure additions and pure removals.
- Far West: single element changes (first-order screening, exact confirmation), on every third hour of the month.

The gate admits many elements, but few of them change.

## Baselines in the tables

- **Variance-Distance Spanning Tree**: the original method (`variance_distance_spanning_tree/topology`), unchanged.
- **Random forest (Liu)**: his forest per line on F4 + F5 (correlation and documentation), threshold 0.5, no physics, constraints or refinement. His original classifier needs switch bars and a switching history of the same network, which an LV feeder does not have.

## Evaluation protocol

| | SimBench LV | Far West |
|---|---|---|
| Networks | 6 SimBench LV feeders, personalized customer profiles | ACTIVSg2000 area 1 (91 buses, 108 branches) |
| Truth | published topology | 93 configurations with 0–6 branches out |
| Documentation | 30 / 20 / 10% mixed errors (missing, extra and wrong connections) | truth with 20% of the states flipped |
| Data | one month, 15 min | one month, 1 h |
| Cases | 72 per level | 93 (80% only) |

Share correct = min(precision, recall) of the line set (SimBench), share of branches in the right state (Far West).
