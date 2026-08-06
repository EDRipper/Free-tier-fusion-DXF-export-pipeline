# Fusion 360 script — capture a clean frame sequence of the beest walking (for a promo video).
# Drives ONE revolute joint through TOTAL_DEG in FRAMES steps and saves a PNG of the canvas at
# each step (no UI, no cursor, high-res). Compile the PNGs to MP4/GIF afterwards.
#
# 1) First run with JOINT_NAME = "" -> it lists your revolute joints in a dialog.
# 2) Set JOINT_NAME to your crank / leg-crankshaft joint (the one you'd Drive Joints on).
# 3) Run again -> frames land in <Desktop>/beest-pipeline/frames/.
import adsk.core
import adsk.fusion
import traceback
import os
import math

JOINT_NAME = "driven 1"  # the joint to spin (leg crankshaft = cleanest loop)
TOTAL_DEG = 1080.0       # 3 turns of the driven gear = 4 turns of the 3:4 pinion => EVERYTHING realigns
FRAMES = 360             # 3 deg/frame; 360 @ 30fps = a 12 s seamless loop (3 gait cycles)
WIDTH, HEIGHT = 1920, 1080


def _desktop():
    od = os.environ.get("OneDrive") or os.environ.get("OneDriveConsumer")
    home = os.path.expanduser("~")
    cands = ([os.path.join(od, "Desktop")] if od else []) + \
            [os.path.join(home, "OneDrive", "Desktop"), os.path.join(home, "Desktop")]
    for c in cands:
        if os.path.isdir(os.path.join(c, "beest-pipeline")):
            return c
    for c in cands:
        if os.path.isdir(c):
            return c
    return os.path.join(home, "Desktop")


def all_joints(design):
    js = []
    for comp in design.allComponents:
        for j in comp.joints:
            js.append(j)
        for j in comp.asBuiltJoints:
            js.append(j)
    return js


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox("Open the beest design first.")
            return

        joints = all_joints(design)
        revs = [j for j in joints if j.jointMotion
                and j.jointMotion.jointType == adsk.fusion.JointTypes.RevoluteJointType]
        names = "\n".join(j.name for j in revs) or "(none found)"

        if not JOINT_NAME:
            ui.messageBox("Set JOINT_NAME (top of the script) to one of these revolute joints,\n"
                          "then run again:\n\n" + names)
            return

        joint = next((j for j in joints if j.name == JOINT_NAME), None)
        if not joint or joint.jointMotion.jointType != adsk.fusion.JointTypes.RevoluteJointType:
            ui.messageBox("Joint '%s' not found / not revolute. Available:\n\n%s" % (JOINT_NAME, names))
            return

        motion = joint.jointMotion
        out = os.path.join(_desktop(), "beest-pipeline", "frames")
        os.makedirs(out, exist_ok=True)
        vp = app.activeViewport
        start = motion.rotationValue

        for i in range(FRAMES):                      # 0 .. FRAMES-1 (no duplicate end frame = clean loop)
            motion.rotationValue = start + math.radians(TOTAL_DEG * i / FRAMES)
            adsk.doEvents()                          # let motion links re-solve
            vp.refresh()
            vp.saveAsImageFile(os.path.join(out, "frame_%04d.png" % i), WIDTH, HEIGHT)

        motion.rotationValue = start                 # restore
        adsk.doEvents(); vp.refresh()
        ui.messageBox("Saved %d frames (%dx%d) to:\n%s\n\nNow compile to video." %
                      (FRAMES, WIDTH, HEIGHT, out))
    except:  # noqa
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
