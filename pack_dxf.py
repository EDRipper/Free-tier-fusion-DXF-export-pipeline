#!/usr/bin/env python
"""
Beest DXF pipeline — Stages B, C, D.

Input : per-part DXFs exported from Fusion (1:1 mm) + parts_manifest.csv
Output: packed sheet DXFs (scaled + hole-corrected + nested) + BOM.csv

  B) scale each part to build size + overwrite hole diameters to real hardware sizes
  C) nest all needed copies onto sheets (rectpack, true rotation, spacing/margin)
  D) write BOM.csv

Run:  py pack_dxf.py [config.json]

Precision note: geometry is never redrawn — only exact affine transforms (scale,
rotate, translate) are applied, and hole radii are set to exact hardware values.
"""
import csv
import json
import math
import os
import sys
from collections import defaultdict

import ezdxf
from ezdxf import bbox
from ezdxf.addons import Importer
from ezdxf.math import Matrix44
from rectpack import newPacker


# ---------- helpers ----------

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_manifest(path):
    rows = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            name = r["part"].strip()
            rows[name] = {
                "per_kit": int(float(r["per_kit_qty"])),
                "thickness": float(r.get("thickness_mm", 0) or 0),
            }
    return rows


def bbox_of(ents):
    bb = bbox.extents(ents)
    return bb, (bb.extmax.x - bb.extmin.x, bb.extmax.y - bb.extmin.y)


def fits(pw, ph, uw, uh, rot):
    if pw <= uw and ph <= uh:
        return True
    if rot and ph <= uw and pw <= uh:
        return True
    return False


# ---------- Stage B: scale + hole-correct ----------

def process_part(infile, outfile, scale, hole_mm):
    doc = ezdxf.readfile(infile)
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    m = Matrix44.scale(scale, scale, 1.0)
    for e in msp:
        e.transform(m)                       # scale link geometry (hole CENTRES move)
    r = hole_mm / 2.0
    for c in msp.query("CIRCLE"):
        c.dxf.radius = r                     # reset hole DIAMETER to real hardware size
    doc.saveas(outfile)
    _, dims = bbox_of(list(msp))
    return dims


# ---------- Stage C: place one instance onto a sheet ----------

def place_instance(part_file, rotated, tx, ty, target_doc):
    src = ezdxf.readfile(part_file)          # fresh, pristine copy each placement
    ents = list(src.modelspace())
    if rotated:
        for e in ents:
            e.transform(Matrix44.z_rotate(math.pi / 2))
    bb, _ = bbox_of(ents)
    dx, dy = tx - bb.extmin.x, ty - bb.extmin.y
    for e in ents:
        e.transform(Matrix44.translate(dx, dy, 0))
    imp = Importer(src, target_doc)
    imp.import_entities(ents, target_doc.modelspace())
    imp.finalize()


# ---------- main ----------

