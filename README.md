# Free-tier Fusion DXF export pipeline

Turn a Fusion 360 **Personal** design into **scaled, hole-corrected, nested, laser-ready cut sheets +
a BOM** — precisely and reproducibly — even though Fusion Personal won't export DXF from the File menu.

![Strandbeest walking — Fusion motion study](video/beest_walk_readme.gif)

*The mechanism this pipeline cuts parts for — gear-driven, three leg-racks phased 120° apart, one hand
crank. ([full-res MP4](video/beest_walk.mp4))*

---

## Why this exists — the Strandbeest workshop

This drives a real event: a **2-day hackathon in The Hague** where **30 people (six teams of five)**
each build a **waist-height, hand-cranked walking [Strandbeest](https://en.wikipedia.org/wiki/Jansen%27s_linkage)**
out of flat-cut plywood.

The animation above is the Fusion 360 model. The catch: it's designed at desktop scale with 4 mm
holes, and **Fusion Personal can't export DXF from the menu.** To turn one CAD model into six cuttable
kits you have to:

1. get every flat part out of Fusion as a precise DXF (Fusion Personal *can* do this via the sketch/API — this automates it),
2. **scale** the whole thing up to ~1 m,
3. resize each hole to a **real bearing/rod** — *not* by scaling it (a 4 mm hole must become a **13 mm
   bearing seat**, not a 24 mm one), but by setting it to the hardware size,
4. **nest** the parts onto plywood sheets and **label** each one,
5. spit out a **shopping list**.

That's this repo, end to end. Output in [`output/demo/`](output/demo): six laser-ready sheets (cut on
[Snijlab](https://snijlab.nl)) + a [BOM with purchase links](output/demo/BOM.md). One team's worth of
parts (a whole beest on one sheet) is in [`nested_1kit/`](nested_1kit).

### How the beest maps to the pipeline
| | |
|---|---|
| **Legs** | 6 (three racks × mirror pairs) → 8 unique links, 6 of each per kit |
| **Drive** | 3:4 reduction (12T pinion → 16T driven), crank pins phased 120°, hand-cranked |
| **Pivots** | M6 bolt through an **F686** bearing in every rotating link hole (13 mm seat), nyloc-capped |
| **Crankshaft** | **12 mm rod in 6001 bearings** (28 mm seats), supported at each rack level |
| **Scale** | ×6 → ~waist height; holes fixed to hardware (13 / 28 / 12 / 6 mm), independent of scale |

---

## What the pipeline does
**Stage A** (inside Fusion) — projects each flat component's face to a DXF at true 1:1 mm + a parts
manifest. **Stages B–D** (`pack_dxf.py`) — scale to build size, set each hole to its real hardware
diameter (only the 4 mm through-holes are treated as holes, so intentional larger holes survive),
nest all copies onto sheets with rectpack, etch each part's name on a `LABEL` layer, and write the BOM.
Geometry is never redrawn — only exact affine transforms — so fits are preserved.

## Setup (once)
```bash
py -m pip install ezdxf rectpack
```

## Run
```bash
# Stage A — inside Fusion: Utilities > ADD-INS > Scripts > run fusion_export_dxf.py
#   -> parts_raw/<part>.dxf (1:1 mm) + parts_raw/parts_manifest.csv

# Stages B-D:
py pack_dxf.py            # -> nested/sheet_XX.dxf + BOM.csv (+ BOM.md by hand)
```
No Fusion? `py make_test_parts.py && py pack_dxf.py` runs it on synthetic parts.

## Configure — `config.json`
| key | meaning |
|---|---|
| `scale` | master build scale = `target_leg_mm / current_leg_mm`. Applied to geometry only. |
| `kits` | how many kits to nest (6). |
| `sheet_w_mm`, `sheet_h_mm` | sheet size (2440×1220 = full NL berken-multiplex sheet). |
| `default_hole_mm` | size every through-hole becomes unless overridden (13 = F686 pivot). **Not scaled.** |
| `hole_source_dia_mm` | only circles this size (4 mm) are treated as holes; bigger circles are left as outline. |
| `part_hole_overrides` | per-part hole size; per-hole roles go in `parts_raw/hole_roles.csv` (part,cx,cy,dia). |
| `hardware_per_kit` | fastener counts → the BOM ×kits. |

## The key idea: size and holes are decoupled
- **Scale** stretches link *lengths* to make the beest big.
- **Hole diameters** are fixed to real hardware and are **never** scaled — a 13 mm bearing seat stays
  13 mm whether the beest is knee- or waist-height. `hole_roles.csv` assigns bearing vs friction per hole.

## After nesting
- `nested/sheet_XX.dxf` → laser/CNC. Set the `LABEL` layer to **score/engrave**, everything else to cut.
- Push `parts_processed/*.dxf` through **Deepnest** for tighter true-shape nesting if you want fewer sheets.
- **Cut a fit-test coupon first** to dial in kerf before committing all kits.

## Files
- `fusion_export_dxf.py` — Stage A (runs in Fusion). · `fusion_walk_frames.py` — captures the walk animation.
- `pack_dxf.py` — Stages B–D. · `config.json` / `parts_raw/hole_roles.csv` — the knobs.
- `output/demo/` — final sheets + BOM. · `input/demo/parts_raw/` — the real extracted parts.
