# Demo output — nested cut sheets + BOM

Example output produced by the pipeline:

- `sheet_01.dxf`, `sheet_02.dxf` — the nested cut sheets (2440×1220 mm), ready for a laser/CNC.
- `sheet_01.svg`, `sheet_02.svg` — the same, rendered for quick viewing.
- `BOM.csv` — cut-part quantities (×10 kits) + hardware list.

**Source:** this was generated from the synthetic test parts (`make_test_parts.py`), which is the
fully runnable end-to-end demo (no Fusion needed). Reproduce with:

```bash
py make_test_parts.py
py pack_dxf.py
```

Parts were scaled ×6 and holes reset to real hardware sizes (6.5 mm pivots, 22 mm 608-bearing seats)
— note the hole sizes are **independent** of the scale factor. To generate the *real* strandbeest
sheets instead, run Stage A in Fusion on the source in [`../../input/demo`](../../input/demo) first.
