"""Aggregate OpenPowerlifting results into the numbers behind splyt.fit/data/what-lifters-total.

Usage: python3 -I analyze.py <openpowerlifting.csv> <out.json>

Data: OpenPowerlifting (https://www.openpowerlifting.org), public domain.

Population for the main tables: full-power meets (Event SBD), Raw (sleeves) equipment,
Sex M or F, a valid total with all three lifts, bodyweight recorded, meet dated
2023-01-01 to 2025-12-31. Each lifter (OpenPowerlifting's unique Name key) counts once:
their best-total raw SBD meet in the window. Equipped (Single-ply) and tested/untested
comparisons use the same rules on their own subsets.
"""
import csv, json, sys, statistics
from collections import defaultdict
from datetime import date

SRC, OUT = sys.argv[1], sys.argv[2]
WIN_START, WIN_END = "2023-01-01", "2025-12-31"
LB = 2.2046226218
PLATES_KG = {1: 135 / LB, 2: 225 / LB, 3: 315 / LB, 4: 405 / LB, 5: 495 / LB}
IPF = {
    "M": [59, 66, 74, 83, 93, 105, 120],
    "F": [47, 52, 57, 63, 69, 76, 84],
}


def f(x):
    try:
        v = float(x)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def ipf_class(sex, bw):
    for c in IPF[sex]:
        if bw <= c:
            return f"{c}"
    return f"{IPF[sex][-1]}+"


def pct(vals, ps=(25, 50, 75, 90, 99)):
    s = sorted(vals)
    n = len(s)
    out = {}
    for p in ps:
        k = (n - 1) * p / 100
        lo, hi = int(k), min(int(k) + 1, n - 1)
        out[str(p)] = round(s[lo] + (s[hi] - s[lo]) * (k - lo), 1)
    return out


best = {}          # (pop, name) -> row dict, best total in window
history = defaultdict(list)  # name -> [(date, total)] raw SBD, all time
first_seen = {}    # name -> earliest meet date (any event/equipment)
meets = set()

with open(SRC, newline="", encoding="utf8") as fh:
    for r in csv.DictReader(fh):
        name, sex, d = r["Name"], r["Sex"], r["Date"]
        if not name or not d:
            continue
        if name not in first_seen or d < first_seen[name][0]:
            first_seen[name] = (d, r["Event"], r["Equipment"])
        if sex not in ("M", "F") or r["Event"] != "SBD":
            continue
        s, b, dl, t, bw = (f(r["Best3SquatKg"]), f(r["Best3BenchKg"]), f(r["Best3DeadliftKg"]),
                           f(r["TotalKg"]), f(r["BodyweightKg"]))
        if not (s and b and dl and t and bw):
            continue
        eq = r["Equipment"]
        if eq == "Raw":
            history[name].append((d, t))
        if not (WIN_START <= d <= WIN_END):
            continue
        meets.add((r["MeetName"], d, r["Federation"]))
        rec = {"sex": sex, "s": s, "b": b, "d": dl, "t": t, "bw": bw, "dots": f(r["Dots"]),
               "age": f(r["Age"]), "tested": r["Tested"] == "Yes"}
        for pop in ({"Raw": ["raw"], "Single-ply": ["single"]}.get(eq, [])):
            key = (pop, name)
            if key not in best or t > best[key]["t"]:
                best[key] = rec

raw = [v for (p, _), v in best.items() if p == "raw"]
single = [v for (p, _), v in best.items() if p == "single"]
out = {"source": "OpenPowerlifting (public domain), data revision 2026-11-14",
       "window": [WIN_START, WIN_END], "meets": len(meets), "n_raw": len(raw), "n_single": len(single)}

