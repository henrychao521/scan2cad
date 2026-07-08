#!/usr/bin/env python3
"""scene_v3.json → 自含 Blender bpy 腳本 out/build_blender.py (建同一房間 + Workbench 算圖)。
跑法: Blender -b -P out/build_blender.py
Blender 座標 X=寬 Y=深 Z=高(Z-up, 天生)。家具由 box 角點求中心/尺寸/角度 → cube。
"""
import sys, os, json, math
import numpy as np

s = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "work/scene_v3.json"))
MODE = sys.argv[2] if len(sys.argv) > 2 else "real"
OUT = "out/build_blender.py"; IMG = os.path.abspath("out/room_blender.png")
R = s["room"]; T = s["wall_t"]; CH = s["ceiling_h"]
X0, X1, Z0, Z1 = R["x0"], R["x1"], R["z0"], R["z1"]
cx0, cy0 = (X0+X1)/2, (Z0+Z1)/2

def box_to_obb(box):
    b = np.array(box)
    c = b.mean(0)
    e1 = b[1]-b[0]; e2 = b[2]-b[1]
    w = np.linalg.norm(e1); d = np.linalg.norm(e2)
    ang = math.atan2(e1[1], e1[0])
    if w < d: w, d = d, w; ang += math.pi/2
    return float(c[0]), float(c[1]), float(w), float(d), float(ang)

COL = {"bench":(0.42,0.70,0.55), "desk":(0.86,0.74,0.52), "cab":(0.55,0.62,0.70),
       "known":(0.30,0.80,0.40), "disc":(1.0,0.55,0.10), "vlm":(0.30,0.55,1.0),
       "wall":(0.82,0.80,0.76), "floor":(0.55,0.53,0.5), "board":(0.16,0.28,0.22),
       "light":(1,0.96,0.75), "screen":(0.92,0.92,0.9)}
def fcol(o):
    if MODE == "prov":
        return COL["disc"] if str(o.get("src","")).startswith("discovered") else COL["known"]
    l = o["label"]
    if "櫃" in l: return COL["cab"]
    if "凳" in l: return COL["desk"]
    return COL["bench"]

L = []; ap = L.append
ap("import bpy, math")
ap("bpy.ops.wm.read_factory_settings(use_empty=True)")
ap("def mat(name,rgb):")
ap("    m=bpy.data.materials.new(name); m.use_nodes=False; m.diffuse_color=(rgb[0],rgb[1],rgb[2],1); return m")
ap("def box(name,cx,cy,cz,sx,sy,sz,rgb,rot=0):")
ap("    bpy.ops.mesh.primitive_cube_add(size=1,location=(cx,cy,cz))")
ap("    o=bpy.context.active_object; o.name=name; o.scale=(sx,sy,sz); o.rotation_euler[2]=rot")
ap("    o.data.materials.append(mat(name,rgb)); return o")
ap("def cyl(name,cx,cy,cz,r,h,rgb,axis='z',rot=0):")
ap("    bpy.ops.mesh.primitive_cylinder_add(radius=r,depth=h,location=(cx,cy,cz))")
ap("    o=bpy.context.active_object; o.name=name")
ap("    o.rotation_euler=(0,1.5708,rot) if axis=='x' else (0,0,rot)")
ap("    o.data.materials.append(mat(name,rgb)); return o")
# 牆(4 片, 避免 boolean) — 用 4 條牆 cuboid, 留門窗簡化(牆頂到 CH)
Wt, Lt = X1-X0, Z1-Z0
ap(f"# 牆")
ap(f"box('wall_z0',{cx0},{Z0-T/2},{CH/2},{Wt+2*T},{T},{CH},{COL['wall']})")
ap(f"box('wall_z1',{cx0},{Z1+T/2},{CH/2},{Wt+2*T},{T},{CH},{COL['wall']})")
ap(f"box('wall_x0',{X0-T/2},{cy0},{CH/2},{T},{Lt},{CH},{COL['wall']})")
ap(f"box('wall_x1',{X1+T/2},{cy0},{CH/2},{T},{Lt},{CH},{COL['wall']})")
ap(f"box('floor',{cx0},{cy0},-0.015,{Wt+2*T},{Lt+2*T},0.03,{COL['floor']})")
bb = s.get("blackboard")
if bb:
    ap(f"box('blackboard',{(bb['x0']+bb['x1'])/2},{Z1-0.02},1.35,{bb['x1']-bb['x0']},0.04,1.0,{COL['board']})")
# 家具(細緻: 檯面+桌腳 / 座面+腳 / 氣瓶 / 其餘方塊)
def legpos(cx, cy, w, d, ang, inset=0.06):
    ca, sa = math.cos(ang), math.sin(ang); pts = []
    npair = max(2, int(w/1.4)+1)
    for i in range(npair):
        lx = -w/2+inset + i*(w-2*inset)/(npair-1)
        for sy in (-1, 1):
            ly = sy*(d/2-inset)
            pts.append((cx+lx*ca-ly*sa, cy+lx*sa+ly*ca))
    return pts
