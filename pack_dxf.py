#!/usr/bin/env python
"""
Beest DXF pipeline — Stages B, C, D.

Input : per-part DXFs from Fusion (1:1 mm) + parts_manifest.csv (+ optional hole_roles.csv)
Output: packed sheet DXFs (scaled + hole-corrected + labelled + nested) + BOM.csv

Precision note: geometry is never redrawn — only exact affine transforms are applied, hole radii
are set to exact hardware values. Labels are placed on the widest solid region of each part (not
the bbox centre) and go on their own LABEL layer so the laser can SCORE them.

HOLE SIZES: default_hole_mm applies to every hole UNLESS overridden. Overrides can be per-part
(part_hole_overrides in config) OR per-hole via parts_raw/hole_roles.csv (part,cx,cy,dia in the
ORIGINAL unscaled model coords) — the reliable per-hole source is the Fusion joints, exported by
fusion_export_dxf.py. Without that file, per-part rules are a GUESS.

Run:  py pack_dxf.py [config.json]
"""
import csv
import json
import math
import os
import sys
from collections import defaultdict

import ezdxf
from ezdxf import bbox
from ezdxf import path as ezpath
from ezdxf.addons import Importer
from ezdxf.enums import TextEntityAlignment
from ezdxf.math import Matrix44, Vec3
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


def read_hole_roles(path):
    """Optional per-hole diameters: part,cx,cy,dia (unscaled model coords)."""
    roles = defaultdict(list)
    if not os.path.exists(path):
        return roles
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            roles[r["part"].strip()].append(
                (float(r["cx"]), float(r["cy"]), float(r["dia"])))
    return roles


def bbox_of(ents):
    bb = bbox.extents(ents)
    return bb, (bb.extmax.x - bb.extmin.x, bb.extmax.y - bb.extmin.y)


def fits(pw, ph, uw, uh, rot):
    return (pw <= uw and ph <= uh) or (rot and ph <= uw and pw <= uh)


# ---------- outline hull (wrap the outline around oversized features) ----------

