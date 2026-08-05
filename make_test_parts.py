#!/usr/bin/env python
"""Generate synthetic Fusion-like part DXFs (outline + 4 mm holes) + a manifest,
so the pipeline can be tested end-to-end without Fusion. Delete parts_raw/ and
replace with your real Fusion exports for the actual run."""
import csv
import os
import ezdxf

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parts_raw")
os.makedirs(OUT, exist_ok=True)


def save(name, msp_builder):
    doc = ezdxf.new(); doc.units = ezdxf.units.MM
    msp_builder(doc.modelspace())
    doc.saveas(os.path.join(OUT, name + ".dxf"))


def link(name, length, width=8.0):
    def build(msp):
        msp.add_lwpolyline([(0, 0), (length, 0), (length, width), (0, width)], close=True)
        msp.add_circle((width / 2, width / 2), radius=2.0)                 # 4 mm hole
        msp.add_circle((length - width / 2, width / 2), radius=2.0)        # 4 mm hole
    save(name, build)


def triangle(name, a=40.0):
    def build(msp):
        msp.add_lwpolyline([(0, 0), (a, 0), (a / 2, a * 0.87)], close=True)
        for hx, hy in [(5, 4), (a - 5, 4), (a / 2, a * 0.72)]:
            msp.add_circle((hx, hy), radius=2.0)
    save(name, build)


def frame(name, w=60.0, h=40.0):
    def build(msp):
        msp.add_lwpolyline([(0, 0), (w, 0), (w, h), (0, h)], close=True)
        for hx, hy in [(10, 10), (w - 10, 10), (10, h - 10), (w - 10, h - 10)]:
            msp.add_circle((hx, hy), radius=2.0)                           # bearing seats
    save(name, build)


link("link_long", 45)
link("link_short", 28)
triangle("triangle")
frame("frame")

with open(os.path.join(OUT, "parts_manifest.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["part", "per_kit_qty", "thickness_mm"])
    w.writerow(["link_long", 6, 9])
    w.writerow(["link_short", 6, 9])
    w.writerow(["triangle", 3, 9])
    w.writerow(["frame", 1, 9])

print("wrote synthetic test parts + manifest to", OUT)
