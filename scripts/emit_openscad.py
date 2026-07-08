#!/usr/bin/env python3
"""scene.json → OpenSCAD .scad (宣告式房間重繪)
座標: OpenSCAD X=arch x(寬), Y=arch z(深), Z=高(上, Z-up)。單位=公尺。
用法: emit_openscad.py [scene.json] [out.scad] [colormode: real|prov]
  real = 擬真材質色; prov = 來源上色(綠=arch 已知 / 橙=點雲發掘 / 藍=VLM 新增)
牆殼扣門/窗; 家具用真實 box 角點 polygon 擠出; 燈具貼天花; wall_items 牆掛; ceiling_items 天花垂吊。
"""
import sys, os, json, math

def box_to_obb(box):
    b = box
    cx = sum(p[0] for p in b)/4.0; cz = sum(p[1] for p in b)/4.0
    e1 = (b[1][0]-b[0][0], b[1][1]-b[0][1]); e2 = (b[2][0]-b[1][0], b[2][1]-b[1][1])
    w = math.hypot(*e1); d = math.hypot(*e2); ang = math.degrees(math.atan2(e1[1], e1[0]))
    if w < d: w, d = d, w; ang += 90
    return cx, cz, w, d, ang

def module_for(label):
    if "凳" in label: return "stool"
    if "空壓" in label: return "compressor"
    if "鑽" in label or "床" in label or "砂輪" in label: return "drillpress"
    if "層架" in label or "架" in label: return "shelving"
    if "櫃" in label: return "cabinet"
    if "檯" in label or "桌" in label: return "bench"
    return "genericbox"

SCENE = sys.argv[1] if len(sys.argv) > 1 else "work/scene_v3.json"
OUT   = sys.argv[2] if len(sys.argv) > 2 else "out/room.scad"
MODE  = sys.argv[3] if len(sys.argv) > 3 else "real"
s = json.load(open(SCENE))
R = s["room"]; T = s["wall_t"]; CH = s["ceiling_h"]
X0, X1, Z0, Z1 = R["x0"], R["x1"], R["z0"], R["z1"]

L = []; ap = L.append
ap("// ===== scan2cad 自動重繪: 由 3DGS 點雲量測 + 幾何發掘 + VLM 生成 =====")
ap(f"// 室內淨 {X1-X0:.2f}(寬) × {Z1-Z0:.2f}(深) × {CH:.2f}(高) m  |  模式={MODE}")
ap(f"// k={s['K']:.4f} m/單位  |  來源: {os.path.basename(s['src_ply'])} + arch + VLM")
ap("$fn=40;")
ap("use <furniture_lib.scad>;")
ap("C_WALL=[0.82,0.80,0.76]; C_FLOOR=[0.60,0.58,0.55]; C_BOARD=[0.16,0.28,0.22];")
ap("C_BENCH=[0.42,0.70,0.55]; C_DESK=[0.86,0.74,0.52]; C_CAB=[0.55,0.62,0.70]; C_MACHINE=[0.58,0.61,0.66];")
ap("C_LIGHT=[1,0.96,0.75]; C_SCREEN=[0.92,0.92,0.9]; C_AC=[0.9,0.9,0.92]; C_DUCT=[0.85,0.85,0.87];")
ap("C_KNOWN=[0.30,0.80,0.40]; C_DISC=[1.0,0.55,0.10]; C_VLM=[0.30,0.55,1.0];")
ap("")

def src_color(o):
    if MODE == "prov":
        sr = o.get("src", "")
        if sr == "vlm": return "C_VLM"
        if sr.startswith("discovered"): return "C_DISC"
        return "C_KNOWN"
    lab = o["label"]
    if any(k in lab for k in ("鑽", "床", "砂輪", "壓", "機", "器材")): return "C_MACHINE"
    if "檯" in lab and "連排" in lab: return "C_BENCH"
    if "櫃" in lab: return "C_CAB"
    if "桌" in lab: return "C_BENCH"
    if "凳" in lab: return "C_DESK"
    return "C_BENCH"

# 牆殼
ap("module walls(){ difference(){")
ap(f"  translate([{X0-T:.3f},{Z0-T:.3f},0]) cube([{(X1-X0)+2*T:.3f},{(Z1-Z0)+2*T:.3f},{CH:.3f}]);")
ap(f"  translate([{X0:.3f},{Z0:.3f},-0.01]) cube([{X1-X0:.3f},{Z1-Z0:.3f},{CH+0.02:.3f}]);")
d = s.get("door")
if d:
    dw = d.get("w", 0.9); dh = min(2.0, CH-0.05)
    dz = min(max(d["z"]+dw/2, Z0+0.1), Z1-dw-0.1)
    ap(f"  translate([{X0-T-0.02:.3f},{dz:.3f},0]) cube([{T+0.04:.3f},{dw:.3f},{dh:.3f}]); // 門(推定)")