MIN = 200
for sex in ("M", "F"):
    rs = [x for x in raw if x["sex"] == sex]
    sec = out[sex] = {"n": len(rs)}
    sec["overall"] = {k: pct([x[k] for x in rs]) for k in ("s", "b", "d", "t", "bw")}
    sec["dots"] = pct([x["dots"] for x in rs if x["dots"]])
    # DOTS histogram, 25-point bins
    hist = defaultdict(int)
    for x in rs:
        if x["dots"]:
            hist[int(x["dots"] // 25) * 25] += 1
    sec["dots_hist"] = sorted(hist.items())
    # IPF classes
    cls = defaultdict(list)
    for x in rs:
        cls[ipf_class(sex, x["bw"])].append(x)
    order = [str(c) for c in IPF[sex]] + [f"{IPF[sex][-1]}+"]
    sec["ipf"] = [{"cls": c, "n": len(cls[c]), **{k: pct([x[k] for x in cls[c]]) for k in ("s", "b", "d", "t")}}
                  for c in order if len(cls[c]) >= MIN]
    # 10-lb bands
    bands = defaultdict(list)
    for x in rs:
        bands[int(x["bw"] * LB // 10) * 10].append(x)
    sec["bands_lb"] = [{"lb": k, "n": len(v), **{m: pct([x[m] for x in v], (25, 50, 75, 90)) for m in ("s", "b", "d", "t")}}
                       for k, v in sorted(bands.items()) if len(v) >= MIN]
    # Ratios (per lifter, then median)
    sec["ratio"] = {"bench_to_squat": round(statistics.median(x["b"] / x["s"] for x in rs), 3),
                    "deadlift_to_squat": round(statistics.median(x["d"] / x["s"] for x in rs), 3),
                    "squat_share": round(statistics.median(x["s"] / x["t"] for x in rs), 3),
                    "bench_share": round(statistics.median(x["b"] / x["t"] for x in rs), 3),
                    "deadlift_share": round(statistics.median(x["d"] / x["t"] for x in rs), 3)}
    # Milestones
    n = len(rs)
    sec["milestones"] = {
        **{f"bench_{p}_plate": round(100 * sum(x["b"] >= kg - 0.01 for x in rs) / n, 1) for p, kg in PLATES_KG.items()},
        "bench_1x_bw": round(100 * sum(x["b"] >= x["bw"] for x in rs) / n, 1),
        "bench_1_5x_bw": round(100 * sum(x["b"] >= 1.5 * x["bw"] for x in rs) / n, 1),
        "squat_2x_bw": round(100 * sum(x["s"] >= 2 * x["bw"] for x in rs) / n, 1),
        "deadlift_2_5x_bw": round(100 * sum(x["d"] >= 2.5 * x["bw"] for x in rs) / n, 1),
        "deadlift_3x_bw": round(100 * sum(x["d"] >= 3 * x["bw"] for x in rs) / n, 1),
        "squat_4_plate": round(100 * sum(x["s"] >= PLATES_KG[4] - 0.01 for x in rs) / n, 1),
        "deadlift_5_plate": round(100 * sum(x["d"] >= PLATES_KG[5] - 0.01 for x in rs) / n, 1),
    }
    # Age curve: 5-year buckets, median DOTS and total
    ages = defaultdict(list)
    for x in rs:
        if x["age"] and 14 <= x["age"] < 80:
            ages[int(x["age"] // 5) * 5].append(x)
    sec["age"] = [{"age": a, "n": len(v), "dots": round(statistics.median(x["dots"] for x in v if x["dots"]), 1),
                   "t": round(statistics.median(x["t"] for x in v), 1)}
                  for a, v in sorted(ages.items()) if len(v) >= MIN]
    # Tested vs untested
    sec["tested"] = {lab: {"n": len(v), "t": pct([x["t"] for x in v], (50,))["50"],
                           "dots": round(statistics.median(x["dots"] for x in v if x["dots"]), 1)}
                     for lab, v in (("tested", [x for x in rs if x["tested"]]),
                                    ("untested", [x for x in rs if not x["tested"]]))}
    ss = [x for x in single if x["sex"] == sex]
    sec["single_ply"] = {"n": len(ss), "t": pct([x["t"] for x in ss], (50,))["50"],
                         "s": pct([x["s"] for x in ss], (50,))["50"], "b": pct([x["b"] for x in ss], (50,))["50"],
                         "d": pct([x["d"] for x in ss], (50,))["50"]}
    sec["raw_median"] = {k: sec["overall"][k]["50"] for k in ("s", "b", "d", "t")}

# Progression: lifters whose first-ever meet was a raw full-power meet in 2015-2022.
def dd(s):
    return date(int(s[:4]), int(s[5:7]), int(s[8:10]))

prog = {"M": defaultdict(list), "F": defaultdict(list)}
sexmap = {}
for (p, name), v in best.items():
    sexmap[name] = v["sex"]
for name, h in history.items():
    fs = first_seen.get(name)
    sex = sexmap.get(name)
    if not fs or sex is None or fs[1] != "SBD" or fs[2] != "Raw" or not ("2015-01-01" <= fs[0] <= "2022-12-31"):
        continue
    h.sort()
    d0 = dd(fs[0])
    base = max(t for d, t in h if d == fs[0]) if any(d == fs[0] for d, _ in h) else None
    if not base:
        continue
    for yr in (1, 2, 3):
        win = [t for d, t in h if 365 * (yr - 1) < (dd(d) - d0).days <= 365 * yr]
        if win:
            prog[sex][yr].append(max(win) / base - 1)
out["progression"] = {sex: [{"year": yr, "n": len(v), "median_gain_pct": round(100 * statistics.median(v), 1),
                             "p75_gain_pct": round(100 * statistics.quantiles(v, n=4)[2], 1)}
                            for yr, v in sorted(prog[sex].items()) if len(v) >= MIN]
                      for sex in ("M", "F")}

json.dump(out, open(OUT, "w"), indent=1)
print(json.dumps({k: out[k] for k in ("meets", "n_raw", "n_single")}))