def _convex_hull(points):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _apply_hull(msp, big_r):
    """Replace the outline with the convex hull of the outline + any circle bigger than big_r
    (so an oversized feature like a wide hub is wrapped by the outline instead of poking out).
    Small holes are left as holes; big circles stay as holes inside the new hull."""
    pts = []
    for e in msp:
        t = e.dxftype()
        if t == "LWPOLYLINE":
            pts += [(p[0], p[1]) for p in e.get_points("xy")]
        elif t == "LINE":
            pts += [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
        elif t in ("ARC", "SPLINE"):
            try:
                pts += [(p.x, p.y) for p in ezpath.make_path(e).flattening(1.0)]
            except Exception:
                pass
    for c in msp.query("CIRCLE"):
        if c.dxf.radius > big_r:
            cx, cy, r = c.dxf.center.x, c.dxf.center.y, c.dxf.radius
            pts += [(cx + r * math.cos(2 * math.pi * k / 48),
                     cy + r * math.sin(2 * math.pi * k / 48)) for k in range(48)]
    hull = _convex_hull(pts)
    if len(hull) < 3:
        return
    for e in list(msp):
        if e.dxftype() in ("LWPOLYLINE", "LINE", "ARC", "SPLINE"):
            msp.delete_entity(e)
    msp.add_lwpolyline(hull, close=True)
    # The oversized hub feature is now wrapped by the outline; it was never a real cut.
    # Replace each wrapped circle with a through-hole placeholder (src_dia) at its centre so the
    # normal hole machinery sizes it by its role (e.g. the crankshaft's friction fit).
    for c in list(msp.query("CIRCLE")):
        if c.dxf.radius > big_r:
            cx, cy = c.dxf.center.x, c.dxf.center.y
            msp.delete_entity(c)
            msp.add_circle((cx, cy), big_r / 2.0)


# ---------- hole sizing (per-hole overrides win over per-part) ----------

def process_part(infile, outfile, scale, default_dia, per_hole, src_dia, tol, hull=False):
    doc = ezdxf.readfile(infile)
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    # de-dupe coincident circles (robust hole capture projects top+bottom edge of each hole)
    seen = set()
    for c in list(msp.query("CIRCLE")):
        key = (round(c.dxf.center.x, 2), round(c.dxf.center.y, 2), round(c.dxf.radius, 2))
        if key in seen:
            msp.delete_entity(c)
        else:
            seen.add(key)
    if hull:
        _apply_hull(msp, big_r=src_dia)   # wrap outline around features bigger than a hole
    # snapshot each circle's ORIGINAL centre + radius so we can (a) match per-hole overrides and
    # (b) resize ONLY the through-holes (dia == src_dia), leaving other circles (e.g. the crank's
    # 25mm hole, or any non-hole feature) as scaled outline.
    circles = list(msp.query("CIRCLE"))
    orig = [(c, c.dxf.center.x, c.dxf.center.y, c.dxf.radius) for c in circles]
    for e in msp:
        e.transform(Matrix44.scale(scale, scale, 1.0))
    for c, ox, oy, orad in orig:
        if abs(orad * 2.0 - src_dia) > tol:
            continue                                   # not a through-hole -> leave as scaled
        dia = default_dia
        for (hx, hy, hd) in per_hole:
            if abs(hx - ox) < 0.3 and abs(hy - oy) < 0.3:
                dia = hd
                break
        c.dxf.radius = dia / 2.0
    doc.saveas(outfile)
    _, dims = bbox_of(list(msp))
    return dims


# ---------- label placement: widest solid region, not bbox centre ----------

def _segments(msp):
    segs = []
    for e in msp:
        if e.dxftype() == "CIRCLE":
            continue
        try:
            pts = list(ezpath.make_path(e).flattening(2.0))
        except Exception:
            continue
        for a, b in zip(pts, pts[1:]):
            segs.append((a.x, a.y, b.x, b.y))
    return segs


def _inside(px, py, segs):
    c = False
    for (x1, y1, x2, y2) in segs:
        if (y1 > py) != (y2 > py):
            xint = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if px < xint:
                c = not c
    return c


def _clearance(px, py, segs, holes):
    best = 1e9
    for (x1, y1, x2, y2) in segs:
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        if L2 == 0:
            d = math.hypot(px - x1, py - y1)
        else:
            t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
            d = math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))
        best = min(best, d)
    for (hx, hy, r) in holes:
        best = min(best, abs(math.hypot(px - hx, py - hy) - r))
    return best


def _box_fits(cx, cy, w, h, ang, segs, holes):
    """True if an oriented rectangle (already margin-inflated) is fully inside the material and
    clear of every hole — sampled on a grid over the box, so text can't cross a cut or a hole."""
    ca, sa = math.cos(ang), math.sin(ang)
    hw, hh = w / 2.0, h / 2.0
    for u in (-hw, -hw * 0.66, -hw * 0.33, 0.0, hw * 0.33, hw * 0.66, hw):
        for v in (-hh, 0.0, hh):
            px = cx + u * ca - v * sa
            py = cy + u * sa + v * ca
            if not _inside(px, py, segs):
                return False
            for (hx, hy, r) in holes:
                if math.hypot(px - hx, py - hy) < r:
                    return False
    return True


def _anchors(bb, segs, holes, n=16):
    """Interior sample points, best-clearance first."""
    pts = []
    for i in range(1, n):
        px = bb.extmin.x + (bb.extmax.x - bb.extmin.x) * i / n
        for j in range(1, n):
            py = bb.extmin.y + (bb.extmax.y - bb.extmin.y) * j / n
            if not _inside(px, py, segs):
                continue
            if any(math.hypot(px - hx, py - hy) < r for hx, hy, r in holes):
                continue
            pts.append((_clearance(px, py, segs, holes), px, py))
    pts.sort(reverse=True)
    return pts


def _fits_h(ax, ay, name, h, arad, segs, holes, aspect, margin_frac):
    m = h * margin_frac
    return _box_fits(ax, ay, len(name) * h * aspect + 2 * m, h + 2 * m, arad, segs, holes)


