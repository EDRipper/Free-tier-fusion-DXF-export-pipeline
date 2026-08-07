# Build Risk Review — before cutting 6 workshop kits

A pre-flight review done before committing plywood + hardware to a 30-person, 2-day workshop.
Ordered by severity. Numbers come from an audit of the actual cut files (`parts_processed/`,
`nested*/`) plus external research (sources at the bottom).

**Golden rule:** cut a fit-test coupon and one full prototype kit, assemble it, and confirm it
walks — *before* cutting the other five. Every item below is far cheaper to fix at coupon stage.

---

## 🔴 High severity — fix before cutting

### R1. Sheet size doesn't match Snijlab's material/bed
- **Evidence:** we nest onto **2440 × 1220 mm**. Snijlab's birch plywood comes on **1200 × 1200 mm**
  sheets; their standard laser bed is **1200 × 600**, large-format up to **2400 × 1200**. Our sheet
  is bigger than *all* of those (even 40 mm over the large-format bed).
- **Why it bites:** the current nesting is un-cuttable at Snijlab as-is; parts near the sheet edge
  fall outside their material.
- **Fix:** re-nest to Snijlab's real stock — **1200 × 1200 mm** (safe, guaranteed in 9 mm birch).
  The longest part is only 510 mm, so it nests fine; you just get more, smaller sheets. One-line
  config change (`sheet_w_mm`/`sheet_h_mm`) + re-run. *(Alternatively confirm 9 mm birch is offered
  on the 2400 × 1200 large-format service and nest to ≤2380 × 1180.)*

### R2. Cut/engrave colours + file format don't match Snijlab's spec
- **Evidence:** our DXFs use layer `0` = cut in **black** and `LABEL` = **red** text. Snijlab reads
  **cut = blue RGB(0,0,255)**, **line-engrave = red RGB(255,0,0)**, plane-engrave = magenta, in
  **RGB** mode; grey is ignored. It also wants **DXF 2004**, **mm, 1:1**, and **text converted to
  outlines**.
- **Why it bites:** our black cut lines may be read as "ignore," and TEXT labels may not import.
  Our red labels happen to match their line-engrave red — but cut is the problem.
- **Fix (pipeline):** remap cut geometry → blue `cut` layer RGB(0,0,255); labels → red
  `line engraving` layer RGB(255,0,0); **convert label text to outline paths**; save as DXF R2004.
  All doable in `pack_dxf.py`. Then confirm against Snijlab's upload preview (it shows exactly what
  will be produced).

### R3. Kerf is not compensated — every fit is affected
- **Evidence:** no kerf offset in `config.json`/`pack_dxf.py`; holes drawn at nominal.
- **Why it bites:** the laser removes ~0.15–0.2 mm and interior holes cut ~one kerf **oversize** →
  8 mm friction holes cut ~8.2 mm (won't grip the rod), 22 mm bearing seats cut ~22.2 mm (608 drops
  in loose).
- **Fix:** shrink hole diameters ~one kerf (draw ~7.8–8.0 mm for the rod fit, ~21.8–22.0 mm for the
  bearing seat), then **verify with a fit-test ladder** on Snijlab's machine + the actual ply batch
  (seats at 21.9/22.0/22.1/22.2; friction at 7.8/7.9/8.0/8.1). Measure real ply thickness first —
  "9 mm" birch is often 8.5–9.2 mm.

### R4. 606 bearings (101/kit) — over-engineered, costly, hard to retain
- **Evidence (audit):** every leg-link hole is a 22 mm 608 seat → **101/kit × 6 = 606 bearings**
  (~€230–300), plus 20 friction holes/kit.
- **Why it bites:** a 22 mm press-fit in 9 mm ply has little grip and **plywood creeps → bearings
  work loose/fall out**; the 7 mm bearing is narrower than the 9 mm ply (walks axially); adjacent
  outer races in a stacked pivot can rub; and pressing 600+ bearings with beginners in 2 days is a
  huge time sink.
- **Fix — pick one:**
  1. **Bearings only where they earn it** (recommended, = original plan): crankshaft (+ optional
     gear shafts) only; leg pivots become **M8 bolt + PTFE/nylon washer + nyloc**. ~101 → ~4–8
     bearings/kit. Hand-crank speeds don't need a bearing at every pivot.
  2. **Keep them but retain properly:** epoxy/retaining compound in each seat and/or **laminate two
     ply layers** for a deeper shouldered bore (also fixes R6).

### R5. No prototype and no fit coupon cut yet
- **Fix — sequence:** (1) fit-test coupon → set kerf; (2) cut **one full kit**; (3) assemble &
  hand-crank to confirm it walks; (4) only then cut the other 5.

---

## 🟠 Medium severity

