#!/usr/bin/env python
"""
Beest DXF pipeline — Stages B, C, D.

Input : per-part DXFs exported from Fusion (1:1 mm) + parts_manifest.csv
Output: packed sheet DXFs (scaled + hole-corrected + labelled + nested) + BOM.csv

  B) scale each part to build size + overwrite hole diameters to real hardware sizes
  C) nest all needed copies onto sheets (rectpack); etch each part's name on a LABEL layer
  D) write BOM.csv

Run:  py pack_dxf.py [config.json]

Precision note: geometry is never redrawn — only exact affine transforms are applied, and
hole radii are set to exact hardware values. Labels go on their own layer so the laser/CNC
can SCORE them (not cut).
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
from ezdxf.enums import TextEntityAlignment
from ezdxf.math import Matrix44
from rectpack import newPacker


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_manifest(path):
    rows = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[r["part"].strip()] = {
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


def process_part(infile, outfile, scale, hole_mm):
    doc = ezdxf.readfile(infile)
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    for e in msp:
        e.transform(Matrix44.scale(scale, scale, 1.0))     # scale geometry (hole CENTRES move)
    r = hole_mm / 2.0
    for c in msp.query("CIRCLE"):
        c.dxf.radius = r                                    # reset hole DIAMETER to hardware size
    doc.saveas(outfile)
    _, dims = bbox_of(list(msp))
    return dims


def place_instance(part_file, name, rotated, tx, ty, target_doc, label_h, label_layer):
    src = ezdxf.readfile(part_file)
    ents = list(src.modelspace())
    if rotated:
        for e in ents:
            e.transform(Matrix44.z_rotate(math.pi / 2))
    bb, (w, h) = bbox_of(ents)
    for e in ents:
        e.transform(Matrix44.translate(tx - bb.extmin.x, ty - bb.extmin.y, 0))
    imp = Importer(src, target_doc)
    imp.import_entities(ents, target_doc.modelspace())
    imp.finalize()
    if label_h > 0:
        hh = min(label_h, min(w, h) * 0.5)
        if hh >= 2.0:
            t = target_doc.modelspace().add_text(name, height=hh, dxfattribs={"layer": label_layer})
            t.set_placement((tx + w / 2.0, ty + h / 2.0), align=TextEntityAlignment.MIDDLE_CENTER)


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
    label_h = float(cfg.get("label_height_mm", 0))
    label_layer = cfg.get("label_layer", "LABEL")

    usable_w = sheet_w - 2 * margin
    usable_h = sheet_h - 2 * margin

    print(f"== Stage B: scale x{scale}, correct holes ==")
    part_dims = {}
    for name, info in manifest.items():
        infile = os.path.join(parts_dir, name + ".dxf")
        if not os.path.exists(infile):
            print(f"  !! missing DXF for '{name}' — skipped"); continue
        hole = float(overrides.get(name, default_hole))
        w, h = process_part(infile, os.path.join(proc_dir, name + ".dxf"), scale, hole)
        part_dims[name] = (w, h)
        print(f"  {name:22s} {w:8.1f} x {h:8.1f} mm   holes->{hole:g}mm   x{info['per_kit'] * kits}")

    print(f"== Stage C: nesting onto {sheet_w:.0f}x{sheet_h:.0f} sheets (label='{label_layer}') ==")
    packer = newPacker(rotation=allow_rotate)
    rid = 0
    rid_map = {}
    for name, info in manifest.items():
        if name not in part_dims:
            continue
        w, h = part_dims[name]
        pw, ph = w + spacing, h + spacing
        if not fits(pw, ph, usable_w, usable_h, allow_rotate):
            print(f"  !! '{name}' ({w:.0f}x{h:.0f}) too big for the sheet — reduce scale or split")
            continue
        for _ in range(info["per_kit"] * kits):
            packer.add_rect(pw, ph, rid)
            rid_map[rid] = (name, pw, ph)
            rid += 1

    packer.add_bin(usable_w, usable_h, count=100000)
    packer.pack()
    rects = packer.rect_list()

    by_bin = defaultdict(list)
    for (b, x, y, w, h, r) in rects:
        by_bin[b].append((x, y, w, h, r))

    sheet_files = []
    for b in sorted(by_bin):
        doc = ezdxf.new(); doc.units = ezdxf.units.MM
        if label_h > 0 and label_layer not in doc.layers:
            doc.layers.add(label_layer, color=1)      # red = score/engrave, not cut
        for (x, y, w, h, r) in by_bin[b]:
            name, pw, ph = rid_map[r]
            rotated = (allow_rotate and abs(w - ph) < 0.5 and abs(h - pw) < 0.5
                       and not (abs(w - pw) < 0.5 and abs(h - ph) < 0.5))
            place_instance(os.path.join(proc_dir, name + ".dxf"), name, rotated,
                           margin + x + spacing / 2.0, margin + y + spacing / 2.0,
                           doc, label_h, label_layer)
        out = os.path.join(out_dir, f"sheet_{b + 1:02d}.dxf")
        doc.saveas(out); sheet_files.append(out)
        print(f"  sheet_{b + 1:02d}.dxf : {len(by_bin[b])} parts")

    bom = os.path.join(out_dir, "BOM.csv")
    with open(bom, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["CUT PARTS", "per_kit", "kits", "total", "hole_mm", "notes"])
        for name, info in manifest.items():
            hole = float(overrides.get(name, default_hole))
            w.writerow([name, info["per_kit"], kits, info["per_kit"] * kits, hole,
                        f"{info['thickness']:g}mm(model) ply, scaled x{scale}"])
        w.writerow([])
        w.writerow(["SHEETS", "", "", len(sheet_files), "", f"{sheet_w:.0f}x{sheet_h:.0f}mm"])
        w.writerow([])
        w.writerow(["HARDWARE", "per_kit", "kits", "total", "", ""])
        for item, q in cfg.get("hardware_per_kit", {}).items():
            w.writerow([item, q, kits, q * kits, "", ""])

    print(f"== Stage D: BOM -> {bom} ==")
    print(f"DONE: {len(sheet_files)} sheet(s), {rid} parts placed, labels on '{label_layer}' layer.")


if __name__ == "__main__":
    main()
