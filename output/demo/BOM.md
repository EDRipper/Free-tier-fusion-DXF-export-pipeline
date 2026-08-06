# Bill of Materials — 6 strandbeest kits

Generated from the pipeline (`config.json`: scale 6.0, 6 kits, 2440×1220 sheets). Prices are rough
EUR estimates; quantities are per-kit × 6. Links are Amazon.nl searches (NL) — pick the cheapest
listing with the right size; bearing specialists (e.g. kogellagershop.nl) are often cheaper in bulk.

## Cut parts
13 unique parts, nested onto **6 sheets** of **9 mm birch plywood** (berken multiplex, 2440×1220).
DXFs: `sheet_01.dxf … sheet_06.dxf`. Labels are on the `LABEL` layer — set it to **score/engrave**,
everything else to **cut**.

| Item | Qty | Source |
|---|---|---|
| 9 mm birch plywood, 2440×1220 sheet | 6 | [Snijlab (supplies + laser-cuts)](https://snijlab.nl/en/collections/laser-cutting-of-plywood-and-plywood) · [GAMMA berken multiplex](https://www.gamma.nl/assortiment/zoeken?text=berken%20multiplex) |

## Hardware

| Item | Size | Per kit | ×6 | ~€ total | Buy |
|---|---|---|---|---|---|
| **F686ZZ** flanged bearing — leg pivots | 6×13×5 mm | 90 | **540** | ~€200 | [amazon.nl](https://www.amazon.nl/s?k=F686ZZ+bearing) |
| **6001ZZ** bearing — crankshaft supports | 12×28×8 mm | 4 | **24** | ~€40 | [amazon.nl](https://www.amazon.nl/s?k=6001ZZ+lager) |
| **M6 bolts** — pivot pins | 30–50 mm | 45 | **270** | ~€30 | [amazon.nl](https://www.amazon.nl/s?k=M6+bout+RVS) |
| **M6 nyloc** nuts | M6 | 45 | **270** | ~€15 | [amazon.nl](https://www.amazon.nl/s?k=M6+zelfborgende+moer) |
| **M6 nylon washers/spacers** | M6 | 120 | **720** | ~€25 | [amazon.nl](https://www.amazon.nl/s?k=M6+nylon+ring) |
| **12 mm steel rod** — crankshaft | ⌀12 mm | 1 | **6** | ~€30 | [amazon.nl](https://www.amazon.nl/s?k=stalen+staf+12mm) |
| **6 mm steel rod** — crank pins + fixed shafts | ⌀6 mm | 5 | **30** | ~€30 | [amazon.nl](https://www.amazon.nl/s?k=stalen+staf+6mm) |
| Crank handle | (cut part) | 1 | 6 | — | in the cut sheets |

**Hardware subtotal ≈ €370.** Plywood/cutting ≈ €300–480 (DIY sheets) or more via Snijlab's cut service.
**Rough total: €700–900 for all 6 kits.**

> Cost lever: 540× F686 is "a bearing in every pivot hole." Friction-fitting one link per pivot
> halves it to ~270 (same rolling smoothness) — worth doing once the assembly order is fixed.

## ⚠ Assumptions to confirm (each a 1-line edit in `hole_roles.csv`)
- **Crank's small hole** set to 13 mm (bearing) — its real role is unconfirmed.
- **Driving-gear centre** set to 12 mm (assumes pinion shaft = crankshaft dia). Adjust if the input
  shaft is thinner.
- **Spacer bearing hole** set to 13 mm (F686). If that spacer actually carries the 12 mm crankshaft,
  it should be 28 mm.

## The bearing/rod system
- Leg pivots: **M6 bolt through F686 bearings**, one per rotating link hole (13 mm seat), nyloc-capped, nylon washers between.
- Crankshaft: **12 mm rod in 6001 bearings** (28 mm seats in the frame spacers).
- Friction holes (fixed shafts, gear bores, crank pins): sized to the rod (6 mm / 12 mm) for a press fit.
