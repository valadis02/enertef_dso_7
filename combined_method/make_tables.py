"""Print the use case 1 result table from a results folder.

    python make_tables.py                 # from the shipped results (results/)
    python make_tables.py --dir <folder>  # from a fresh run collected with run_all.py --stage collect
"""
import argparse
import glob
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
M = ["documented", "variance_distance_spanning_tree", "liu_only", "combined"]
HEAD = ("| Use case · scenario | Documented | Variance-Distance Spanning Tree | Random forest (Liu) | Combination | Siamese (Liu) |\n"
        "|---|---|---|---|---|---|")


def pc(x):
    return f"{100 * x:.1f}"


def lv_uc1(d):
    R = pd.concat([pd.read_csv(f) for f in glob.glob(f"{d}/res_*.csv")])
    return [R[m].mean() for m in M], len(R)


def assign(f, liu="liu_cluster"):
    R = pd.read_csv(f)
    return [R.documented.mean(), R.variance_distance_spanning_tree.mean(), R[liu].mean(), R.combined.mean()], len(R)


def mv(d):
    R = pd.concat([pd.read_csv(f) for f in glob.glob(f"{d}/res_*.csv")])
    return [R[R.method == m].open_found.mean() for m in M], [int(R[R.method == m].false_open.sum()) for m in M]


def fw(d, pattern, open_metric):
    rows = [json.load(open(f)) for f in sorted(glob.glob(f"{d}/{pattern}"))]
    out, fo = [], []
    for m in ["doc"] + M[1:]:
        acc, of, n = [], [], 0
        for r in rows:
            t = np.array(r["truth"]); s = np.array(r[m]); to = t == 0
            acc.append((s == t).mean()); of.append(((s == 0) & to).sum() / max(to.sum(), 1)); n += int(((s == 0) & ~to).sum())
        out.append(np.mean(of) if open_metric else np.mean(acc)); fo.append(n)
    return out, fo, len(rows)


def levels(fn, lv=(70, 80, 90)):
    vals = []
    for L in lv:
        try:
            vals.append(fn(L))
        except Exception:
            vals.append(None)
    cells = []
    for k in range(4):
        cells.append(" / ".join(pc(v[k]) if v else "–" for v in vals))
    return cells


def row(label, cells, siam="–"):
    return f"| {label} | " + " | ".join(cells) + f" | {siam} |"


def main(R):
    out = [HEAD.replace(" Siamese (Liu) |", "").replace("|---|---|---|---|---|---|", "|---|---|---|---|---|")]
    row = lambda label, cells: f"| {label} | " + " | ".join(cells) + " |"
    out.append(row("SimBench LV", levels(lambda L: lv_uc1(f"{R}/simbench_lv_doc{L}/uc1_final_lv")[0])))
    v, _, _ = fw(f"{R}/far_west_doc80/uc1_final_fw", "uc1_*.json", False)
    out.append(row("Far West (80% only)", [pc(x) for x in v]))
    print("\n".join(out))
    print("\nCells: documentation 70 / 80 / 90% correct; share of lines (branches) in the right state.")
    print("Cases: SimBench LV 72 per level, Far West 93.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--dir", default=os.path.join(HERE, "results")); a = ap.parse_args()
    main(a.dir)