def compute_label(processed_file, name, max_h, min_h=3.0, aspect=0.68, margin_frac=0.35):
    """Return (x, y, height, angle_deg) for a label whose whole bounding box FITS on the part
    (no overlap with any cut line or hole). Runs text along the long axis; binary-searches the
    largest fitting height at the best-clearance anchors. None if nothing fits."""
    doc = ezdxf.readfile(processed_file)
    msp = doc.modelspace()
    bb = bbox.extents(msp)
    segs = _segments(msp)
    holes = [(c.dxf.center.x, c.dxf.center.y, c.dxf.radius) for c in msp.query("CIRCLE")]
    prim = 0.0 if (bb.extmax.x - bb.extmin.x) >= (bb.extmax.y - bb.extmin.y) else 90.0
    anchors = _anchors(bb, segs, holes)
    if not anchors:
        return None
    for (_clr, ax, ay) in anchors[:12]:
        for ang in (prim, (prim + 90.0) % 180.0):
            arad = math.radians(ang)
            if not _fits_h(ax, ay, name, min_h, arad, segs, holes, aspect, margin_frac):
                continue                                   # can't even fit the smallest here
            lo, hi, best = min_h, max_h, min_h            # binary-search the tallest that fits
            for _ in range(6):
                mid = (lo + hi) / 2.0
                if _fits_h(ax, ay, name, mid, arad, segs, holes, aspect, margin_frac):
                    best, lo = mid, mid
                else:
                    hi = mid
            return ax, ay, best, ang
    return None


def place_instance(part_file, name, rotated, tx, ty, target_doc, label, label_layer):
    src = ezdxf.readfile(part_file)
    ents = list(src.modelspace())
    rot = Matrix44.z_rotate(math.pi / 2) if rotated else None
    if rot:
        for e in ents:
            e.transform(rot)
    bb, (w, h) = bbox_of(ents)
    dx, dy = tx - bb.extmin.x, ty - bb.extmin.y
    for e in ents:
        e.transform(Matrix44.translate(dx, dy, 0))
    imp = Importer(src, target_doc)
    imp.import_entities(ents, target_doc.modelspace())
    imp.finalize()
    if not label:
        return
    lx, ly, lh, langle = label
    if rot:
        v = rot.transform(Vec3(lx, ly, 0))
        lx, ly = v.x, v.y
        langle = (langle + 90.0) % 180.0
    lx, ly = lx + dx, ly + dy
    t = target_doc.modelspace().add_text(
        name, height=lh, dxfattribs={"layer": label_layer, "rotation": langle})
    t.set_placement((lx, ly), align=TextEntityAlignment.MIDDLE_CENTER)


