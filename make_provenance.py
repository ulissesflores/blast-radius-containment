#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_provenance.py — bind the SHA-256 chain of truth for this artifact.

Writes:
  output/provenance.json — machine-readable record: source hashes, output
                           hashes, parameters/seed, environment, git commit,
                           and a single `chain_hash` over all of the above.
  output/hash-chain.md   — human-readable audit manifest.

The `chain_hash` is the audit anchor: any change to source, parameters or
results changes it. Run AFTER run_all.py.
"""
from __future__ import annotations
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"

SOURCE = ["blast_radius.py", "run_all.py", "make_provenance.py",
          "tests/test_blast_radius.py"]
RESULTS = ["results.json", "raw_replicas.jsonl",
           "fig1_blast_distribuicao.png", "fig2_blast_vs_segmentos.png",
           "fig3_heatmap_seg_deteccao.png", "fig4_fronteira_seg_perf.png",
           "fig5_sensibilidade.png"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, timeout=10).stdout.strip() or "n/a"
    except Exception:
        return "n/a"


def dep_versions() -> dict:
    out = {"python": sys.version.split()[0]}
    for mod in ("numpy", "matplotlib"):
        try:
            out[mod] = __import__(mod).__version__
        except Exception:
            out[mod] = "n/a"
    return out


def main():
    src = {f: sha256(ROOT / f) for f in SOURCE if (ROOT / f).exists()}
    res = {f: sha256(OUT / f) for f in RESULTS if (OUT / f).exists()}
    params = json.loads((OUT / "results.json").read_text())["params"] if (OUT / "results.json").exists() else {}
    seed = json.loads((OUT / "results.json").read_text()).get("master_seed") if (OUT / "results.json").exists() else None

    record = {
        "artifact": "blast-radius-containment",
        "master_seed": seed,
        "parameters": params,
        "environment": {**dep_versions(), "platform": platform.platform()},
        "git_commit": git_commit(),
        "source_sha256": src,
        "results_sha256": res,
    }
    # chain hash over a canonical serialization of everything above
    canonical = json.dumps(record, sort_keys=True, ensure_ascii=False).encode("utf-8")
    record["chain_hash"] = hashlib.sha256(canonical).hexdigest()
    (OUT / "provenance.json").write_text(json.dumps(record, indent=2, ensure_ascii=False))

    lines = ["# Hash chain — chain of truth", "",
             f"- **chain_hash**: `{record['chain_hash']}`",
             f"- master_seed: `{seed}`",
             f"- git_commit: `{record['git_commit']}`",
             f"- environment: `{record['environment']}`", "",
             "## Source (SHA-256)"]
    lines += [f"- `{h}`  {f}" for f, h in src.items()]
    lines += ["", "## Results (SHA-256)"]
    lines += [f"- `{h}`  {f}" for f, h in res.items()]
    lines += ["", "> If any source or result changes, `chain_hash` changes. "
                  "Re-run `python run_all.py && python make_provenance.py` to regenerate."]
    (OUT / "hash-chain.md").write_text("\n".join(lines) + "\n")
    print("chain_hash:", record["chain_hash"])


if __name__ == "__main__":
    main()
