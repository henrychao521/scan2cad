#!/usr/bin/env python3
"""R3: scene_v3.json → CadQuery B-Rep → STEP (第三引擎, 補齊 MCL39 三軟體)。
房殼(外-內-門窗開口) + 家具方塊 → Assembly → out/room.step。並驗每件 isValid()。
跑: ~/3d/cadquery-venv/bin/python scripts/emit_cadquery.py
"""
import sys, os, json, math
import cadquery as cq

s = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "work/scene_v3.json"))
R = s["room"]; T = s["wall_t"]; CH = s["ceiling_h"]
X0, X1, Z0, Z1 = R["x0"], R["x1"], R["z0"], R["z1"]
cx0, cy0 = (X0+X1)/2, (Z0+Z1)/2
W, D = X1-X0, Z1-Z0

def obb(box):
    b = box; cx = sum(p[0] for p in b)/4; cz = sum(p[1] for p in b)/4
    e1 = (b[1][0]-b[0][0], b[1][1]-b[0][1]); e2 = (b[2][0]-b[1][0], b[2][1]-b[1][1])
    w = math.hypot(*e1); d = math.hypot(*e2); ang = math.degrees(math.atan2(e1[1], e1[0]))
    if w < d: w, d = d, w; ang += 90
    return cx, cz, w, d, ang

# ---- 房殼 ----
shell = (cq.Workplane("XY").box(W+2*T, D+2*T, CH).translate((cx0, cy0, CH/2))
         .cut(cq.Workplane("XY").box(W, D, CH+0.1).translate((cx0, cy0, CH/2))))
# 門開口
d = s.get("door")
if d:
    dw = d.get("w", 0.9); dh = min(2.0, CH-0.05)
    dz = min(max(d["z"]+dw/2, Z0+0.1), Z1-dw-0.1)
    shell = shell.cut(cq.Workplane("XY").box(T*3, dw, dh).translate((X0, dz+dw/2, dh/2)))
# 窗開口
sillh, headh = 0.9, min(2.05, CH-0.1)
def cut_wins(segs, wx):
    global shell
    for a, b in segs:
        a = max(a, Z0+0.1); b = min(b, Z1-0.1)
        if b-a < 0.7: continue
        shell = shell.cut(cq.Workplane("XY").box(T*3, b-a, headh-sillh)
                          .translate((wx, (a+b)/2, (sillh+headh)/2)))
Wd = s.get("windows", {}); cut_wins(Wd.get("left", []), X0); cut_wins(Wd.get("right", []), X1)

asm = cq.Assembly()
asm.add(shell, name="room_shell", color=cq.Color(0.82, 0.80, 0.76))

# ---- 家具(B-Rep 方塊) ----
valid = []; invalid = []
for i, o in enumerate(s["furniture"]):
    cx, cz, w, d2, ang = obb(o["box"])
    h = o["h"]
    part = (cq.Workplane("XY").box(w, d2, h).translate((cx, cz, h/2))
            .rotate((cx, cz, 0), (cx, cz, 1), ang))
    ok = part.val().isValid()
    (valid if ok else invalid).append(f"{o['label']}#{i}")
    asm.add(part, name=f"f{i}_{o['label']}", color=cq.Color(0.42, 0.70, 0.55))

# ---- 匯出 STEP ----
os.makedirs("out", exist_ok=True)
step = "out/room.step"
asm.save(step)
shell_ok = shell.val().isValid()
print(f"房殼 isValid={shell_ok}")
print(f"家具 B-Rep: {len(valid)} 有效 / {len(invalid)} 無效  {('無效:'+str(invalid)) if invalid else ''}")
print(f"→ {step}  ({os.path.getsize(step)//1024} KB, {len(s['furniture'])+1} 實體)")

# STL 給算圖/驗證用(整體 compound)
try:
    comp = shell
    for i, o in enumerate(s["furniture"]):
        cx, cz, w, d2, ang = obb(o["box"]); h = o["h"]
        comp = comp.union(cq.Workplane("XY").box(w, d2, h).translate((cx, cz, h/2)).rotate((cx, cz, 0), (cx, cz, 1), ang))
    cq.exporters.export(comp, "out/room_cq.stl")
    print("→ out/room_cq.stl (union compound)")
except Exception as e:
    print("STL union 略過:", str(e)[:80])

json.dump({"shell_valid": bool(shell_ok), "furniture_valid": len(valid),
           "furniture_invalid": invalid, "n_solids": len(s['furniture'])+1},
          open("work/step_report.json", "w"), ensure_ascii=False, indent=1)
