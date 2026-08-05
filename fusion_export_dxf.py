# Fusion 360 script (Stage A) — export every FLAT (plate-like) component as a DXF (1:1)
# and write parts_manifest.csv. Round/3D parts (rods, pins, bearings, chunky handles) are
# auto-skipped. Each part is sketched on its OWN flat face, so assembly layering / position /
# axis-crossing does NOT matter — every part comes out as a clean 2D outline.
#
# RUN (works in Fusion Personal):
#   1. STRONGLY recommended: File -> Save As -> a COPY (e.g. "beest-export"), run this THERE,
#      so your master can't be touched. (The script also deletes the temp sketches it makes,
#      so it leaves no trace even if run on the master — but a copy is belt-and-suspenders.)
#   2. Set document units to mm (Document Settings) if they aren't already.
#   3. Utilities -> ADD-INS -> Scripts and Add-Ins -> Scripts -> "+" -> point at this file -> Run.
#   4. Check ~/Desktop/beest-pipeline/parts_raw/ : only flat parts + parts_manifest.csv + skipped.csv
#
# Tune FLAT_MAX_THICKNESS_MM if a real flat part is skipped or a chunky part slips through.
import adsk.core
import adsk.fusion
import traceback
import os
import csv

OUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "beest-pipeline", "parts_raw")
FLAT_MAX_THICKNESS_MM = 40.0     # a "flat part" is thinner than this between its two big faces
FLAT_AREA_RATIO = 0.85           # the two big faces must be ~equal area (front/back of a plate)


def safe(name):
    return "".join(ch if (ch.isalnum() or ch in " _-") else "_" for ch in name).strip()


def find_flat_face(comp):
    """Return (largest flat face, thickness_mm) if the component is plate-like, else (None, 0)."""
    planar = []
    for body in comp.bRepBodies:
        for f in body.faces:
            if f.geometry.objectType == adsk.core.Plane.classType():
                planar.append(f)
    if len(planar) < 2:
        return None, 0.0
    planar.sort(key=lambda f: f.area, reverse=True)
    top = planar[0]
    n1 = top.geometry.normal
    o1 = top.geometry.origin
    for f in planar[1:]:
        n2 = f.geometry.normal
        if abs(abs(n1.dotProduct(n2)) - 1.0) < 1e-3 and f.area >= FLAT_AREA_RATIO * top.area:
            v = o1.vectorTo(f.geometry.origin)
            gap_mm = abs(v.dotProduct(n1)) * 10.0     # Fusion API cm -> mm
            if 0.1 < gap_mm < FLAT_MAX_THICKNESS_MM:
                return top, round(gap_mm, 2)
    return None, 0.0


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

        # count occurrences per unique component
        counts = {}

        def walk(occs):
            for occ in occs:
                counts[occ.component.name] = counts.get(occ.component.name, 0) + 1
                walk(occ.childOccurrences)

        walk(root.occurrences)

        exported, skipped = [], []
        for comp in design.allComponents:
            if comp == root and comp.bRepBodies.count == 0:
                continue
            face, thick = find_flat_face(comp)
            if not face:
                if comp.bRepBodies.count > 0:
                    skipped.append((comp.name, "not plate-like (rod/pin/3D part)"))
                continue
            try:
                sk = comp.sketches.add(face)
                sk.project(face)                       # outer boundary + holes
                path = os.path.join(OUT_DIR, safe(comp.name) + ".dxf")
                ok = sk.saveAsDXF(path)
                sk.deleteMe()                          # clean up: leave the design untouched
                if ok:
                    exported.append((comp.name, thick))
                else:
                    skipped.append((comp.name, "saveAsDXF returned false"))
            except Exception as e:
                skipped.append((comp.name, "error: %s" % e))

        exported_names = {n for n, _ in exported}
        with open(os.path.join(OUT_DIR, "parts_manifest.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["part", "per_kit_qty", "thickness_mm"])
            for name, thick in exported:
                w.writerow([safe(name), counts.get(name, 1), thick])
        with open(os.path.join(OUT_DIR, "skipped.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["component", "reason"])
            for name, reason in skipped:
                w.writerow([name, reason])

        ui.messageBox(
            "Exported %d flat parts.\nSkipped %d non-flat components (see skipped.csv).\n\n%s\n\n"
            "Now: check parts_raw/, then run  py pack_dxf.py"
            % (len(exported), len(skipped), OUT_DIR)
        )
    except:  # noqa
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
