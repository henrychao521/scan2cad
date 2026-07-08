#!/usr/bin/env python3
"""Phase 4 驗證: CAD 物件框疊回點雲俯視 → 尺寸吻合 + 覆蓋率。
出 work/verify_overlay.png + work/verify_metrics.json。
覆蓋率 = 佔據點雲格中落在任一物件框內的比例(模型代表了多少掃到的東西)。
"""
import sys, os, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
from matplotlib.path import Path as MPath
sys.path.insert(0, os.path.dirname(__file__))
from plyio import read_ply, opacity

s = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "work/scene_v3.json"))
K = s["K"]; floor_y = s["floor_y_unit"]; R = s["room"]
X0, X1, Z0, Z1 = R["x0"], R["x1"], R["z0"], R["z1"]
cols, n = read_ply(s["src_ply"])
x, y, z = cols['x'], cols['y'], cols['z']; op = opacity(cols)
hgt = (floor_y - y) * K
band = (hgt > 0.12) & (hgt < 2.1) & (op > 0.25)
Xm, Zm = x[band]*K, z[band]*K

# 佔據網格(公制 5cm)
CELL = 0.05
W = int((X1-X0)/CELL)+2; H = int((Z1-Z0)/CELL)+2
gi = ((Xm-X0)/CELL).astype(int).clip(0, W-1); gj = ((Zm-Z0)/CELL).astype(int).clip(0, H-1)
G = np.zeros((H, W)); np.add.at(G, (gj, gi), 1.0)
occ = G > np.quantile(G[G > 0], 0.5)

# 物件框遮罩
import matplotlib.path as mpath
gy, gx = np.mgrid[0:H, 0:W]
cellpts = np.stack([gx.ravel()*CELL+X0, gy.ravel()*CELL+Z0], 1)
covered = np.zeros(H*W, bool)
for o in s["furniture"]:
    covered |= mpath.Path(np.array(o["box"])).contains_points(cellpts)
covered = covered.reshape(H, W)
occ_cells = occ.sum()
cov_ratio = float((occ & covered).sum() / max(occ_cells, 1))

metrics = {
    "room_dims_m": [round(X1-X0, 2), round(Z1-Z0, 2), s["ceiling_h"]],
    "room_area_m2": round((X1-X0)*(Z1-Z0), 1),
    "n_objects_total": len(s["furniture"]) + len(s.get("wall_items", [])) + len(s.get("ceiling_items", [])),
    "n_arch": sum(1 for o in s["furniture"] if o.get("src", "arch") in ("arch", None)),
    "n_discovered": sum(1 for o in s["furniture"] if str(o.get("src", "")).startswith("discovered")),
    "n_vlm": len(s.get("wall_items", [])) + len(s.get("ceiling_items", [])),
    "occupied_footprint_coverage": round(cov_ratio, 3),
    "note": "覆蓋率=站立物點雲佔據格落在物件框內比例; 未覆蓋=牆邊/散落未建模的雜項",
}
json.dump(metrics, open("work/verify_metrics.json", "w"), ensure_ascii=False, indent=1)

# 疊圖
fig, ax = plt.subplots(figsize=(9, 10.6))
ax.imshow(occ, extent=[X0, X1, Z1, Z0], cmap='Greys', alpha=0.55, aspect='equal')
ax.add_patch(Rectangle((X0, Z0), X1-X0, Z1-Z0, fill=False, ec='#111', lw=2))
CMAP = {"arch": "#25c04a", "discovered": "#ff8c1a", "discovered+vlm": "#ff8c1a"}
for o in s["furniture"]:
    c = CMAP.get(o.get("src", "arch"), "#25c04a")
    ax.add_patch(Polygon(np.array(o["box"]), closed=True, fill=True, fc=c, ec='#222', lw=1, alpha=0.5))
    ax.text(o["cx"], o["cz"], o["label"], ha='center', va='center', fontsize=6, color='#111')
for o in s.get("wall_items", []):
    a, b = o["along"]; wall = o["wall"]
    if wall == "x0":   xy, w, h = (X0, a), 0.15, b-a
    elif wall == "x1": xy, w, h = (X1-0.15, a), 0.15, b-a
    elif wall == "z0": xy, w, h = (a, Z0), b-a, 0.15
    else:              xy, w, h = (a, Z1-0.15), b-a, 0.15
    ax.add_patch(Rectangle(xy, w, h, fc='#3a72ff', ec='#1a3', lw=1, alpha=0.8))
    ax.text(xy[0]+w/2, xy[1]+h/2, o["label"], ha='center', va='center', fontsize=5.5, color='#003')
ax.set_xlim(X0-0.6, X1+0.6); ax.set_ylim(Z1+0.6, Z0-0.6); ax.set_aspect('equal')
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang TC']; plt.rcParams['axes.unicode_minus'] = False
ax.set_title(f"CAD 物件框 疊回 點雲俯視佔據\n室內 {X1-X0:.2f}×{Z1-Z0:.2f}m · 佔據覆蓋率 {cov_ratio*100:.0f}% · 綠=已知 橙=發掘 藍=VLM", fontsize=12)
ax.set_xlabel("X 寬 (m)"); ax.set_ylabel("Z 深 (m)")
plt.tight_layout(); plt.savefig("work/verify_overlay.png", dpi=115, facecolor='white'); plt.close()
print(json.dumps(metrics, ensure_ascii=False, indent=1))
print("→ work/verify_overlay.png, verify_metrics.json")
