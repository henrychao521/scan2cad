#!/usr/bin/env python3
"""Phase 2: 從點雲自動發掘 arch_elements 沒涵蓋的新物件。
掃地板以上體積 → 排除牆/已知家具佔位 → XZ 占據網格分群 → minAreaRect 方塊 + 高度。
輸出 work/discovered.json + work/discover_debug.png，並寫 work/scene_v2.json(已知+新發掘)。
"""
import sys, os, json
import numpy as np
import cv2
sys.path.insert(0, os.path.dirname(__file__))
from plyio import read_ply, opacity

SCENE = sys.argv[1] if len(sys.argv) > 1 else "work/scene.json"
s = json.load(open(SCENE))
K = s["K"]; floor_y = s["floor_y_unit"]
R = s["room"]; X0, X1, Z0, Z1 = R["x0"], R["x1"], R["z0"], R["z1"]
cols, n = read_ply(s["src_ply"])
x, y, z = cols['x'], cols['y'], cols['z']; op = opacity(cols)

# 站立物體積: 離地 0.12–2.1 m, 且在室內(退牆 8cm)
hgt = (floor_y - y) * K
inside = (x > (X0/K)+0.08/K) & (x < (X1/K)-0.08/K) & (z > (Z0/K)+0.08/K) & (z < (Z1/K)-0.08/K)
band = (hgt > 0.12) & (hgt < 2.1) & (op > 0.25) & inside
xu, zu, hh = x[band], z[band], hgt[band]
print(f"站立物候選點 {band.sum():,}")

# XZ 占據網格 (公制 3cm)
CELL = 0.03
xm, zm = xu*K, zu*K
W = int((X1-X0)/CELL)+2; H = int((Z1-Z0)/CELL)+2
gi = ((xm-X0)/CELL).astype(int).clip(0, W-1)
gj = ((zm-Z0)/CELL).astype(int).clip(0, H-1)
G = np.zeros((H, W), np.float32)
np.add.at(G, (gj, gi), 1.0)
# 每格最高物高(給後面查高度)
HT = np.zeros((H, W), np.float32)
np.maximum.at(HT, (gj, gi), hh)

occ = (G > np.quantile(G[G > 0], 0.62)).astype(np.uint8)
occ = cv2.morphologyEx(occ, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1)
occ = cv2.morphologyEx(occ, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)

# 已知家具佔位遮罩(公制 box → 網格)
known = np.zeros((H, W), np.uint8)
for o in s["furniture"]:
    poly = np.array([[int((px-X0)/CELL), int((pz-Z0)/CELL)] for px, pz in o["box"]], np.int32)
    cv2.fillPoly(known, [poly], 1)
known = cv2.dilate(known, np.ones((5, 5), np.uint8), 1)

# 侵蝕分裂: 打斷細橋 → 標記侵蝕後的核 → 各自膨脹回原尺寸取 box(避免整片黏成巨塊)
ITER = 4
core = cv2.erode(occ, np.ones((3, 3), np.uint8), iterations=ITER)
nf, lab, stats, cent = cv2.connectedComponentsWithStats(core)
disc = []
for i in range(1, nf):
    core_m = (lab == i).astype(np.uint8)
    if core_m.sum() < 6:
        continue
    m = (cv2.dilate(core_m, np.ones((3, 3), np.uint8), iterations=ITER) & occ).astype(bool)
    area = m.sum() * CELL * CELL
    if area < 0.08 or area > 6.0:   # 太小=雜訊, 太大=殘留巨塊 → 拒絕
        continue
    overlap = (m & (known > 0)).sum() / max(m.sum(), 1)
    if overlap > 0.45:              # 大半與已知家具重疊 → 已知
        continue
    ys, xs = np.where(m)
    rect = cv2.minAreaRect(np.stack([xs, ys], 1).astype(np.float32))
    box = [[round(float(px*CELL+X0), 3), round(float(py*CELL+Z0), 3)] for px, py in cv2.boxPoints(rect)]
    (cx, cz), (w, d), ang = rect
    w, d = max(w, d)*CELL, min(w, d)*CELL
    h = float(np.percentile(HT[m][HT[m] > 0], 95)) if (HT[m] > 0).any() else 0.7
    disc.append({"box": box, "cx": round(cx*CELL+X0, 3), "cz": round(cz*CELL+Z0, 3),
                 "w": round(w, 2), "d": round(d, 2), "h": round(min(h, 2.1), 2),
                 "label": "未辨識物", "src": "discovered", "area": round(area, 2)})
disc.sort(key=lambda o: -o["w"]*o["d"])
print(f"發掘出 {len(disc)} 個新物件(非已知家具):")
for o in disc:
    print(f"  {o['w']:.2f}×{o['d']:.2f}×{o['h']:.2f}m  ({o['area']:.1f}m²)  @({o['cx']:.1f},{o['cz']:.1f})")

json.dump(disc, open("work/discovered.json", "w"), ensure_ascii=False, indent=1)

# scene_v2 = 已知 + 新發掘
s2 = dict(s)
s2["furniture"] = s["furniture"] + [{k: v for k, v in o.items() if k != "area"} for o in disc]
s2["discovered_n"] = len(disc)
json.dump(s2, open("work/scene_v2.json", "w"), ensure_ascii=False, indent=1)

# debug 俯視圖
dbg = cv2.cvtColor((occ*60).astype(np.uint8), cv2.COLOR_GRAY2BGR)
for o in s["furniture"]:
    poly = np.array([[int((px-X0)/CELL), int((pz-Z0)/CELL)] for px, pz in o["box"]], np.int32)
    cv2.polylines(dbg, [poly], True, (0, 200, 0), 2)          # 綠=已知
for o in disc:
    poly = np.array([[int((px-X0)/CELL), int((pz-Z0)/CELL)] for px, pz in o["box"]], np.int32)
    cv2.polylines(dbg, [poly], True, (0, 80, 255), 2)         # 紅=新發掘
cv2.imwrite("work/discover_debug.png", cv2.flip(dbg, 0))
print("→ work/discovered.json, scene_v2.json, discover_debug.png")
