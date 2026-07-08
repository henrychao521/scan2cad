#!/usr/bin/env python3
"""共用: 讀 raw 3DGS PLY(splat 框, y-down) → dict of columns。
只支援 build_arch_plan / splat-transform 解碼出的 `element vertex` + `property float` 格式。
"""
import numpy as np

def read_ply(src, want=None):
    """回傳 {name: np.float32 array}。want 給定則只留這些欄(省記憶體)。"""
    props = []; n = 0
    with open(src, "rb") as f:
        while True:
            s = f.readline().decode("ascii", "ignore").strip()
            if s.startswith("element vertex"):
                n = int(s.split()[-1])
            elif s.startswith("property float"):
                props.append(s.split()[-1])
            elif s == "end_header":
                break
        d = np.frombuffer(f.read(n * len(props) * 4), dtype="<f4").reshape(n, len(props))
    cols = {k: d[:, props.index(k)] for k in props}
    if want:
        cols = {k: cols[k] for k in want if k in cols}
    return cols, n

def luminance(cols):
    C0 = 0.28209479
    return np.clip(0.299*(0.5+cols['f_dc_0']*C0) + 0.587*(0.5+cols['f_dc_1']*C0)
                   + 0.114*(0.5+cols['f_dc_2']*C0), 0, 1)

def opacity(cols):
    return 1/(1+np.exp(-cols['opacity']))

def find_floor(x, y, z, op):
    """y-down: 地板在 y 較大側的密度峰。取中央 60% 區避免牆。回傳 floor_y(單位)。"""
    cx = (x > np.quantile(x,.2)) & (x < np.quantile(x,.8)) & \
         (z > np.quantile(z,.2)) & (z < np.quantile(z,.8))
    h, e = np.histogram(y[cx], bins=120, weights=op[cx])
    c = (e[:-1]+e[1:])/2
    return float(c[np.argmax(h*(c > np.median(c)))])

if __name__ == "__main__":
    import sys
    cols, n = read_ply(sys.argv[1])
    x, y, z = cols['x'], cols['y'], cols['z']
    op = opacity(cols)
    fl = find_floor(x, y, z, op)
    print(f"點數 {n:,}")
    for a, v in [('x', x), ('y', y), ('z', z)]:
        print(f"  {a}: [{v.min():.3f}, {v.max():.3f}]  span={np.ptp(v):.3f}")
    print(f"  floor_y(單位) ≈ {fl:.4f}")
