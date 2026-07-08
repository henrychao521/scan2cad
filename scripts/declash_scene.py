#!/usr/bin/env python3
"""R4 修正: 自動消除 L3 穿插/出界(呼應 MCL39 auto_declash)。有上限、確定性。
策略(剛體平移+必要時縮小/移除, 不變形朝向):
  ①全部內縮到房內  ②迭代解穿插:
     - 低優先件(VLM/發掘)被推離高優先件; 累計推 >CAP 仍卡 → 移除(視為量測重複/誤置)
     - arch 互撞 → 縮小較小件足跡(朝中心), 代表其緊貼/塞於大件旁
輸出 work/scene_v4.json。牆掛/天花板不動。
"""
import sys, os, json, copy
import numpy as np
import cv2

s = json.load(open("work/scene_v3.json"))
R = s["room"]; X0, X1, Z0, Z1 = R["x0"], R["x1"], R["z0"], R["z1"]
MARGIN = 0.02; CLASH_FRAC = 0.06; CAP = 10          # 每件最多推 10 步(0.6m)
STEP = 0.06; CELL = 0.03
W = int((X1-X0)/CELL)+2; H = int((Z1-Z0)/CELL)+2
PRIO = {"arch": 3, None: 3, "discovered": 2, "discovered+vlm": 2, "vlm": 1}

F = copy.deepcopy(s["furniture"])
def prio(o): return PRIO.get(o.get("src", "arch"), 2)
def cen(o): return np.array([o["cx"], o["cz"]])
def shift(o, dx, dz): o["box"] = [[p[0]+dx, p[1]+dz] for p in o["box"]]; o["cx"] += dx; o["cz"] += dz
def shrink(o, f):
    c = cen(o); o["box"] = [[c[0]+(p[0]-c[0])*f, c[1]+(p[1]-c[1])*f] for p in o["box"]]
    o["w"] *= f; o["d"] *= f
def clip(o):
    xs = [p[0] for p in o["box"]]; zs = [p[1] for p in o["box"]]; dx = dz = 0.0
    if min(xs) < X0+MARGIN: dx = (X0+MARGIN)-min(xs)
    if max(xs) > X1-MARGIN: dx = (X1-MARGIN)-max(xs)
    if min(zs) < Z0+MARGIN: dz = (Z0+MARGIN)-min(zs)
    if max(zs) > Z1-MARGIN: dz = (Z1-MARGIN)-max(zs)
    if dx or dz: shift(o, dx, dz)
    return abs(dx)+abs(dz)
def raster(o):
    m = np.zeros((H, W), np.uint8)
    poly = np.array([[int((p[0]-X0)/CELL), int((p[1]-Z0)/CELL)] for p in o["box"]], np.int32)
    cv2.fillPoly(m, [poly], 1); return m

clipped = sum(1 for o in F if clip(o) > 1e-6)
pushcount = [0]*len(F); alive = [True]*len(F); removed = []; shrunk = []

def worst_clash():
    idx = [i for i in range(len(F)) if alive[i]]
    masks = {i: raster(F[i]) for i in idx}; areas = {i: int(masks[i].sum()) for i in idx}
    best = None
    for a in range(len(idx)):
        for b in range(a+1, len(idx)):
            i, j = idx[a], idx[b]
            inter = int((masks[i] & masks[j]).sum())
            if inter == 0: continue
            frac = inter/max(1, min(areas[i], areas[j]))
            if frac > CLASH_FRAC and (best is None or inter > best[2]):
                best = (i, j, inter)
    return best

for it in range(200):
    wc = worst_clash()
    if wc is None: break
    i, j, inter = wc
    lo, hi = (i, j) if prio(F[i]) <= prio(F[j]) else (j, i)
    if prio(F[lo]) < 3:                      # 低優先 → 推離
        if pushcount[lo] >= CAP:
            alive[lo] = False; removed.append(F[lo]["label"]); continue
        d = cen(F[lo]) - cen(F[hi]); d = d/max(np.linalg.norm(d), 1e-3)*STEP
        shift(F[lo], float(d[0]), float(d[1])); clip(F[lo]); pushcount[lo] += 1
    else:                                    # arch 互撞 → 縮小較小件
        small = lo if (F[lo]["w"]*F[lo]["d"]) <= (F[hi]["w"]*F[hi]["d"]) else hi
        shrink(F[small], 0.88)
        if F[small]["label"] not in shrunk: shrunk.append(F[small]["label"])
        if F[small]["w"] < 0.15 or F[small]["d"] < 0.1:
            alive[small] = False; removed.append(F[small]["label"]+"(縮沒)")

F2 = [o for k, o in enumerate(F) if alive[k]]
scene4 = dict(s); scene4["furniture"] = F2
scene4["declash"] = {"clipped_inside": clipped, "removed": removed, "shrunk": shrunk, "iters": it}
json.dump(scene4, open("work/scene_v4.json", "w"), ensure_ascii=False, indent=1)
print(f"內縮 {clipped} 件 · 縮小 {shrunk} · 移除 {removed} · 迭代 {it} · 剩 {len(F2)} 件")
print("→ work/scene_v4.json")