def main():
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    cfg = load_config(cfg_path)
    base = os.path.dirname(os.path.abspath(cfg_path))

    def P(p):
        return p if os.path.isabs(p) else os.path.join(base, p)

    parts_dir = P(cfg["parts_dir"])
    manifest = read_manifest(P(cfg["manifest"]))
    for pname, q in cfg.get("qty_override", {}).items():   # e.g. a spare crank -> 2 per kit
        if pname in manifest:
            manifest[pname]["per_kit"] = int(q)
    hull_parts = set(cfg.get("hull_parts", []))
    hole_roles = read_hole_roles(os.path.join(parts_dir, "hole_roles.csv"))
    proc_dir = P(cfg["processed_dir"]); os.makedirs(proc_dir, exist_ok=True)
    out_dir = P(cfg["out_dir"]); os.makedirs(out_dir, exist_ok=True)

    scale = float(cfg["scale"]); kits = int(cfg["kits"])
    sheet_w = float(cfg["sheet_w_mm"]); sheet_h = float(cfg["sheet_h_mm"])
    spacing = float(cfg["part_spacing_mm"]); margin = float(cfg["sheet_margin_mm"])
    default_hole = float(cfg["default_hole_mm"])
    overrides = cfg.get("part_hole_overrides", {})
    rename = cfg.get("rename", {})
    src_dia = float(cfg.get("hole_source_dia_mm", 4.0))
    src_tol = float(cfg.get("hole_source_tol_mm", 0.6))
    allow_rotate = bool(cfg.get("allow_rotate", True))
    label_cap = float(cfg.get("label_height_mm", 0))
    label_layer = cfg.get("label_layer", "LABEL")

    usable_w = sheet_w - 2 * margin
    usable_h = sheet_h - 2 * margin
    have_roles = bool(hole_roles)
    print(f"== Stage B: scale x{scale}; hole roles source: "
          f"{'hole_roles.csv (from joints)' if have_roles else 'per-part GUESS (no hole_roles.csv)'} ==")

    part_dims, part_label = {}, {}
    for name, info in manifest.items():
        infile = os.path.join(parts_dir, name + ".dxf")
        if not os.path.exists(infile):
            print(f"  !! missing DXF for '{name}' — skipped"); continue
        default_dia = float(overrides.get(name, default_hole))
        # per-hole centres are matched in original (pre-scale) model coords inside process_part
        per_hole = hole_roles.get(name, [])
        outfile = os.path.join(proc_dir, name + ".dxf")
        w, h = process_part(infile, outfile, scale, default_dia, per_hole, src_dia, src_tol,
                            hull=(name in hull_parts))
        part_dims[name] = (w, h)
        lbl = compute_label(outfile, rename.get(name, name), label_cap) if label_cap > 0 else None
        part_label[name] = lbl
        tag = "per-hole" if name in hole_roles else f"all={default_dia:g}mm"
        lt = f"label {lbl[2]:.0f}mm@{lbl[3]:.0f}deg" if lbl else "NO LABEL FITS"
        print(f"  {name:22s} {w:8.1f} x {h:8.1f} mm   holes:{tag}   {lt}   x{info['per_kit'] * kits}")

    print(f"== Stage C: nesting onto {sheet_w:.0f}x{sheet_h:.0f} sheets ==")
    packer = newPacker(rotation=allow_rotate)
    rid = 0
    rid_map = {}
    for name, info in manifest.items():
        if name not in part_dims:
            continue
        w, h = part_dims[name]
        pw, ph = w + spacing, h + spacing
        if not fits(pw, ph, usable_w, usable_h, allow_rotate):
            print(f"  !! '{name}' too big for the sheet — reduce scale or split"); continue
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
        if label_cap > 0 and label_layer not in doc.layers:
            doc.layers.add(label_layer, color=1)
        for (x, y, w, h, r) in by_bin[b]:
            name, pw, ph = rid_map[r]
            rotated = (allow_rotate and abs(w - ph) < 0.5 and abs(h - pw) < 0.5
                       and not (abs(w - pw) < 0.5 and abs(h - ph) < 0.5))
            place_instance(os.path.join(proc_dir, name + ".dxf"), rename.get(name, name), rotated,
                           margin + x + spacing / 2.0, margin + y + spacing / 2.0,
                           doc, part_label[name], label_layer)
        out = os.path.join(out_dir, f"sheet_{b + 1:02d}.dxf")
        doc.saveas(out); sheet_files.append(out)
        print(f"  sheet_{b + 1:02d}.dxf : {len(by_bin[b])} parts")

    bom = os.path.join(out_dir, "BOM.csv")
    with open(bom, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["CUT PARTS", "per_kit", "kits", "total", "hole_mm", "notes"])
        for name, info in manifest.items():
            hd = "per-hole" if name in hole_roles else f"{float(overrides.get(name, default_hole)):g}"
            w.writerow([rename.get(name, name), info["per_kit"], kits, info["per_kit"] * kits, hd,
                        f"{info['thickness']:g}mm(model), x{scale}"])
        w.writerow([])
        w.writerow(["SHEETS", "", "", len(sheet_files), "", f"{sheet_w:.0f}x{sheet_h:.0f}mm"])
        w.writerow([])
        w.writerow(["HARDWARE", "per_kit", "kits", "total", "", ""])
        for item, q in cfg.get("hardware_per_kit", {}).items():
            w.writerow([item, q, kits, q * kits, "", ""])

    print(f"== Stage D: BOM -> {bom} ==")
    print(f"DONE: {len(sheet_files)} sheet(s), {rid} parts, "
          f"hole roles from {'JOINTS' if have_roles else 'GUESS'}.")


if __name__ == "__main__":
    main()
