#!/usr/bin/env python3
"""
full_eval.py — evaluate a Vulcan heuristic on all test traces/sizes and optionally submit.

Evaluate (saves results to a JSON file):
    python full_eval.py path/to/heuristic.cpp [--server http://localhost:5000]

Submit a saved result file:
    python full_eval.py --submit results/mypolicy_20260612_143000.json [--server http://localhost:5000]
"""

import os, sys, json, argparse, urllib.request, urllib.error
from datetime import datetime, timezone
from evaluator import TRACE_DIR, score_full

RESULTS_DIR    = os.path.join(os.path.dirname(TRACE_DIR), "results")
DEFAULT_SERVER = "http://localhost:5000"


def print_results_table(results: dict, label: str = "Results") -> None:
    print(f"\n{'─'*52}")
    print(f"  {label}")
    print(f"{'─'*52}")
    print(f"  {'Scenario':<20} {'obj_hit_rate':>12} {'byte_hit_rate':>13}")
    print(f"  {'─'*47}")
    for key in sorted(results):
        d = results[key]
        print(f"  {key:<20} {d['obj_hit_rate']:>12.4f} {d['byte_hit_rate']:>13.4f}")
    vals_o = [v["obj_hit_rate"]  for v in results.values() if v["obj_hit_rate"]  > 0]
    vals_b = [v["byte_hit_rate"] for v in results.values() if v["byte_hit_rate"] > 0]
    if vals_b:
        print(f"  {'─'*47}")
        print(f"  {'Mean':<20} {sum(vals_o)/len(vals_o):>12.4f} {sum(vals_b)/len(vals_b):>13.4f}")
    print(f"{'─'*52}")


def save_result(basename: str, cpp_source: str, results: dict, metadata: dict) -> str:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(RESULTS_DIR, f"{basename}_{ts}.json")
    with open(path, "w") as f:
        json.dump({"metadata": metadata, "results": results, "cpp_source": cpp_source}, f, indent=2)
    return path


def submit(payload: dict, server_url: str = DEFAULT_SERVER) -> dict | None:
    data = json.dumps({"metadata": payload["metadata"], "results": payload["results"]}).encode()
    req = urllib.request.Request(
        f"{server_url}/api/submit", data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"[full_eval] HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
    except Exception as e:
        print(f"[full_eval] Submission failed: {e}", file=sys.stderr)
    return None


def _ask(prompt: str, default: str = "") -> str:
    val = input(f"{prompt} [{default}]: " if default else f"{prompt}: ").strip()
    return val or default


def _collect_metadata(basename: str) -> dict:
    print("\n--- Submit to Leaderboard ---")
    return {
        "submitter_name": _ask("Your name"),
        "group_name":     _ask("Group / team name (optional)"),
        "heuristic_name": _ask("Heuristic name", default=basename),
        "description":    _ask("One-line description"),
        "algo_type":      "vulcanevolve",
    }


def _do_submit(payload: dict, server_url: str) -> None:
    print(f"\nSubmitting to {server_url} ...")
    resp = submit(payload, server_url=server_url)
    if resp and "id" in resp:
        print(f"  Submission ID : {resp['id']}")
        print(f"  MRR vs FIFO  : {resp['mrr']:.4f}x" if resp.get("mrr") else "  MRR: N/A")
        print(f"  Leaderboard  : {server_url}")
    else:
        print("  Submission failed. The result file is still saved — retry with it later.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate a Vulcan heuristic and submit to leaderboard")
    parser.add_argument("input", help=".cpp heuristic file (evaluate mode) or results .json (submit mode)")
    parser.add_argument("--submit", action="store_true", help="Submit a previously saved results .json file")
    parser.add_argument("--server", default=DEFAULT_SERVER)
    args = parser.parse_args()

    # --- submit path ---
    if args.submit:
        with open(args.input) as f:
            payload = json.load(f)
        basename = os.path.splitext(os.path.basename(args.input))[0]
        print_results_table(payload["results"], label=f"Results for {basename}")
        if not payload.get("metadata", {}).get("submitter_name"):
            payload["metadata"] = _collect_metadata(basename)
        _do_submit(payload, args.server)
        sys.exit(0)

    # --- evaluate path ---
    with open(args.input) as f:
        cpp_source = f.read()

    results = score_full(cpp_source)
    basename = os.path.splitext(os.path.basename(args.input))[0]
    print_results_table(results, label=f"Results for {basename}")

    metadata = {"submitter_name": "", "group_name": "", "heuristic_name": basename,
                "description": "", "algo_type": "vulcanevolve"}
    saved_path = save_result(basename, cpp_source, results, metadata)
    print(f"\n  Saved to: {saved_path}")
    print(f"  Submit with: python full_eval.py --submit {saved_path}")
