#!/usr/bin/env python3
"""檢索件: 精密立式鑽床 CadQuery B-Rep → out/drillpress.step (可製造)。
跑: ~/3d/cadquery-venv/bin/python scripts/emit_drillpress_step.py
單件示範「檢索>重建」: 以精密參數化零件取代點雲粗方塊。
"""
import cadquery as cq, math, os

H = 1.55; coly = -0.10; rc = 0.032
p = cq.Workplane("XY")

# 底座 (圓角箱 + T槽 + 安裝孔)
base = (cq.Workplane("XY").box(0.34, 0.42, 0.05).edges("|Z").fillet(0.03)
        .translate((0, coly+0.035, 0.025)))
for sx in (-0.07, 0, 0.07):
    base = base.cut(cq.Workplane("XY").box(0.016, 0.30, 0.03).translate((sx, coly+0.04, 0.05)))
for sx in (-0.11, 0.11):
    base = base.cut(cq.Workplane("XY").cylinder(0.09, 0.011).translate((sx, coly-0.07, 0.03)))
part = base
# 立柱
part = part.union(cq.Workplane("XY").cylinder(H-0.05, rc).translate((0, coly, 0.05+(H-0.05)/2)))
# 圓工作台 (中心孔) + 支臂套環 + 夾把
tz = H*0.42
table = (cq.Workplane("XY").cylinder(0.028, 0.14).translate((0, 0.07, tz))
         .cut(cq.Workplane("XY").cylinder(0.05, 0.018).translate((0, 0.07, tz))))
part = part.union(table)
part = part.union(cq.Workplane("XY").cylinder(0.11, 0.05).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, coly, tz)))
part = part.union(cq.Workplane("XY").cylinder(0.10, 0.008).rotate((0, 0, 0), (0, 1, 0), 90).translate((0.06, 0.03, tz)))
part = part.union(cq.Workplane("XY").sphere(0.02).translate((0.13, 0.03, tz)))
# 頭部鑄件 + 馬達 + 皮帶罩
hz = H*0.80
part = part.union(cq.Workplane("XY").cylinder(0.14, 0.10).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, coly, hz)))
part = part.union(cq.Workplane("XY").box(0.14, 0.20, 0.14).translate((0, 0.02, hz)))
part = part.union(cq.Workplane("XY").cylinder(0.15, 0.085).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, coly-0.05, hz+0.02)))
# 主軸套筒 + 夾頭 + 鑽頭
part = part.union(cq.Workplane("XY").cylinder(0.13, 0.022).translate((0, 0.09, hz-0.11)))
part = part.union(cq.Workplane("XY").circle(0.031).workplane(offset=0.08).circle(0.026).loft().translate((0, 0.09, hz-0.19)))
part = part.union(cq.Workplane("XY").cylinder(0.04, 0.006).translate((0, 0.09, hz-0.215)))
# 三幅進給手輪
hub = (0.10, 0.02, hz-0.03)
part = part.union(cq.Workplane("XY").cylinder(0.03, 0.022).rotate((0, 0, 0), (0, 1, 0), 90).translate(hub))
for a in (0, 120, 240):
    dz = math.cos(math.radians(a)); dy = math.sin(math.radians(a))
    end = (hub[0], hub[1]+dy*0.11, hub[2]+dz*0.11)
    part = part.union(cq.Workplane("XY").cylinder(0.11, 0.007)
                      .rotate((0, 0, 0), (1, 0, 0), a).translate((hub[0], hub[1]+dy*0.055, hub[2]+dz*0.055)))
    part = part.union(cq.Workplane("XY").sphere(0.015).translate(end))

os.makedirs("out", exist_ok=True)
sol = part.val()
print("鑽床 B-Rep isValid:", sol.isValid(), "· 體積 %.4f m³" % sol.Volume())
cq.exporters.export(part, "out/drillpress.step")
cq.exporters.export(part, "out/drillpress.stl")
print("→ out/drillpress.step (%d KB) + drillpress.stl" % (os.path.getsize("out/drillpress.step")//1024))