### R6. Slender single-layer links rack out of plane
- **Evidence (audit):** longest links L/W ≈ 6.6 (LinkE 395×60, LinkJ 360×60, LinkF 284×48) in single
  9 mm ply. Walls around holes are healthy (≥13 mm) — the issue is sideways floppiness, not snapping.
- **Why it bites:** deflection ∝ length³; single flat bars flex out of the kinematic plane, the foot
  leaves its plane, stride shrinks, it wobbles. Joint slop (~0.1 mm/joint) also sums to several mm at
  the foot across an 8-bar leg.
- **Fix:** **double-up (laminate) the long links** with internal spacers, and box/triangulate the
  central frame — standard practice at ~1 m. Doubling also deepens the bearing bores (R4 option 2).

### R7. Friction & hand-crank effort
- **Why it bites:** a 6-leg, ~130-pivot machine is **friction-dominated**; torque accumulates and can
  make it hard to crank.
- **Fix:** PTFE/thrust washers between moving faces, smooth shoulder-bolt or bushed pivots, nylocs
  snug-not-tight, and a generous crank-handle radius. The existing gear reduction helps — keep it.

### R8. Verify in the Fusion assembly (not visible from flat parts)
- **Gear mesh centre distance:** the two gear shafts must sit at the correct pitch spacing or teeth
  won't mesh (tooth ratio ~3:4 is fine; confirm the shaft-hole spacing).
- **"Component19 / Links h,i,g":** one 454×222 mm plate with only **2 holes** — if that name means
  three separate links merged into one Fusion component, cutting it as a single plate is wrong.
  Confirm it's genuinely one physical part.

### R9. Crankshaft — single 8 mm rod driving 6 legs
- **Why it bites:** wind-up/deflection across the width robs motion from far legs.
- **Fix:** bearing-support the crankshaft at every rack (frame spacers); keep spans short; step up
  rod diameter if whippy on the prototype.

---

## 🟡 Lower severity / logistics

### R10. Feet slip on smooth floors
- Strandbeests walk in place on smooth surfaces — the pointed feet need grip. **Add rubber foot
  caps / textured tips** for a hard workshop floor.

### R11. Phasing errors bind or limp
- Legs are clocked on the crankshaft (racks phased 120°). Verify each rack's crank throw is set to
  the intended offset **before final tightening** — if it hops/rocks, check phasing first.

### R12. Weight & tipping
- ~13 kg/kit raw part area (bbox upper bound; real ~8–9 kg cut); ~98 kg ply across 6 sheets (fewer
  per sheet once re-nested to 1200×1200). Ensure a stable stance; it's a heavy machine.

### R13. Assembly guide for beginners
- 6 legs × 8 links × several pivots is a lot of steps. Engraved labels help; add a printed manual,
  alignment jigs, and pre-bagged hardware per team.

---

## Snijlab specifics (confirmed from their design-rules pages)
- **Formats:** DWG, DXF, AI, PDF. Draw 1:1, **mm**. Export **DXF/DWG 2004 "natural."** Convert text
  & fills to outlines; strip dimensions/frames/centrelines.
- **Cut vs engrave (RGB):** cut-through = **blue 0,0,255**; line-engrave = **red 255,0,0**;
  plane-engrave = **magenta 255,0,255** (closed paths). RGB mode only (CMYK misreads). Grey = ignored.
  Line thickness ~0.2 mm. Upload preview shows the final result.
- **Sizes:** standard bed 1200×600; large-format up to 2400×1200.
- **9 mm birch ("berken multiplex"):** stocked & cut, B/B FSC; birch sheet **1200×1200 mm**; from ~€15.
- **Pricing:** instant automated quote from the drawing (cut length/area/part count) × qty × material
  × delivery speed — not flat per-sheet. Get the live quote.
- **Lead time:** you choose it; Express = order before 12:00, next-day.

---

## Sources
- Kerf-aware hole sizing (IDeATe/CMU) — https://courses.ideate.cmu.edu/16-375/f2025/text/mechanism/bearing-demos.html
- Plywood kerf — https://www.1laser.com/blogs/topic/laser-cutting-plywood · https://cutlasercut.com/drawing-resources/expert-tips/laser-kerf/
- Wall/edge margins — https://sendcutsend.com/blog/basic-tolerances-and-cut-feature-relationships/
- Press-fit retention in wood (epoxy/Loctite) — https://www.homemodelenginemachinist.com/threads/what-size-hole-for-press-fit.828/
- Strandbeest build problems (slop, doubled links, friction, feet) — https://makezine.com/article/drones-vehicles/6-common-problems-to-avoid-when-building-a-strandbeest/
- DIY Walkers / Burns build (phasing, feet) — https://www.diywalkers.com/strandbeest.html
- Plywood strandbeest build reference — https://www.nablu.com/2020/05/building-strandbeest.html
- Snijlab design rules — https://snijlab.nl/en/pages/drawing-rules · birch ply — https://snijlab.nl/en/products/birch-plywood
