# Demo input — Fusion source

`beest-fusion-cache-backup.zip` is the Fusion 360 source for the strandbeest example: the top-level
assembly (`_working` / `_FML`) plus every referenced component, as Fusion's local working-cache
`.f3d` files.

**These raw cache files don't open standalone in Fusion** (the assembly references components by
GUID). They're here as the archival source. To actually work from it:

1. In Fusion, open the design (or a `.f3z` export of it — a `.f3z` is the portable, self-contained
   format and is what you'd normally publish here).
2. Run [`../../fusion_export_dxf.py`](../../fusion_export_dxf.py) (Stage A) to produce the per-part
   DXFs that the pipeline consumes.
3. Run `py ../../pack_dxf.py` to get scaled, hole-corrected, nested sheets.

For a fully runnable, no-Fusion demo, see `make_test_parts.py` in the repo root, which generates
synthetic parts that produce the output in [`../../output/demo`](../../output/demo).