for i, o in enumerate(s["furniture"]):
    cx, cy, w, d, ang = box_to_obb(o["box"]); h = o["h"]; rgb = fcol(o); lab = o["label"]; nm = f"f{i}"
    if ("檯" in lab or "桌" in lab):                     # 工作檯: 檯面+桌腳+層板
        ap(f"box('{nm}_top',{cx:.3f},{cy:.3f},{h-0.022:.3f},{w:.3f},{d:.3f},0.045,{rgb},{ang:.4f})")
        for k, (gx, gy) in enumerate(legpos(cx, cy, w, d, ang)):
            ap(f"box('{nm}_lg{k}',{gx:.3f},{gy:.3f},{(h-0.045)/2:.3f},0.06,0.06,{h-0.045:.3f},{rgb},{ang:.4f})")
        ap(f"box('{nm}_sh',{cx:.3f},{cy:.3f},0.12,{w-0.14:.3f},{d-0.14:.3f},0.02,{rgb},{ang:.4f})")
    elif "凳" in lab:                                    # 木凳: 座面+腳
        ap(f"box('{nm}_st',{cx:.3f},{cy:.3f},{h-0.02:.3f},{w:.3f},{d:.3f},0.035,{rgb},{ang:.4f})")
        for k, (gx, gy) in enumerate(legpos(cx, cy, w, d, ang, 0.04)):
            ap(f"cyl('{nm}_lg{k}',{gx:.3f},{gy:.3f},{(h-0.035)/2:.3f},0.016,{h-0.035:.3f},{rgb})")
    elif "空壓" in lab:                                  # 空壓機: 氣瓶+馬達
        tr = min(d, h*0.55)/2
        ap(f"cyl('{nm}_tank',{cx:.3f},{cy:.3f},{tr+0.06:.3f},{tr:.3f},{w-0.1:.3f},{rgb},'x',{ang:.4f})")
        ap(f"box('{nm}_mot',{cx:.3f},{cy:.3f},{2*tr+0.06:.3f},{w*0.4:.3f},{d*0.6:.3f},{max(0.1,h-2*tr-0.06):.3f},{rgb},{ang:.4f})")
    else:                                                # 櫃/機台/器材: 方塊
        ap(f"box('{nm}_{lab}',{cx:.3f},{cy:.3f},{h/2:.3f},{w:.3f},{d:.3f},{h:.3f},{rgb},{ang:.4f})")
# 燈
for i, lt in enumerate(s.get("lights", [])):
    ang = math.radians(lt["ang"])
    ap(f"box('light{i}',{lt['x']:.3f},{lt['z']:.3f},{CH-0.05:.3f},{lt['len']:.3f},0.12,0.05,{COL['light']},{ang:.4f})")
# 牆掛
for i, o in enumerate(s.get("wall_items", [])):
    a, b = o["along"]; wall = o["wall"]; base = o["base_h"]; h = o["h"]; th = o.get("thick", 0.05)
    col = COL["vlm"] if MODE == "prov" else (COL["screen"] if "幕" in o["label"] else COL["cab"])
    if wall == "x0":   cx, cy, sx, sy = X0+th/2, (a+b)/2, th, b-a
    elif wall == "x1": cx, cy, sx, sy = X1-th/2, (a+b)/2, th, b-a
    elif wall == "z0": cx, cy, sx, sy = (a+b)/2, Z0+th/2, b-a, th
    else:              cx, cy, sx, sy = (a+b)/2, Z1-th/2, b-a, th
    ap(f"box('wall_{i}_{o['label']}',{cx:.3f},{cy:.3f},{base+h/2:.3f},{sx:.3f},{sy:.3f},{h:.3f},{col})")
# 天花垂吊
for i, o in enumerate(s.get("ceiling_items", [])):
    col = COL["vlm"] if MODE == "prov" else (0.85,0.85,0.87)
    dr = o.get("drop", 0.6)
    ap(f"cyl('ceil_{i}_{o['label']}',{o['x']:.3f},{o['z']:.3f},{CH-dr/2:.3f},{o.get('r',0.12):.3f},{dr:.3f},{col})")
# 相機 + 燈 + 算圖 (Workbench)
ap(f"cam_data=bpy.data.cameras.new('cam'); cam=bpy.data.objects.new('cam',cam_data); bpy.context.scene.collection.objects.link(cam)")
ap(f"cam.location=({cx0-6.2:.2f},{Z0-5.2:.2f},6.2); cam.rotation_euler=(math.radians(60),0,math.radians(-38))")
ap("cam_data.lens=30; bpy.context.scene.camera=cam")
ap("sun=bpy.data.objects.new('sun',bpy.data.lights.new('sun','SUN')); bpy.context.scene.collection.objects.link(sun)")
ap("sun.data.energy=4.2; sun.rotation_euler=(math.radians(42),math.radians(18),math.radians(10))")
ap("fill=bpy.data.objects.new('fill',bpy.data.lights.new('fill','SUN')); bpy.context.scene.collection.objects.link(fill)")
ap("fill.data.energy=1.5; fill.rotation_euler=(math.radians(50),math.radians(-30),0)")
ap("sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'")
ap("sc.display.shading.light='STUDIO'; sc.display.shading.color_type='MATERIAL'")
ap("sc.render.resolution_x=1400; sc.render.resolution_y=1000; sc.render.film_transparent=False")
ap(f"sc.render.filepath=r'{IMG}'")
ap("bpy.ops.render.render(write_still=True)")
ap("print('RENDERED', sc.render.filepath)")

os.makedirs("out", exist_ok=True)
open(OUT, "w").write("\n".join(L) + "\n")
print(f"→ {OUT}  ({len(s['furniture'])} 家具 + 牆掛/天花)  render→ {IMG}")