def main():
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    cfg = load_config(cfg_path)
    base = os.path.dirname(os.path.abspath(cfg_path))

    def P(p):
        return p if os.path.isabs(p) else os.path.join(base, p)

    parts_dir = P(cfg["parts_dir"])
    manifest = read_manifest(P(cfg["manifest"]))
    proc_dir = P(cfg["processed_dir"]); os.makedirs(proc_dir, exist_ok=True)
    out_dir = P(cfg["out_dir"]); os.makedirs(out_dir, exist_ok=True)

    scale = float(cfg["scale"]); kits = int(cfg["kits"])
    sheet_w = float(cfg["sheet_w_mm"]); sheet_h = float(cfg["sheet_h_mm"])
    spacing = float(cfg["part_spacing_mm"]); margin = float(cfg["sheet_margin_mm"])
    default_hole = float(cfg["default_hole_mm"])
    overrides = cfg.get("part_hole_overrides", {})
    allow_rotate = bool(cfg.get("allow_rotate", True))

    usable_w = sheet_w - 2 * margin
    usable_h = sheet_h - 2 * margin

    print(f"== Stage B: scale x{scale}, correct holes ==")
    part_dims = {}
    for name, info in manifest.items():
        infile = os.path.join(parts_dir, name + ".dxf")
        if not os.path.exists(infile):
            print(f"  !! missing DXF for '{name}' ({infile}) — skipped")
            continue
        hole = float(overrides.get(name, default_hole))
        w, h = process_part(infile, os.path.join(proc_dir, name + ".dxf"), scale, hole)
        part_dims[name] = (w, h)
        print(f"  {name:22s} {w:8.1f} x {h:8.1f} mm   holes->{hole:g}mm   x{info['per_kit'] * kits}")

    print(f"== Stage C: nesting onto {sheet_w:.0f}x{sheet_h:.0f} sheets "
          f"(usable {usable_w:.0f}x{usable_h:.0f}, {spacing:g}mm gap) ==")
    packer = newPacker(rotation=allow_rotate)
    rid = 0
    rid_map = {}
    for name, info in manifest.items():
        if name not in part_dims:
            continue
        w, h = part_dims[name]
        pw, ph = w + spacing, h + spacing
        if not fits(pw, ph, usable_w, usable_h, allow_rotate):
            print(f"  !! '{name}' ({w:.0f}x{h:.0f}) too big for the sheet — reduce scale or split it")
            continue
        for _ in range(info["per_kit"] * kits):
            packer.add_rect(pw, ph, rid)
            rid_map[rid] = (name, pw, ph)
            rid += 1

    packer.add_bin(usable_w, usable_h, count=100000)
    packer.pack()
    rects = packer.rect_list()               # (bin, x, y, w, h, rid)

    placed = set(r[5] for r in rects)
    missing = set(rid_map) - placed
    if missing:
        print(f"  !! {len(missing)} parts did not place — check oversize warnings")

    by_bin = defaultdict(list)
    for (b, x, y, w, h, r) in rects:
        by_bin[b].append((x, y, w, h, r))

    sheet_files = []
    for b in sorted(by_bin):
        doc = ezdxf.new(); doc.units = ezdxf.units.MM
        for (x, y, w, h, r) in by_bin[b]:
            name, pw, ph = rid_map[r]
            rotated = (allow_rotate
                       and abs(w - ph) < 0.5 and abs(h - pw) < 0.5
                       and not (abs(w - pw) < 0.5 and abs(h - ph) < 0.5))
            tx = margin + x + spacing / 2.0
            ty = margin + y + spacing / 2.0
            place_instance(os.path.join(proc_dir, name + ".dxf"), rotated, tx, ty, doc)
        out = os.path.join(out_dir, f"sheet_{b + 1:02d}.dxf")
        doc.saveas(out); sheet_files.append(out)
        print(f"  sheet_{b + 1:02d}.dxf : {len(by_bin[b])} parts")

    # ---------- Stage D: BOM ----------
    bom = os.path.join(out_dir, "BOM.csv")
    with open(bom, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["CUT PARTS", "per_kit", "kits", "total", "notes"])
        for name, info in manifest.items():
            w.writerow([name, info["per_kit"], kits, info["per_kit"] * kits,
                        f"{info['thickness']:g}mm ply, scaled x{scale}"])
        w.writerow([])
        w.writerow(["SHEETS", "", "", len(sheet_files), f"{sheet_w:.0f}x{sheet_h:.0f}mm"])
        w.writerow([])
        w.writerow(["HARDWARE", "per_kit", "kits", "total", ""])
        for item, q in cfg.get("hardware_per_kit", {}).items():
            w.writerow([item, q, kits, q * kits, ""])

    print(f"== Stage D: BOM -> {bom} ==")
    print(f"DONE: {len(sheet_files)} sheet(s), {rid} parts placed, BOM written to {out_dir}")


if __name__ == "__main__":
    main()
