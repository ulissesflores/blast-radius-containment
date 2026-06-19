#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_provenance.py — bind the SHA-256 chain of truth for this artifact.

Design (machine-independent guarantee):
  `chain_hash` is computed ONLY over deterministic, machine-independent inputs —
  the SOURCE code and the NUMERIC results (results.json + raw_replicas.jsonl),
  plus the seed and parameters. Those numeric results are bit-reproducible from
  the fixed seed (numpy default_rng), so re-running on ANY machine with a
  compatible numpy yields the SAME chain_hash.

  Environment (OS, Python/numpy/matplotlib versions), git commit and figure PNG
  hashes are recorded as INFORMATIONAL only and are NOT folded into chain_hash —
  precisely because they vary by machine/toolchain (e.g., matplotlib/freetype
  changes PNG bytes) and would otherwise break the cross-machine guarantee.

Writes:
  output/provenance.json — chain_hash + the hashed core + an `informational` block.
  output/hash-chain.md   — human-readable audit manifest.

Run AFTER run_all.py.
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
CORE_DATA = ["results.json", "raw_replicas.jsonl"]          # numeric, deterministic -> hashed
FIGURES = ["fig1_blast_distribuicao.png", "fig2_blast_vs_segmentos.png",
           "fig3_heatmap_seg_deteccao.png", "fig4_fronteira_seg_perf.png",
           "fig5_sensibilidade.png"]                          # toolchain-dependent -> informational


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
    results = json.loads((OUT / "results.json").read_text()) if (OUT / "results.json").exists() else {}

    # --- hashed core: deterministic & machine-independent -----------------------
    core = {
        "artifact": "blast-radius-containment",
        "master_seed": results.get("master_seed"),
        "parameters": results.get("params", {}),
        "source_sha256": {f: sha256(ROOT / f) for f in SOURCE if (ROOT / f).exists()},
        "data_sha256": {f: sha256(OUT / f) for f in CORE_DATA if (OUT / f).exists()},
    }
    canonical = json.dumps(core, sort_keys=True, ensure_ascii=False).encode("utf-8")
    chain_hash = hashlib.sha256(canonical).hexdigest()

    record = dict(core)
    record["chain_hash"] = chain_hash
    record["informational"] = {                                # recorded, NOT hashed
        "note": "environment, git_commit and figure hashes vary by machine/toolchain "
                "and are excluded from chain_hash to keep the guarantee machine-independent.",
        "environment": {**dep_versions(), "platform": platform.platform()},
        "git_commit": git_commit(),
        "figures_sha256": {f: sha256(OUT / f) for f in FIGURES if (OUT / f).exists()},
    }
    (OUT / "provenance.json").write_text(json.dumps(record, indent=2, ensure_ascii=False))

    lines = ["# Hash chain — chain of truth", "",
             f"- **chain_hash** (over source + numeric results): `{chain_hash}`",
             f"- master_seed: `{core['master_seed']}`",
             "- Re-running `python run_all.py && python make_provenance.py` on any machine",
             "  with a compatible numpy reproduces this `chain_hash` (numeric results are",
             "  bit-reproducible from the seed).", "",
             "## Source (SHA-256) — hashed"]
    lines += [f"- `{h}`  {f}" for f, h in core["source_sha256"].items()]
    lines += ["", "## Numeric results (SHA-256) — hashed"]
    lines += [f"- `{h}`  {f}" for f, h in core["data_sha256"].items()]
    lines += ["", "## Informational (NOT hashed)",
              f"- git_commit: `{record['informational']['git_commit']}`",
              f"- environment: `{record['informational']['environment']}`",
              "- figure PNG hashes: see provenance.json (toolchain-dependent)."]
    (OUT / "hash-chain.md").write_text("\n".join(lines) + "\n")
    print("chain_hash (machine-independent):", chain_hash)


if __name__ == "__main__":
    main()
