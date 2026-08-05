# Free-tier Fusion DXF export pipeline

Fusion 360 **Personal** blocks File-menu DXF export — but sketch DXF export and the Python API still
work. This pipeline uses that to go from a Fusion assembly to **scaled, hole-corrected, nested cut
sheets + a BOM**, reproducibly and precisely (only exact affine transforms are applied — no geometry
is redrawn, so press/clearance fits survive).

Built for a laser/CNC strandbeest workshop (the worked example throughout), but it works for any
flat-part Fusion assembly you need to batch-export, rescale, and nest for cutting.

![example nested sheet](examples/sheet_01.svg)

## Setup (once)
```bash
py -m pip install ezdxf rectpack
```

## Run
```bash
# Stage A — inside Fusion: Utilities > ADD-INS > Scripts > run fusion_export_dxf.py
#   -> writes parts_raw/<part>.dxf (1:1 mm) + parts_raw/parts_manifest.csv

# Stages B-D — from this folder:
py pack_dxf.py            # -> nested/sheet_XX.dxf + nested/BOM.csv
```

To sanity-check the pipeline without Fusion:
```bash
py make_test_parts.py    # writes synthetic parts into parts_raw/
py pack_dxf.py
```

## Configure — `config.json`
| key | meaning |
|---|---|
| `scale` | master build scale. Compute as `target_leg_mm / current_leg_mm`. Applied to link geometry only. |
| `kits` | how many kits to nest (10). |
| `sheet_w_mm`, `sheet_h_mm` | sheet size. 2440×1220 = full NL berken-multiplex sheet; set to the cutter bed if smaller. |
| `part_spacing_mm` | gap between parts. |
| `sheet_margin_mm` | keep-clear border. |
| `allow_rotate` | let the nester rotate parts 90° for tighter packing. |
| `default_hole_mm` | diameter every hole becomes (pivot = M6 clearance, e.g. 6.5). **Not scaled** — real hardware size. |
| `part_hole_overrides` | `{ "part_name": mm }` — set all holes in that part to a different size (e.g. `"frame": 22` for 608 seats). |
| `hardware_per_kit` | fastener counts, multiplied ×kits into the BOM. |

## The key idea: size and holes are decoupled
- **Scale** stretches link *lengths* (hole centres) to make the beest big.
- **Hole diameters** are set to real hardware sizes and are **not** scaled — so a 6.5 mm pivot stays
  6.5 mm whether the beest is knee- or waist-height. `part_hole_overrides` handles the few holes that
  need bearing seats instead.

## After nesting
- `nested/sheet_XX.dxf` → send to the laser/CNC (or into Deepnest first for tighter true-shape nesting
  — feed it the same `parts_processed/*.dxf`).
- **Kerf/bit comp:** do it in the cutter software (LightBurn / CAM), or add an offset step here.
- **Cut a fit-test coupon first** (holes at nominal ±0.1/0.2 mm) to dial in the press/clearance fits
  on the real machine + material before cutting all 10 kits.

## Files
- `fusion_export_dxf.py` — Stage A, runs inside Fusion.
- `pack_dxf.py` — Stages B–D (scale, hole-correct, nest, BOM).
- `make_test_parts.py` — synthetic parts for testing.
- `config.json` — all knobs.
