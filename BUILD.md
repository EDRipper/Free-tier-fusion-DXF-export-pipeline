# Making it real — strandbeest kit build spec

Everything needed to turn the nested sheets in [`output/demo`](output/demo) into **6 hand-cranked,
waist-height walking strandbeest kits** (6 teams of 5, 2 days). Per-kit figures are in `BOM.csv`.

---

## 1. The pin joints (the core question)

Every leg joint is a **pivot**: links must rotate relative to each other around a shared pin.

**The joint stack (per pivot):**
- **One shared pin** = an **M6 bolt** (or 6 mm rod) through the aligned holes of every link at that pivot.
- **Rotation** = a **flanged ball bearing** seated in each rotating link's hole. The link spins on it.
- **The flange** sits against the plywood face and **stops the bearing pushing through**.
- **Retention** = **bolt head** one end + **M6 nyloc nut** the other = the caps that stop the pin
  sliding out. Snug, not clamped — bearings must still spin freely.
- **Spacing** = **nylon washers** between links so faces don't rub.

*Shared M6 pin · ball bearings spin · flanges + bolt-head/nyloc retain.* No press-fit on the links.

### Why ball bearings, not bushings
~40 pivots per beest, hand-cranked (no motor to muscle through stiction). Bushings are *sliding*
friction (μ≈0.1–0.2, sticky at startup); ball bearings are *rolling* (μ≈0.002) — ~20–100× less drag,
compounded across 40 joints, and worse for bushings at waist-scale loads. Ball bearings it is.

### Bearing vs friction, per hole
- **Leg-link holes → 13 mm** ball-bearing seats (rotate).
- **Gear centres → 8 mm** friction fit onto the shaft (turn with it).
- **Frame-spacer holes → 22 mm** 608 crankshaft-bearing seats. *(assumed — confirm)*
- **Spacer holes → 8 mm** shaft pass-through. *(assumed — confirm)*

### Optional saving (same smoothness)
Fixing one link per pivot to the pin (only its neighbour rotates on a bearing) **halves** the bearing
count to ~45/kit with *identical* rolling friction. Needs per-hole role assignment, so do it once the
assembly order is locked; the simple "bearing in every hole" version below is foolproof for the workshop.

---

## 2. Bearings & hardware (real parts, 6 kits)

| Role | Part | Size (bore×OD×W) | Hole seat | Qty (6 kits) | Source |
|---|---|---|---|---|---|
| Leg pivots | **F686ZZ** flanged ball bearing | 6×13×5 | 13 mm | ~540 | Amazon.nl / bearing shop, bulk |
| Crankshaft | **608ZZ** skate bearing | 8×22×7 | 22 mm | ~36 | Amazon.nl ~€6.5/10 |
| Pivot pins | **M6 bolts** 30–50 mm | — | 13 mm | ~270 | GAMMA/Hornbach/Praxis |
| Pin caps | **M6 nyloc nuts** | — | — | ~270 | DIY store |
| Spacing | **M6 nylon washers** | — | — | ~720 | DIY store |
| Crank axle | **8 mm rod / M8 threaded rod** | — | 8/22 mm | ~6 | DIY store |
| Crank handle | cut plywood part | — | — | 6 | (cut) |

Dutch terms: kogellager (bearing), bout (bolt), zelfborgende moer (nyloc), ring (washer),
draadeind (threaded rod), berken multiplex (birch ply).

---

## 3. Scale & size

- **`scale: 6.0`** → **~waist-height** (longest link ≈ 431 mm, full beest ≈ 0.9–1 m). The 13 mm
  bearing seats fit with big margin (they'd fit down to ~×2.5), so *size* sets the scale here.
- Retarget with **`scale = target_leg_mm / current_leg_mm`** — give me a leg height and I set it exactly.
- **Holes never scale** — fixed to hardware (13 / 8 / 22 mm) at any `scale`.

---

## 4. Material & cutting

- **9 mm birch multiplex** (berken multiplex), 2440×1220 sheets. One honest 9 mm stock throughout
  (2D outlines are thickness-agnostic; the model's 3/5 mm values are informational).
- **6 sheets for 6 kits** with the built-in bounding-box nester; **Deepnest** (true-shape) drops it to ~4.
- **Labels:** every part is etched with its name on the **`LABEL`** layer — set that layer to
  **score/engrave**, everything else to **cut**. Essential for 30 people sorting parts.
- **Cut a fit-test coupon first** (13 mm holes at nominal ±0.1/0.2 mm) to dial in kerf for a snug
  bearing press on the real machine + material.

---

## 5. Rough budget (6 kits, ball bearings)

| item | cost |
|---|---|
| Plywood (~6 sheets) | €300–480 |
| F686 pivot bearings (~540) | ~€216 |
| 608 + rod + misc | ~€65 |
| Bolts / nyloc / washers | ~€150 |
| **Total** | **~€730–910** |

Deepnest (fewer sheets) and the friction-fix optimization (half the bearings) pull it lower.

---

## 6. Build flow (2 days, 6 teams of 5)

1. **Pre-cut** all 6 sheets on FabLab Den Haag's CNC router *before* the event (30 people can't share one machine).
2. Day 1: each team assembles its beest's legs — press a bearing into each link hole, stack the links,
   run the M6 pin, washers between, nyloc to snug. Etched labels tell them which link is which.
3. Day 1 (parallel): build each crankshaft — 608 bearings in the frame plates, gears on the 8 mm shaft,
   crank handle on top.
4. Day 2: mount legs to the crank throws (120° phased), tune, hand-crank, walk.
5. **De-risk:** build ONE full kit as a prototype before cutting all six.

---

## 7. Confirm with me
- The two `*(assumed)*` hole roles (frame spacer, spacer) — their real job in the drivetrain.
- Final **leg height** → exact `scale`.
- The **`crank`** part still needs a clean re-export (its holes were on the wrong face).
