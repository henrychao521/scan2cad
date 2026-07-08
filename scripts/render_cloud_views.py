#!/usr/bin/env python3
"""渲染乾淨點雲視圖給 VLM 分析(matplotlib 散點, 用真實顏色)。
出: work/view_top.png(俯視標尺), work/view_persp.png(斜視)。
俯視加公尺格線, 讓 VLM 能用格線量測物件。
"""
import sys, os, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
from plyio import read_ply, opacity

s = json.load(open("work/scene.json"))
K = s["K"]; floor_y = s["floor_y_unit"]; R = s["room"]
cols, n = read_ply(s["src_ply"])
x, y, z = cols['x'], cols['y'], cols['z']; op = opacity(cols)
C0 = 0.28209479
rgb = np.clip(np.stack([0.5+cols['f_dc_0']*C0, 0.5+cols['f_dc_1']*C0, 0.5+cols['f_dc_2']*C0], 1), 0, 1)
# 公制座標(y-up)
Xm, Zm = x*K, z*K
Hm = (floor_y - y)*K
keep = (op > 0.3) & (Hm > 0.05) & (Hm < 2.2)
Xm, Zm, Hm, rgb = Xm[keep], Zm[keep], Hm[keep], rgb[keep]
print(f"渲染點 {keep.sum():,}")

# ---- 俯視(公尺格線) ----
fig, ax = plt.subplots(figsize=(9, 10.6))
order = np.argsort(Hm)  # 低到高, 高的畫上面
ax.scatter(Xm[order], Zm[order], c=rgb[order], s=1.2, marker='.', linewidths=0)
ax.set_xticks(np.arange(np.floor(R["x0"]), np.ceil(R["x1"])+1))
ax.set_yticks(np.arange(np.floor(R["z0"]), np.ceil(R["z1"])+1))
ax.grid(True, color='#00ffff', alpha=0.35, lw=0.6)
ax.set_aspect('equal'); ax.set_xlabel("X 寬 (m)"); ax.set_ylabel("Z 深 (m)")
ax.set_title(f"工坊點雲俯視 · 格線=1m · 室內 {R['x1']-R['x0']:.2f}×{R['z1']-R['z0']:.2f}m", fontsize=12)
ax.set_facecolor('#111')
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang TC']
plt.tight_layout(); plt.savefig("work/view_top.png", dpi=110, facecolor='white'); plt.close()

# ---- 斜視(用高度上色的側 3/4) ----
fig = plt.figure(figsize=(11, 7)); ax = fig.add_subplot(111, projection='3d')
sub = np.random.RandomState(0).permutation(len(Xm))[:120000]
ax.scatter(Xm[sub], Zm[sub], Hm[sub], c=rgb[sub], s=1.0, marker='.', linewidths=0)
ax.set_box_aspect((R["x1"]-R["x0"], R["z1"]-R["z0"], 2.0))
ax.view_init(elev=28, azim=-60); ax.set_xlabel("X(m)"); ax.set_ylabel("Z(m)"); ax.set_zlabel("高(m)")
ax.set_title("工坊點雲 3/4 斜視", fontsize=12)
plt.tight_layout(); plt.savefig("work/view_persp.png", dpi=110, facecolor='white'); plt.close()
print("→ work/view_top.png, work/view_persp.png")
