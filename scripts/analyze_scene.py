#!/usr/bin/env python3
"""Phase 1 分析: raw 3DGS 點雲(splat 框, y-down) + arch_elements.json
   → 補上每個元件的『高度』與『離地高』→ scene.json (公制, y-up 給建模用)。

座標轉換: 建模用右手 y-up 公制。
  X_m = x_unit * K            (寬, 同 arch)
  Y_m = (floor_y - y_unit)*K  (高, 離地; y-down→y-up)
  Z_m = z_unit * K            (深, 同 arch)
arch_elements 的 room/furniture 已是公制(x,z), 這裡只補 y(高).
"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from plyio import read_ply, opacity, luminance

PLY   = sys.argv[1] if len(sys.argv) > 1 else "work/lt4_raw.ply"
ARCH  = sys.argv[2] if len(sys.argv) > 2 else "/Users/henry/x5-roomtour-pages/assets/arch_elements.json"
OUT   = sys.argv[3] if len(sys.argv) > 3 else "work/scene.json"
OPMIN = 0.25

arch = json.load(open(ARCH))
K = arch["k"]
cols, n = read_ply(PLY)
x, y, z = cols['x'], cols['y'], cols['z']
op = opacity(cols); lum = luminance(cols)
keep = op > OPMIN
x, y, z, lum = x[keep], y[keep], z[keep], lum[keep]
print(f"點數 {n:,} → 保留(op>{OPMIN}) {keep.sum():,}")

# ---- 地板: XZ 覆蓋最廣的水平帶(取大y側, y-down 地板在大y) ----
nb = 80
ye = np.linspace(y.min(), y.max(), nb+1); yc = (ye[:-1]+ye[1:])/2
gx = ((x-x.min())/np.ptp(x)*40).astype(int).clip(0,39)
gz = ((z-z.min())/np.ptp(z)*40).astype(int).clip(0,39)
yb = np.clip(np.digitize(y, ye)-1, 0, nb-1)
cov = np.zeros(nb)
for b in range(nb):
    m = yb == b
    if m.sum() < 50: continue
    cov[b] = len(set(zip(gx[m].tolist(), gz[m].tolist())))
cov /= cov.max()
# 地板 = 下半(大y)覆蓋最高帶
lower = yc > np.median(yc)
floor_y = float(yc[np.argmax(cov * lower)])
# 天花板: 點稀疏, 覆蓋法失效 → 取頂端 2% 分位(掃到的最高處)。
# 對照 build_arch_plan 慣例(燈帶=floor-2.3單位)取較大者, 避免掃描未達真天花板時低估。
top_y = float(np.percentile(y, 2.0))
ceil_meas = (floor_y - top_y) * K
ceil_arch = 2.3 * K                       # build_arch_plan 的燈帶假設(≈1.98m)
ceil_h_m = round(max(ceil_meas, ceil_arch), 2)
print(f"floor_y={floor_y:+.3f} 單位  top2%_y={top_y:+.3f}  量測淨高={ceil_meas:.2f}m / arch假設={ceil_arch:.2f}m → 採 {ceil_h_m}m")

def height_in_footprint(cx_m, cz_m, w_m, d_m, ang_deg=0.0, pct=95, shrink=0.7):
    """在(公制中心±足跡)內取點, 回傳頂面離地高(m) 與 點數。足跡略縮避免夾到鄰件/地板。"""
    cxu, czu = cx_m/K, cz_m/K
    hw, hd = (w_m*shrink/2)/K, (d_m*shrink/2)/K
    th = np.radians(ang_deg)
    dx, dz = x-cxu, z-czu
    # 旋轉到物件座標
    lx =  dx*np.cos(th) + dz*np.sin(th)
    lz = -dx*np.sin(th) + dz*np.cos(th)
    m = (np.abs(lx) < hw) & (np.abs(lz) < hd) & (y < floor_y-0.02)  # 地板以上
    if m.sum() < 30:
        return None, int(m.sum())
    hgt = (floor_y - y[m]) * K              # 離地高(m)
    top = float(np.percentile(hgt, pct))
    return round(top, 2), int(m.sum())

# ---- 家具/機台高度 ----
HPRIOR = {"工作檯(連排)":0.85, "工作桌":0.75, "邊檯/櫃":0.9}
furn = []
for i, o in enumerate(arch["furniture"]):
    ang = o.get("ang", 0.0)
    h, cnt = height_in_footprint(o["cx"], o["cz"], o["w"], o["d"], ang)
    src = "cloud"
    if h is None or not (0.25 <= h <= 2.0):
        h = HPRIOR.get(o["label"], 0.8); src = "prior"
    furn.append({**o, "h": h, "h_src": src, "pts": cnt})
    print(f"  家具#{i} {o['label']:8s} {o['w']:.2f}×{o['d']:.2f}m  高={h:.2f}m ({src}, {cnt}pt)")

scene = {
    "unit": "m", "frame": "y-up-right-handed", "K": K, "floor_y_unit": floor_y,
    "src_ply": os.path.abspath(PLY), "src_arch": os.path.abspath(ARCH),
    "room": arch["room"], "wall_t": arch.get("wall_t", 0.15),
    "ceiling_h": ceil_h_m,
    "door": arch.get("door"), "windows": arch.get("windows"),
    "blackboard": arch.get("blackboard"), "lights": arch.get("lights", []),
    "furniture": furn,
    "notes": "高度由點雲足跡量測(op>%.2f); ceiling 為掃到淨高, 相機視角可能未含完整天花板(±10%%)." % OPMIN,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(scene, open(OUT, "w"), ensure_ascii=False, indent=1)
print(f"\n→ {OUT}  (room {arch['room']['x1']-arch['room']['x0']:.2f}×{arch['room']['z1']-arch['room']['z0']:.2f}m, 淨高 {ceil_h_m}m, 家具 {len(furn)})")
