# Making it real — strandbeest kit build spec

Everything needed to turn the nested sheets in [`output/demo`](output/demo) into ~10 hand-cranked,
waist-height walking strandbeest kits. Numbers are for **10 kits**; per-kit figures in `BOM.csv`.

---

## 1. The pin joints (this is the core question)

Every leg joint is a **pivot**: links must rotate relative to each other around a shared pin.

**The joint stack (per pivot):**
- **One shared pin** = an **M6 bolt** (or 6 mm rod) through the aligned holes of every link at that pivot.
- **Rotation** = a **flanged bearing/bushing** seated in each rotating link's hole. The link spins on it.
- **The flange** sits against the plywood face and **stops the bearing pushing through**.
- **Retention** = the **bolt head** on one end + an **M6 nyloc nut** on the other = the caps that stop
  the pin sliding out. Snug, not clamped — the bearings must still spin.
- **Spacing** = **nylon washers** between links so faces don't rub.

So: *shared M6 pin · bearings spin · flanges + bolt-head/nyloc retain*. No press-fit needed on the links.

### Bearing vs friction — which hole is which
- **Leg-link holes → bearing/bushing seat** (they rotate). Hole Ø = **13 mm** (F686 outer diameter).
- **Gear centre holes → friction/press fit onto the shaft** (the gear turns *with* the shaft).
  Hole Ø = **8 mm**.
- **Frame-spacer holes → crankshaft ball-bearing seats.** Hole Ø = **22 mm** (608 outer diameter). *(assumed — confirm)*
- **Spacer holes → shaft pass-through.** Hole Ø = **8 mm**. *(assumed — confirm)*

The two `*(assumed)*` rows are my best guess at the drivetrain — tell me the real role and it's a
one-line change in `config.json` → re-run.

### Cost lever (read this)
"A bearing in every link hole" = **~90 per kit → ~900 total**. Two ways to cut that:
- **Nylon flanged bushings** instead of ball bearings (same 13 mm seat): ~€0.10 vs ~€0.40 each → saves
  ~€270 across 10 kits. **Recommended for a hand-cranked workshop build** — plenty smooth, far cheaper/lighter.
- **Friction-fit one link per pivot** (the pin fixed to one link, only the other rotates): **halves** the
  bearing count to ~45/kit. Needs per-hole assignment, so worth doing once the assembly order is set.

---

## 2. Bearings & hardware (real parts)

| Role | Part | Size (bore×OD×W) | Hole seat | Qty (10 kits) | Source |
|---|---|---|---|---|---|
| Leg pivots | **F686ZZ** flanged **or** 6 mm nylon flanged bushing | 6×13×5 | 13 mm | ~900 | Amazon.nl / bearing shop |
| Crankshaft | **608ZZ** (skate bearing) | 8×22×7 | 22 mm | ~60 | Amazon.nl ~€6.5/10 |
| Pivot pins | **M6 bolts** 30–50 mm | — | 13 mm holes | ~450 | GAMMA/Hornbach/Praxis |
| Pin caps | **M6 nyloc nuts** | — | — | ~450 | DIY store |
| Spacing | **M6 nylon washers** | — | — | ~1200 | DIY store |
| Crank axle | **8 mm rod / M8 threaded rod** | — | 8/22 mm | ~10 | DIY store |
| Crank handle | cut plywood part | — | — | 10 | (cut) |

Dutch terms: kogellager (bearing), bout (bolt), zelfborgende moer (nyloc), ring (washer),
draadeind (threaded rod), berken multiplex (birch ply).

---

## 3. Scale & size

- **`scale: 6.0`** in `config.json` gives a **~waist-height** machine (longest link ≈ 431 mm,
  full beest ≈ 0.9–1 m). Bearings fit with huge margin at this scale (they'd fit down to ~×2.5, so
  size — not the bearing — sets the scale here).
- To retarget: **`scale = target_leg_mm / current_leg_mm`**. Give me your desired leg height (or let me
  measure the assembled leg) and I'll set it exactly.
- **Holes do NOT scale** — they're fixed to the hardware (13 / 8 / 22 mm) regardless of `scale`.

---

## 4. Material & cutting

- **9 mm birch multiplex** (berken multiplex), 2440×1220 sheets. (Links model at 3 mm and gears at 5 mm,
  but for a waist-height walker use one honest 9 mm stock throughout; the 2D outlines are thickness-agnostic.)
- **~9 sheets for 10 kits** with the built-in bounding-box nester. Run the processed parts through
  **Deepnest** (true-shape) to drop it to ~6.
- **Labels:** every part is etched with its name on the **`LABEL`** layer — set that layer to
  **score/engrave**, everything else to **cut**. Essential for 30 people sorting parts.
- **Cut a fit-test coupon first** (13 mm holes at nominal ±0.1/0.2 mm) to dial in kerf so bearings
  press in snug on the real machine + material.

---

## 5. Rough budget (10 kits)

| | Ball-bearing pivots | Bushing pivots (recommended) |
|---|---|---|
| Plywood (~9 sheets) | €450–720 | €450–720 |
| Pivot sleeves (~900) | ~€360 | ~€90 |
| Bolts/nyloc/washers | ~€250 | ~€250 |
| 608 + rod + misc | ~€80 | ~€80 |
| **Total** | **~€1140–1410** | **~€870–1140** |

Within a "decent budget", and Deepnest + bushings pulls it toward the low end.

---

## 6. Build flow (2 days, teams of 3)

1. **Pre-cut** all sheets on FabLab Den Haag's CNC router *before* the event (30 people can't share one machine).
2. Day 1: each team assembles legs — press a bushing/bearing in each link hole, stack the links, run the
   M6 pin, washers between, nyloc to snug. Etched labels tell them which link is which.
3. Day 1 (parallel): a lead builds each crankshaft — 608 bearings in the frame plates, gears on the 8 mm
   shaft, crank handle on top.
4. Day 2: mount legs to the crank throws (120° phased), tune friction, hand-crank, walk.
5. **De-risk:** build ONE full kit as a prototype before cutting all ten.

---

## 7. Confirm with me
- Pivot hardware: **ball bearings or nylon bushings?** (drives cost)
- The two `*(assumed)*` hole roles (frame spacer, spacer).
- Final **leg height** → exact `scale`.
- The **crank** part still needs a clean re-export (its holes didn't project — wrong face).
