# Demo input

Two forms of the strandbeest input:

- **`parts_raw/`** — the **12 real flat parts** exported from Fusion by `fusion_export_dxf.py`
  (Stage A): 8 leg links, 2 gears, 2 spacer plates, each a clean 1:1 mm outline + holes, plus
  `parts_manifest.csv`. **This is the directly runnable pipeline input** — point `config.json`'s
  `parts_dir` at it and run `py ../../pack_dxf.py` to reproduce the sheets in
  [`../../output/demo`](../../output/demo).

- **`beest-fusion-cache-backup.zip`** — the upstream Fusion source (assembly + all component
  `.f3d` cache files) the parts were exported from. Archival; raw cache files don't open standalone
  (a `.f3z` export is the portable format). Open the design in Fusion and run Stage A to regenerate
  `parts_raw/` yourself.

Round hardware (rods, pins, bearings, the crank) is intentionally **not** here — those are bought,
not cut.