def wins(segs, wx, side):
    for a, b in segs:
        a = max(a, Z0+0.1); b = min(b, Z1-0.1)
        if b-a < 0.7: continue
        sill, head = 0.9, min(2.05, CH-0.1)
        ap(f"  translate([{wx-T-0.02:.3f},{a:.3f},{sill:.3f}]) cube([{T+0.04:.3f},{b-a:.3f},{head-sill:.3f}]); // 窗{side}")
W = s.get("windows", {}); wins(W.get("left", []), X0, "左"); wins(W.get("right", []), X1, "右")
ap("} }")
ap("module floorplane(){ color(C_FLOOR) translate([%.3f,%.3f,-0.03]) cube([%.3f,%.3f,0.03]); }"
   % (X0-T, Z0-T, (X1-X0)+2*T, (Z1-Z0)+2*T))
bb = s.get("blackboard")
if bb:
    bw = bb['x1']-bb['x0']
    ap("module blackboard(){")
    ap(f"  color(C_BOARD) translate([{bb['x0']:.3f},{Z1-0.03:.3f},0.85]) cube([{bw:.3f},0.03,1.0]);")
    ap(f"  color([0.75,0.6,0.4]) difference(){{")   # 木框
    ap(f"    translate([{bb['x0']-0.05:.3f},{Z1-0.05:.3f},0.80]) cube([{bw+0.10:.3f},0.05,1.10]);")
    ap(f"    translate([{bb['x0']:.3f},{Z1-0.08:.3f},0.85]) cube([{bw:.3f},0.06,1.0]);")
    ap(f"  }}")
    ap("}")

# ---- 建築細節(R2): 踢腳 / 窗框窗台 / 門扇門框 ----
sillh, headh = 0.9, min(2.05, CH-0.1)
win_specs = []
for a, b in W.get("left", []):
    a = max(a, Z0+0.1); b = min(b, Z1-0.1)
    if b-a >= 0.7: win_specs.append(("x0", X0, a, b))
for a, b in W.get("right", []):
    a = max(a, Z0+0.1); b = min(b, Z1-0.1)
    if b-a >= 0.7: win_specs.append(("x1", X1, a, b))

sk, kt = 0.07, 0.02
ap("module skirting(){ color([0.5,0.48,0.45]) union(){")
ap(f"  translate([{X0:.3f},{Z0:.3f},0]) cube([{X1-X0:.3f},{kt},{sk}]);")
ap(f"  translate([{X0:.3f},{Z1-kt:.3f},0]) cube([{X1-X0:.3f},{kt},{sk}]);")
ap(f"  translate([{X0:.3f},{Z0:.3f},0]) cube([{kt},{Z1-Z0:.3f},{sk}]);")
ap(f"  translate([{X1-kt:.3f},{Z0:.3f},0]) cube([{kt},{Z1-Z0:.3f},{sk}]);")
ap("} }")

