"""Reproduce every use case 1 result.

    python run_all.py --stage lv --workers 2            # SimBench LV, 70/80/90%
    python run_all.py --stage far_west --workers 2      # Far West, 80%, full mode
    python run_all.py --stage collect                   # copy the per-case results to work/results/
    python run_all.py --stage tables                    # print the table from work/results/

Each scenario runs in its own folder under work/ (or CM_WORK). Steps whose output
exists are skipped, so an interrupted run can be started again. All random choices
are seeded: a rerun gives the shipped numbers.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SB_CODE, FW_CODE = os.path.join(HERE, "simbench"), os.path.join(HERE, "far_west")
WORK = os.environ.get("CM_WORK", os.path.join(HERE, "work"))
FW_DATA = os.environ.get("ACTIVSG_DATA", os.path.join(FW_CODE, "data"))
LV = ["1-LV-rural1--0-sw", "1-LV-semiurb4--0-sw", "1-LV-urban6--0-sw",
      "1-LV-rural2--0-sw", "1-LV-rural3--0-sw", "1-LV-semiurb5--0-sw"]
LEVELS = {70: "0.30", 80: "0.20", 90: "0.10"}           # documentation correct -> DOCERR
BASE = dict(os.environ, MONTH="1", TDM="1", SUFFIX="_month", ONLYJ0="1", GLO="0.05", GHI="0.95",
            OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", ACTIVSG_DATA=FW_DATA)


def env(scenario, **kw):
    e = dict(BASE, CM_WORK=os.path.join(WORK, scenario)); e.update({k: str(v) for k, v in kw.items()})
    return e


def run(args, cwd, e):
    out = os.path.join(e["CM_WORK"], "done", "_".join(a.replace("/", "-") for a in args)[:150])
    if os.path.exists(out):
        return
    print("  $", " ".join(args), f"[{os.path.basename(e['CM_WORK'])}]", flush=True)
    r = subprocess.run([sys.executable, "-W", "ignore"] + args, cwd=cwd, env=e)
    if r.returncode:
        print(f"  ! exit {r.returncode}: {' '.join(args)}", flush=True); return
    os.makedirs(os.path.dirname(out), exist_ok=True); open(out, "w").close()


def parallel(jobs, w):
    with ThreadPoolExecutor(w) as ex:
        list(ex.map(lambda j: run(*j), jobs))


def lv_profiles(w):
    """One month of LV power flow with personalized profiles, shared by every LV scenario."""
    e = env("lv_profiles", INDIV="1")
    parallel([(["sb_sim.py", c], SB_CODE, e) for c in LV], w)
    return os.path.join(e["CM_WORK"], "simbench", "sb_cache_month")


def link_cache(cache, scenario):
    d = os.path.join(WORK, scenario, "simbench"); os.makedirs(d, exist_ok=True)
    if not os.path.exists(os.path.join(d, "sb_cache_month")):
        os.symlink(cache, os.path.join(d, "sb_cache_month"))


def lv_uc1(e, w):
    parallel([(["exp_lv_pipeline.py", "class_0.5", str(i)], SB_CODE, e) for i in range(len(LV))], w)
    run(["exp_lv_pipeline.py", "class_0.5", "combine"], SB_CODE, e)
    run(["exp_final_lv.py", "0"], SB_CODE, e)                      # trains the forests once
    parallel([(["exp_final_lv.py", str(i)], SB_CODE, e) for i in range(1, len(LV))], w)


def lv(w):
    cache = lv_profiles(w)
    for L, err in LEVELS.items():
        s = f"lv_doc{L}"; link_cache(cache, s)
        print(f"[SimBench LV {L}%] use case 1 (no trusted line)", flush=True)
        lv_uc1(env(s, DOCERR=err, CANDS="all"), w)


def fw_inputs(w):
    need = ["case_ACTIVSg2000.m", "ts/load_MW.csv", "ts/load_MVAR.csv", "ts/ren_MW.csv"]
    miss = [f for f in need if not os.path.exists(os.path.join(FW_DATA, f))]
    if miss:
        sys.exit(f"Far West inputs missing in {FW_DATA}: {miss}. See README (Far West data).")
    e = env("fw_scenarios", FWSTEP=1, FWHOURS=720, FWK=5)
    q = os.path.join(e["CM_WORK"], "far_west")
    e.update(FWOUT_MULTI=os.path.join(q, "scen_multi_q_month"), FWOUT7=os.path.join(q, "scen_fw7_month"))
    if not os.path.exists(os.path.join(FW_DATA, "activsg2000_pp.json")):
        run(["build_net.py"], FW_CODE, e)
    cfg = json.load(open(os.path.join(FW_CODE, "configs.json")))
    os.makedirs(os.path.join(q, "scen_q_month"), exist_ok=True)
    print("[Far West] one month of hourly AC power flow per configuration (many hours)", flush=True)
    parallel([(["generate.py", "4000", "720", str(s), str(s + 1), os.path.join(q, "scen_q_month")], FW_CODE, e)
              for s in cfg["singles"]] +
             [(["gen_multi.py", str(i), str(i + 1)], FW_CODE, e) for i in cfg["multi"]], w)
    return q, cfg


def fw_scenario(s, q, cfg, w, **kw):
    e = env(s, FWSTEP=1, FWHOURS=720, FWK=5, **kw)
    d = os.path.join(e["CM_WORK"], "far_west"); os.makedirs(d, exist_ok=True)
    for name in ("scen_q_month", "scen_multi_q_month"):
        if not os.path.exists(os.path.join(d, name)):
            os.symlink(os.path.join(q, name), os.path.join(d, name))
    n1 = 3 * (len(cfg["singles"]) + len(cfg["multi"]))
    step = max(1, n1 // (4 * w))
    parallel([(["fw_ac.py", "build", "uc1", str(a), str(min(a + step, n1))], FW_CODE, e) for a in range(0, n1, step)], w)
    run(["exp_final_fw.py", "uc1", "run", "0", "0"], FW_CODE, e)  # trains the forests once
    parallel([(["exp_final_fw.py", "uc1", "run", str(a), str(a + 6)], FW_CODE, e) for a in range(0, 96, 6)], w)


def far_west(w):
    q, cfg = fw_inputs(w)
    print("[Far West 80%] full mode", flush=True)
    fw_scenario("far_west_doc80", q, cfg, w, DOCERR="0.20")


def collect():
    R = os.path.join(WORK, "results")
    pairs = []
    for L in LEVELS:
        pairs.append((f"lv_doc{L}/simbench/final_lv_month", f"simbench_lv_doc{L}/uc1_final_lv"))
    pairs.append(("far_west_doc80/far_west/final_fw_month", "far_west_doc80/uc1_final_fw"))
    for a, b in pairs:
        src, dst = os.path.join(WORK, a), os.path.join(R, b)
        if not os.path.exists(src):
            print("  missing:", a); continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("*.pkl"))
    print("collected in", R)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["lv", "far_west", "collect", "tables"])
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    if a.stage == "collect":
        collect()
    elif a.stage == "tables":
        subprocess.run([sys.executable, os.path.join(HERE, "make_tables.py"), "--dir", os.path.join(WORK, "results")])
    else:
        globals()[a.stage](a.workers)
