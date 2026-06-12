#!/usr/bin/env python3
"""
seed_baselines.py — populate the leaderboard DB with:
  1. All classical algorithms from baselines_all.json
  2. All Vulcan heuristics from policysmith-demo/results.json (scored on w106 only,
     so full 30-scenario results must come from re-running full_eval.py on them —
     we insert what we have and mark the rest as 0.0)

Run once after baselines.sh:
  python3 leaderboard-webapp/seed_baselines.py
"""
import os, sys, json, sqlite3
from datetime import datetime, timezone

HERE     = os.path.dirname(os.path.abspath(__file__))
ROOT     = os.path.dirname(HERE)
DB_PATH  = os.path.join(HERE, "leaderboard.db")

BASELINES_ALL = os.path.join(ROOT, "baselines_all.json")
RESULTS_JSON  = os.path.join(ROOT, "policysmith-demo", "results.json")
FIFO_FILE     = os.path.join(ROOT, "fifo_baselines.json")

TRACES = ["w86", "w87", "w89", "w90", "w93", "w94", "w99", "w103", "w105", "w106"]
SIZES  = ["1pct", "3pct", "10pct"]
ALL_KEYS = [f"{t}_{s}" for t in TRACES for s in SIZES]

ALGO_DESCRIPTIONS = {
    "fifo":      "First-In First-Out — evict the oldest inserted object",
    "lru":       "Least Recently Used — evict the least recently accessed object",
    "lfu":       "Least Frequently Used — evict the object with lowest access count",
    "lfuda":     "LFU with Dynamic Aging — LFU variant that ages counters over time",
    "arc":       "Adaptive Replacement Cache — balances recency and frequency",
    "s3-fifo":   "S3-FIFO — small/main/ghost FIFO queues, state-of-the-art 2023",
    "clock":     "CLOCK — efficient LRU approximation with a reference bit",
    "wtinyLFU":  "Window TinyLFU — frequency sketch + window/main caches (Caffeine)",
    "lhd":       "LHD — Least Hit Density, size-aware eviction policy",
}


def load_fifo_baselines():
    if not os.path.exists(FIFO_FILE):
        return {}
    with open(FIFO_FILE) as f:
        return json.load(f).get("results", {})


def compute_mrr(results: dict, fifo: dict, metric="byte_hit_rate") -> float | None:
    if not fifo:
        return None
    ratios = []
    for k, v in results.items():
        fv = fifo.get(k, {}).get(metric, 0)
        if fv > 0:
            ratios.append(v[metric] / fv)
    return sum(ratios) / len(ratios) if ratios else None


def empty_results() -> dict:
    return {k: {"obj_hit_rate": 0.0, "byte_hit_rate": 0.0,
                "n_req": 0, "n_miss": 0, "cache_size": 0, "runtime_seconds": 0.0}
            for k in ALL_KEYS}


def summary_stats(results: dict):
    obj_vals  = [v["obj_hit_rate"]  for v in results.values() if v.get("obj_hit_rate",  0) > 0]
    byte_vals = [v["byte_hit_rate"] for v in results.values() if v.get("byte_hit_rate", 0) > 0]
    mean_obj  = sum(obj_vals)  / len(obj_vals)  if obj_vals  else 0.0
    mean_byte = sum(byte_vals) / len(byte_vals) if byte_vals else 0.0
    return round(mean_obj, 6), round(mean_byte, 6)


def insert(db, name, group, heuristic, description, algo_type, results, fifo, submitted_at):
    mrr = compute_mrr(results, fifo)
    mean_obj, mean_byte = summary_stats(results)
    db.execute(
        """INSERT OR IGNORE INTO submissions
           (submitter_name, group_name, heuristic_name, description,
            algo_type, submitted_at, results_json, mrr, mean_obj_hr, mean_byte_hr)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (name, group, heuristic, description, algo_type,
         submitted_at, json.dumps(results), mrr, mean_obj, mean_byte),
    )


def init_db(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            submitter_name  TEXT NOT NULL,
            group_name      TEXT,
            heuristic_name  TEXT NOT NULL,
            description     TEXT,
            algo_type       TEXT DEFAULT 'vulcanevolve',
            submitted_at    TEXT NOT NULL,
            results_json    TEXT NOT NULL,
            mrr             REAL,
            mean_obj_hr     REAL,
            mean_byte_hr    REAL
        )
    """)


def main():
    db = sqlite3.connect(DB_PATH)
    init_db(db)
    fifo = load_fifo_baselines()

    seeded = 0
    ts_base = "2026-06-01T00:00:00+00:00"

    # ---- 1. Classical baselines ----
    if not os.path.exists(BASELINES_ALL):
        print(f"WARNING: {BASELINES_ALL} not found — skipping classical baselines.")
        print("Run baselines.sh first.")
    else:
        with open(BASELINES_ALL) as f:
            all_baselines = json.load(f)

        for algo, algo_results in all_baselines.items():
            # Pad any missing keys with zeros
            full_results = empty_results()
            for k, v in algo_results.items():
                if k in full_results:
                    full_results[k] = v
            desc = ALGO_DESCRIPTIONS.get(algo, f"Classical cache algorithm: {algo}")
            insert(db, "Baseline", "System", algo.upper(), desc,
                   "classical", full_results, fifo, ts_base)
            seeded += 1
            print(f"  Seeded classical: {algo}")

    # ---- 2. Vulcan heuristics from results.json ----
    if not os.path.exists(RESULTS_JSON):
        print(f"WARNING: {RESULTS_JSON} not found — skipping Vulcan heuristics.")
    else:
        with open(RESULTS_JSON) as f:
            vulcan_results = json.load(f)

        size_map = {0.01: "1pct", 0.03: "3pct", 0.1: "10pct"}

        for i, entry in enumerate(vulcan_results):
            # results.json only has the w106 training score; we fill the rest with 0
            # The full 30-scenario eval should come from re-running full_eval.py
            full_results = empty_results()
            score = entry.get("score", 0.0)
            # Assign the known score to w106_10pct (that's what evaluator.py uses)
            full_results["w106_10pct"] = {
                "obj_hit_rate": 0.0,
                "byte_hit_rate": round(score, 6),
                "n_req": 0, "n_miss": 0, "cache_size": 0, "runtime_seconds": 0.0,
            }
            iteration = entry.get("iter", i)
            name = "LRU (seed)" if iteration == -1 else f"Vulcan iter {iteration} (#{i+1})"
            desc = "Seed LRU policy" if iteration == -1 else f"LLM-evolved Vulcan heuristic, iteration {iteration}"
            ts = f"2026-06-01T{i:02d}:00:00+00:00"
            insert(db, "PolicySmith", "Demo", name, desc,
                   "vulcanevolve", full_results, fifo, ts)
            seeded += 1
            print(f"  Seeded Vulcan: {name} (score={score:.4f})")

    db.commit()
    db.close()
    print(f"\nSeeded {seeded} entries into {DB_PATH}")
    print("Start the webapp: python3 leaderboard-webapp/app.py")


if __name__ == "__main__":
    main()
