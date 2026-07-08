#!/usr/bin/env python3
"""R4: MCL39 式場景驗證 L1/L3。
L1 健康: STEP 每件實體 isValid (讀 step_report.json)。
L3 裝配: 家具足跡兩兩穿插(clash) + 是否皆在房內。
出 work/verify_scene_report.json + work/clash_map.png。
穿插用共享網格柵格化足跡取交集面積(避免 shapely 依賴)。
"""
import sys, os, json
import numpy as np
import cv2
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

SCENE = sys.argv[1] if len(sys.argv) > 1 else "work/scene_v3.json"
s = json.load(open(SCENE))
R = s["room"]; X0, X1, Z0, Z1 = R["x0"], R["x1"], R["z0"], R["z1"]
step = json.load(open("work/step_report.json")) if os.path.exists("work/step_report.json") else {}

CELL = 0.03
W = int((X1-X0)/CELL)+2; H = int((Z1-Z0)/CELL)+2
def raster(box):
    m = np.zeros((H, W), np.uint8)
    poly = np.array([[int((px-X0)/CELL), int((pz-Z0)/CELL)] for px, pz in box], np.int32)
    cv2.fillPoly(m, [poly], 1); return m

F = s["furniture"]
masks = [raster(o["box"]) for o in F]
areas = [int(m.sum()) for m in masks]

# L3-a: 兩兩穿插
CLASH_FRAC = 0.06   # 交集>較小件6%才算真穿插(容忍量測邊界微疊)
clashes = []
for i in range(len(F)):
    for j in range(i+1, len(F)):
        inter = int((masks[i] & masks[j]).sum())
        if inter == 0: continue
        frac = inter / max(1, min(areas[i], areas[j]))
        if frac > CLASH_FRAC:
            clashes.append({"a": F[i]["label"], "ai": i, "b": F[j]["label"], "bj": j,
                            "overlap_m2": round(inter*CELL*CELL, 3), "frac": round(frac, 2)})

# L3-b: 是否在房內(角點超出牆內緣容忍 5cm)
tol = 0.05
out_of_room = []
for i, o in enumerate(F):
    for px, pz in o["box"]:
        if px < X0-tol or px > X1+tol or pz < Z0-tol or pz > Z1+tol:
            out_of_room.append({"label": o["label"], "i": i,
                                "corner": [round(px, 2), round(pz, 2)]}); break

L1_pass = step.get("shell_valid", True) and step.get("furniture_invalid", []) == []
L3_pass = len(clashes) == 0 and len(out_of_room) == 0
report = {
    "L1_健康": {"pass": bool(L1_pass), "shell_valid": step.get("shell_valid"),
              "furniture_valid": step.get("furniture_valid"), "invalid": step.get("furniture_invalid", [])},
    "L3_裝配": {"pass": bool(L3_pass), "clash_pairs": clashes,
              "out_of_room": out_of_room, "clash_tol_frac": CLASH_FRAC, "room_tol_m": tol},
    "summary": f"L1 {'✓' if L1_pass else '✗'} · L3 {'✓' if L3_pass else '✗'} "
               f"({len(clashes)} 穿插, {len(out_of_room)} 出界)",
}
json.dump(report, open("work/verify_scene_report.json", "w"), ensure_ascii=False, indent=1)

# clash 圖
fig, ax = plt.subplots(figsize=(8.5, 10))
ax.add_patch(Polygon([[X0, Z0], [X1, Z0], [X1, Z1], [X0, Z1]], closed=True, fill=False, ec='#111', lw=2))
clash_ids = set()
for c in clashes: clash_ids.add(c["ai"]); clash_ids.add(c["bj"])
oor_ids = {o["i"] for o in out_of_room}
for i, o in enumerate(F):
    col = '#e23b3b' if i in clash_ids else ('#e8a020' if i in oor_ids else '#25c04a')
    ax.add_patch(Polygon(np.array(o["box"]), closed=True, fill=True, fc=col, ec='#222', lw=1, alpha=0.5))
    ax.text(o["cx"], o["cz"], o["label"], ha='center', va='center', fontsize=6)
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang TC']; plt.rcParams['axes.unicode_minus'] = False
ax.set_xlim(X0-0.5, X1+0.5); ax.set_ylim(Z1+0.5, Z0-0.5); ax.set_aspect('equal')
ax.set_title(f"L3 裝配檢查 · 綠=OK 紅=穿插 橙=出界\n{report['summary']}", fontsize=12)
ax.set_xlabel("X 寬 (m)"); ax.set_ylabel("Z 深 (m)")
plt.tight_layout(); plt.savefig("work/clash_map.png", dpi=115, facecolor='white'); plt.close()
print(json.dumps(report, ensure_ascii=False, indent=1))
print("→ work/verify_scene_report.json, clash_map.png")
