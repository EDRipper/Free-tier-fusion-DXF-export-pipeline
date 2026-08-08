# Bill of Materials — 6 strandbeest kits

Uniform **8 mm** hardware system: **two hole sizes only** — 22 mm (608 bearing seat) and 8 mm
(M8 rod / friction). Prices are rough EUR estimates; per-kit × 6. Links are Amazon.nl searches (NL).

## Cut parts
13 unique parts, nested onto **13 sheets** of **9 mm birch plywood** (berken multiplex,
**1200×1200 mm** — Snijlab's birch stock size). DXFs: `sheet_01.dxf … sheet_13.dxf`, already
Snijlab-ready: **cut = blue** (layer `cut`, RGB 0,0,255), **engrave = red** (layer `line engraving`,
RGB 255,0,0), text converted to outlines, DXF R2004, mm. One whole beest spans ~3 sheets:
`../nested_1kit/`.

| Item | Qty | Source |
|---|---|---|
| 9 mm birch plywood, 1200×1200 sheet | 13 | [Snijlab birch ply (supplies + laser-cuts)](https://snijlab.nl/en/products/birch-plywood) · [GAMMA berken multiplex](https://www.gamma.nl/assortiment/zoeken?text=berken%20multiplex) |

## Hardware

Bearings are used **only on the crankshaft** (where continuous rotation earns them). Leg pivots are
plain **M8 bolt + nylon washers** running in 9 mm clearance holes — the friction math shows this is
easily hand-crankable (~0.4 kgf at the crank), and it avoids the "bearing works loose in plywood"
problem. This drops bearings from 606 to **30** — see `../BUILD_RISKS.md` (R4).

| Item | Size | Per kit | ×6 | ~€ total | Buy |
|---|---|---|---|---|---|
| **608ZZ** bearing — crankshaft supports only | 8×22×7 mm | 5 | **30** | ~€14 | [amazon.nl](https://www.amazon.nl/s?k=608zz+lager) |
| **M8 bolts** — leg pivot pins (links pivot on the shank) | 30–50 mm | 45 | **270** | ~€55 | [amazon.nl](https://www.amazon.nl/s?k=M8+bout+RVS) |
| **M8 nyloc** nuts | M8 | 45 | **270** | ~€22 | [amazon.nl](https://www.amazon.nl/s?k=M8+zelfborgende+moer) |
| **M8 nylon washers** — between every pivoting face | M8 | 120 | **720** | ~€22 | [amazon.nl](https://www.amazon.nl/s?k=M8+nylon+ring) |
| **8 mm steel rod** — crankshaft, crank pins, fixed shafts, handle | ⌀8 mm | 8 | **48** | ~€30 | [amazon.nl](https://www.amazon.nl/s?k=stalen+staf+8mm) |
| Crank handle | (cut part) | 1 | 6 | — | in the cut sheets |

**Hardware subtotal ≈ €145** (was ~€360 — dropping the leg-pivot bearings saves ~€215). Plywood/
cutting ≈ €300–480 (now 13× 1200×1200 sheets). **Rough total: €450–650 for all 6 kits.**

> Anti-bind tip: so beginners can't crush a pivot by over-tightening the nyloc, add a short M8 nylon
> spacer/bushing (or a shoulder bolt) sized to the link-stack length inside each pivot — the nut then
> bottoms out and the links stay free. Nylon washers between faces cut friction further.

## Hole roles — three sizes
- **22 mm** (608 bearing seat, ×30 total): crankshaft supports only — frame-spacer crankshaft hole,
  spacer bearing hole.
- **9 mm** (M8 pivot clearance): every leg-link pivot hole — links rotate freely on the bolt shank.
- **8 mm** (M8 rod, friction/press): frame-spacer fixed-shaft holes · spacer friction hole · gear
  centres · driven-gear crank pin · crank handle · crank crankshaft mount.

## The system
- **Crankshaft:** 8 mm rod in 608 bearings (22 mm seats), supported at each frame rack.
- **Leg pivots:** M8 bolt through 9 mm clearance holes, nyloc-capped, nylon washers between faces —
  no bearings, hand-crankable, nothing to work loose.
- **Friction holes** (fixed shafts, gear bores, crank pins/mount, handle): 8 mm, press-fit on the rod.

_Hole sizes are drawn kerf-compensated (−0.2 mm); confirm the exact fit with a coupon before the full cut._
