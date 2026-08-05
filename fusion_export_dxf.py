# Fusion 360 script (Stage A) — export each unique component's flat face as a DXF (1:1 mm)
# and write parts_manifest.csv (part name, per-kit instance count, thickness).
#
# HOW TO RUN (works in Fusion Personal):
#   1. Open the beest design.
#   2. Utilities tab -> ADD-INS -> Scripts and Add-Ins -> Scripts -> the "+" -> point at this file.
#   3. Select it -> Run. It writes into ~/Desktop/beest-pipeline/parts_raw/.
#   4. Then run  py pack_dxf.py  from the beest-pipeline folder.
#
# NOTE: this is the one stage I could not test outside Fusion. It follows the standard
# API pattern (largest planar face -> sketch -> project -> saveAsDXF). If a part fails,
# it's usually because the component has no single flat face (fix: pick the face manually).
import adsk.core
import adsk.fusion
import traceback
import os
import csv

OUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "beest-pipeline", "parts_raw")


def safe(name):
    return "".join(ch if (ch.isalnum() or ch in " _-") else "_" for ch in name).strip()


def largest_planar_face(comp):
    best, best_area = None, 0.0
    for body in comp.bRepBodies:
        for f in body.faces:
            if f.geometry.objectType == adsk.core.Plane.classType() and f.area > best_area:
                best, best_area = f, f.area
    return best


def thickness_mm(comp):
    for body in comp.bRepBodies:
        bb = body.boundingBox
        dims = (bb.maxPoint.x - bb.minPoint.x,
                bb.maxPoint.y - bb.minPoint.y,
                bb.maxPoint.z - bb.minPoint.z)
        return round(min(dims) * 10.0, 2)   # Fusion API is cm -> mm
    return 0.0


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox("Open the beest design first.")
            return
        os.makedirs(OUT_DIR, exist_ok=True)
        root = design.rootComponent

        # count instances per unique component
        counts = {}

        def walk(occs):
            for occ in occs:
                counts[occ.component.name] = counts.get(occ.component.name, 0) + 1
                walk(occ.childOccurrences)

        walk(root.occurrences)

        exported = []
        for comp in design.allComponents:
            face = largest_planar_face(comp)
            if not face:
                continue
            sk = comp.sketches.add(face)
            sk.project(face)                       # outer boundary + holes -> sketch curves
            path = os.path.join(OUT_DIR, safe(comp.name) + ".dxf")
            sk.saveAsDXF(path)
            exported.append(comp.name)

        with open(os.path.join(OUT_DIR, "parts_manifest.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["part", "per_kit_qty", "thickness_mm"])
            for comp in design.allComponents:
                if comp.name in exported:
                    w.writerow([safe(comp.name), counts.get(comp.name, 1), thickness_mm(comp)])

        ui.messageBox("Exported %d parts to:\n%s\n\nNow run  py pack_dxf.py" % (len(exported), OUT_DIR))
    except:  # noqa
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
