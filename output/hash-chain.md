# Hash chain — chain of truth

- **chain_hash** (over source + numeric results): `ea9e7437e82904bad8c501f462a6cd186ef1b4e49544f0da1d27324af8f2e455`
- master_seed: `513`
- Re-running `python run_all.py && python make_provenance.py` on any machine
  with a compatible numpy reproduces this `chain_hash` (numeric results are
  bit-reproducible from the seed).

## Source (SHA-256) — hashed
- `fea2be1b48936bbd1293f382e618ddff67e5a3e2a5826641e422f03a6429c64b`  blast_radius.py
- `9c1f1154e5903606f3fe9ff208edcb1c44b75bf21eb6551b465be4954f30c2fa`  run_all.py
- `5569dc94bab5dffd81dfc6399d60c6c38e709bb9078d6d1be9cd225091a0fc86`  make_provenance.py
- `c0a64b2e5a9ace8ee77188783b6a678a0801d7c2cd8782ac078896a365f5b59f`  tests/test_blast_radius.py

## Numeric results (SHA-256) — hashed
- `61dad00231e737331ae32c7884176e368ffabf84e46ee017761a1833be01c05e`  results.json
- `5d8ff91c6ae127d87a135750a88d2ae348abb7e6e58b2de04d1e4d0938178d6d`  raw_replicas.jsonl

## Informational (NOT hashed)
- git_commit: `ca43782283a11b83375f9504db775c4bae146411`
- environment: `{'python': '3.14.5', 'numpy': '2.4.6', 'matplotlib': '3.10.9', 'platform': 'macOS-26.6-arm64-arm-64bit-Mach-O'}`
- figure PNG hashes: see provenance.json (toolchain-dependent).