ap("module windetail(){")
for wall, wx, a, b in win_specs:
    gx = wx - T/2
    inner = X0 if wall == "x0" else X1-0.08
    ap(f"  // 窗 {wall} {a:.2f}-{b:.2f}m")
    ap(f"  color([0.58,0.76,0.9]) translate([{gx-0.01:.3f},{a:.3f},{sillh:.3f}]) cube([0.02,{b-a:.3f},{headh-sillh:.3f}]);")  # 玻璃
    ap(f"  color([0.92,0.92,0.92]) union(){{")
    ap(f"    translate([{gx-0.03:.3f},{a:.3f},{sillh:.3f}]) cube([0.06,0.05,{headh-sillh:.3f}]);")
    ap(f"    translate([{gx-0.03:.3f},{b-0.05:.3f},{sillh:.3f}]) cube([0.06,0.05,{headh-sillh:.3f}]);")
    ap(f"    translate([{gx-0.03:.3f},{a:.3f},{sillh:.3f}]) cube([0.06,{b-a:.3f},0.05]);")
    ap(f"    translate([{gx-0.03:.3f},{a:.3f},{headh-0.05:.3f}]) cube([0.06,{b-a:.3f},0.05]);")
    nmul = max(1, int((b-a)//1.1))
    for k in range(1, nmul+1):
        mz = a + k*(b-a)/(nmul+1)
        ap(f"    translate([{gx-0.03:.3f},{mz-0.02:.3f},{sillh:.3f}]) cube([0.06,0.04,{headh-sillh:.3f}]);")
    ap(f"  }}")
    ap(f"  color([0.8,0.78,0.75]) translate([{inner:.3f},{a-0.03:.3f},{sillh-0.04:.3f}]) cube([0.08,{b-a+0.06:.3f},0.04]);")  # 窗台
ap("}")

if d:
    dw = d.get("w", 0.9); dh = min(2.0, CH-0.05)
    dz = min(max(d["z"]+dw/2, Z0+0.1), Z1-dw-0.1)
    ap("module doordetail(){")
    ap(f"  color([0.62,0.45,0.30]) union(){{")   # 門框
    ap(f"    translate([{X0-0.03:.3f},{dz-0.05:.3f},0]) cube([{T+0.06:.3f},0.05,{dh:.3f}]);")
    ap(f"    translate([{X0-0.03:.3f},{dz+dw:.3f},0]) cube([{T+0.06:.3f},0.05,{dh:.3f}]);")
    ap(f"    translate([{X0-0.03:.3f},{dz-0.05:.3f},{dh:.3f}]) cube([{T+0.06:.3f},{dw+0.10:.3f},0.05]);")
    ap(f"  }}")
    ap(f"  color([0.72,0.55,0.38]) translate([{X0:.3f},{dz:.3f},0]) rotate([0,0,-42]) cube([0.04,{dw:.3f},{dh:.3f}]);")  # 門扇(半開)
    ap(f"  color([0.85,0.7,0.3]) translate([{X0:.3f},{dz:.3f},1.0]) rotate([0,0,-42]) translate([0.04,{dw-0.08:.3f},0]) sphere(r=0.03);")  # 把手
    ap("}")

# 家具
ap("module furniture(){")
for i, o in enumerate(s["furniture"]):
    cx, cz, w, d, ang = box_to_obb(o["box"])
    mod = module_for(o["label"])
    ap(f"  // #{i} {o['label']} {w:.2f}x{d:.2f}x{o['h']:.2f}m [{o.get('src','arch')}] -> {mod}")
    ap(f"  translate([{cx:.3f},{cz:.3f},0]) rotate([0,0,{ang:.2f}]) color({src_color(o)}) {mod}({w:.3f},{d:.3f},{o['h']:.3f});")
ap("}")

# 燈具
ap("module lights(){")
for lt in s.get("lights", []):
    ln = lt["len"]; ang = lt["ang"]
    ap(f"  translate([{lt['x']:.3f},{lt['z']:.3f},{CH-0.05:.3f}]) rotate([0,0,{ang:.1f}]) color(C_LIGHT) translate([{-ln/2:.3f},-0.06,0]) cube([{ln:.3f},0.12,0.05]);")
ap("}")

# 牆掛物件(VLM)
def wall_box(o):
    wall = o["wall"]; a, b = o["along"]; base = o["base_h"]; h = o["h"]; th = o.get("thick", 0.05)
    col = "C_VLM" if MODE == "prov" else ("C_SCREEN" if "幕" in o["label"] else ("C_AC" if "冷氣" in o["label"] else "C_CAB"))
    if wall == "x0":   cube = (th, b-a, h); pos = (X0, a, base)
    elif wall == "x1": cube = (th, b-a, h); pos = (X1-th, a, base)
    elif wall == "z0": cube = (b-a, th, h); pos = (a, Z0, base)
    else:              cube = (b-a, th, h); pos = (a, Z1-th, base)
    ap(f"  color({col}) translate([{pos[0]:.3f},{pos[1]:.3f},{pos[2]:.3f}]) cube([{cube[0]:.3f},{cube[1]:.3f},{cube[2]:.3f}]); // {o['label']}[vlm]")
ap("module wallitems(){")
for o in s.get("wall_items", []): wall_box(o)
ap("}")

# 天花板垂吊(VLM)
ap("module ceilingitems(){")
for o in s.get("ceiling_items", []):
    col = "C_VLM" if MODE == "prov" else "C_DUCT"
    ap(f"  color({col}) translate([{o['x']:.3f},{o['z']:.3f},{CH-o.get('drop',0.6):.3f}]) cylinder(h={o.get('drop',0.6):.3f},r={o.get('r',0.12):.3f}); // {o['label']}[vlm]")
ap("}")

ap("color(C_WALL) walls();")
ap("floorplane();")
ap("skirting(); windetail();")
if d: ap("doordetail();")
if bb: ap("blackboard();")
ap("furniture(); lights(); wallitems(); ceilingitems();")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write("\n".join(L) + "\n")
nf = len(s["furniture"]); nw = len(s.get("wall_items", [])); nc = len(s.get("ceiling_items", []))
print(f"→ {OUT}  [{MODE}]  家具{nf} 牆掛{nw} 天花{nc} 燈{len(s.get('lights',[]))}")
