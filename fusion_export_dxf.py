# Fusion 360 script (Stage A) — export every FLAT (plate-like) component as a DXF (1:1)
# and write parts_manifest.csv. Round/3D parts (rods, pins, bearings, chunky handles) are
# auto-skipped. Each part is sketched on its OWN flat face, so assembly layering / position /
# axis-crossing does NOT matter — every part comes out as a clean 2D outline.
#
# RUN (works in Fusion Personal):
#   1. STRONGLY recommended: File -> Save As -> a COPY (e.g. "beest-export"), run this THERE.
#      (The script also deletes the temp sketches it makes, so it leaves no trace either way.)
#   2. Set document units to mm (Document Settings) if they aren't already.
#   3. Utilities -> ADD-INS -> Scripts and Add-Ins -> Scripts -> "+" -> point at the folder
#      containing this file -> Run.  (Fusion only lists a script if its .py sits in a folder of
#      the SAME name.)
#   4. Check <Desktop>/beest-pipeline/parts_raw/ : flat parts + parts_manifest.csv + skipped.csv
#
# Tune FLAT_MAX_THICKNESS_MM / FLAT_WIDTH_RATIO if a real flat part is skipped or a chunky/round
# part slips through. Note: a part whose holes are NOT on its largest face (rare) may export
# without holes — check skipped.csv and the DXFs, and export such parts manually if needed.
import adsk.core
import adsk.fusion
import traceback
import os
import csv


# ---- resolve output dir, accounting for OneDrive-redirected Desktop ----
def _desktop():
    onedrive = os.environ.get("OneDrive") or os.environ.get("OneDriveConsumer")
    candidates = []
    if onedrive:
        candidates.append(os.path.join(onedrive, "Desktop"))
    home = os.path.expanduser("~")
    candidates.append(os.path.join(home, "OneDrive", "Desktop"))
    candidates.append(os.path.join(home, "Desktop"))
    # prefer a Desktop that already contains beest-pipeline, else first that exists
    for c in candidates:
        if os.path.isdir(os.path.join(c, "beest-pipeline")):
            return c
    for c in candidates:
        if os.path.isdir(c):
            return c
    return candidates[-1]


OUT_DIR = os.path.join(_desktop(), "beest-pipeline", "parts_raw")
FLAT_MAX_THICKNESS_MM = 40.0     # a flat part is thinner than this between its two big faces
FLAT_AREA_RATIO = 0.85           # the two big faces must be ~equal area (front/back of a plate)
FLAT_WIDTH_RATIO = 3.0           # face must be broad vs thickness: area_mm2 > ratio * gap_mm^2
                                 # (this is what rejects round pins/dowels seen end-on)


def safe(name):
    return "".join(ch if (ch.isalnum() or ch in " _-") else "_" for ch in name).strip()


def find_flat_face(comp):
    """Return (largest flat face, thickness_mm) if the component is a broad thin plate, else (None, 0)."""
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
            gap_mm = abs(v.dotProduct(n1)) * 10.0        # Fusion API cm -> mm
            area_mm2 = top.area * 100.0                  # cm^2 -> mm^2
            if 0.1 < gap_mm < FLAT_MAX_THICKNESS_MM and area_mm2 > FLAT_WIDTH_RATIO * gap_mm ** 2:
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
                    skipped.append((comp.name, "not a broad flat plate (rod/pin/3D part)"))
                continue
            try:
                # Project the flat FACE -> the solid's TRUE TRIMMED outline: rounded ends come
                # through as arcs (not full circles), so nothing gets severed on the laser, plus
                # the holes on that face. Then scan the body's edges for any full-circle (Circle3D)
                # hole edges the face projection missed, so every hole lands.
                sk = comp.sketches.add(face)
                sk.project(face)
                for body in comp.bRepBodies:
                    for edge in body.edges:
                        try:
                            if edge.geometry.objectType == adsk.core.Circle3D.classType():
                                sk.project(edge)
                        except Exception:
                            pass
                path = os.path.join(OUT_DIR, safe(comp.name) + ".dxf")
                ok = sk.saveAsDXF(path)
                sk.deleteMe()
                (exported if ok else skipped).append(
                    (comp.name, thick) if ok else (comp.name, "saveAsDXF returned false"))
            except Exception as e:
                skipped.append((comp.name, "error: %s" % e))

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
            "Exported %d flat parts.\nSkipped %d components (see skipped.csv).\n\n%s\n\n"
            "Now: check parts_raw/, then run  py pack_dxf.py"
            % (len(exported), len(skipped), OUT_DIR)
        )
    except:  # noqa
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
