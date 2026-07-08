#!/usr/bin/env python3
"""R4: scene_v3.json 家具 OBB → 雷切板件分解(scan2lasercut)。

把掃描重繪的家具方塊,拆成可雷切的縮尺模型板件:
  開頂盒 5 片 — 前/後(垂直邊母槽)、左/右(垂直邊公榫)、底(四邊榫舌)。
  垂直角=指接榫;底板=槽榫;三種接合共用同一分段函數,公母必對合。
輸出:out/lasercut_<label>.dxf(R12,mm)+ out/lasercut_<label>.png 預覽。

概念出處:2026-07-07 教師研習「從 3D 列印到雷射切割」——立體想法拆成一片一片板件。
用法: python3 scripts/emit_lasercut.py work/scene_v3.json --index 4 --scale 10 --t 3
"""
import argparse, json, math, sys
from pathlib import Path

# ── 接合分段:長度 L 切 n(奇數)段,奇數索引段=榫位;首尾段必為平邊(避開轉角) ──
def joints(L, t):
    n = max(3, int(round(L / (2.5 * t))))
    if n % 2 == 0:
        n += 1
    seg = L / n
    return [(i * seg, (i + 1) * seg) for i in range(1, n - 1, 2)]

def edge_path(x0, y0, x1, y1, tabs, depth):
    """從 (x0,y0) 走到 (x1,y1) 的邊,在 tabs 區段向外凸 depth(母槽用負 depth 內凹)。
    僅支援軸對齊邊。回傳不含起點的頂點序列。"""
    horiz = abs(y1 - y0) < 1e-9
    L = abs((x1 - x0) if horiz else (y1 - y0))
    sgn = 1 if ((x1 > x0) if horiz else (y1 > y0)) else -1
    # 外法線 = 行進方向順時針轉 90°:(dx,dy)→(dy,-dx)(逆時針多邊形的外側)
    nx, ny = ((0, -sgn) if horiz else (sgn, 0))
    pts = []
    for a, b in tabs:
        pa = (x0 + sgn * a, y0) if horiz else (x0, y0 + sgn * a)
        pb = (x0 + sgn * b, y0) if horiz else (x0, y0 + sgn * b)
        pts += [pa, (pa[0] + nx * depth, pa[1] + ny * depth),
                (pb[0] + nx * depth, pb[1] + ny * depth), pb]
    pts.append((x1, y1))
    return pts

def panel(w, h, edges):
    """逆時針矩形 (0,0)-(w,h);edges = {'bottom'|'right'|'top'|'left': (tabs, depth)}。"""
    corners = [(0, 0), (w, 0), (w, h), (0, h)]
    names = ["bottom", "right", "top", "left"]
    pts = [corners[0]]
    for i, name in enumerate(names):
        x0, y0 = corners[i]
        x1, y1 = corners[(i + 1) % 4]
        if name in edges:
            tabs, depth = edges[name]
            pts += edge_path(x0, y0, x1, y1, tabs, depth)
        else:
            pts.append((x1, y1))
    return pts[:-1]  # 閉合多邊形,去重終點

def obb_dims(o):
    b = o["box"]
    e1 = math.hypot(b[1][0] - b[0][0], b[1][1] - b[0][1])
    e2 = math.hypot(b[2][0] - b[1][0], b[2][1] - b[1][1])
    return max(e1, e2), min(e1, e2), o["h"]

def build_panels(W, D, H, t):
    """回傳 [(名稱, 頂點列表)];尺寸皆 mm、板厚 t。開頂盒。"""
    jH = joints(H, t)            # 垂直角接合(共用)
    jW = joints(W - 2 * t, t)    # 底板 X 向接合
    jD = joints(D - 2 * t, t)    # 底板 Y 向接合
    out = []
    # 前/後 W×H:左右邊母槽(內凹 t),底邊母槽對底板榫(內凹 t,偏移 t)
    fb_bottom = [(a + t, b + t) for a, b in jW]
    for name in ("front", "back"):
        out.append((name, panel(W, H, {
            "left": (jH, -t), "right": (jH, -t), "bottom": (fb_bottom, -t)})))
    # 左/右 (D-2t)×H:左右邊公榫(外凸 t),底邊母槽
    for name in ("left", "right"):
        out.append((name, panel(D - 2 * t, H, {
            "left": (jH, t), "right": (jH, t), "bottom": (jD, -t)})))
    # 底 (W-2t)×(D-2t):四邊榫舌外凸 t
    out.append(("bottom", panel(W - 2 * t, D - 2 * t, {
        "bottom": (jW, t), "top": (jW, t), "left": (jD, t), "right": (jD, t)})))
    return out

def layout(panels, gap=6.0):
    """簡單橫排+換行的排版,回傳 (平移後 panels, 板材外框)。"""
    placed, x, y, row_h, max_w = [], gap, gap, 0, 0
    for name, pts in panels:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        w = max(xs) - min(xs); h = max(ys) - min(ys)
        if x + w + gap > 420 and placed:  # A3-ish 寬度換行
            x, y = gap, y + row_h + gap
            row_h = 0
        dx, dy = x - min(xs), y - min(ys)
        placed.append((name, [(px + dx, py + dy) for px, py in pts]))
        x += w + gap
        row_h = max(row_h, h)
        max_w = max(max_w, x)
    return placed, (max_w + gap, y + row_h + gap)

def write_dxf(placed, path):
    L = ["0", "SECTION", "2", "ENTITIES"]
    for _, pts in placed:
        L += ["0", "POLYLINE", "8", "CUT", "66", "1", "70", "1"]
        for x, y in pts:
            L += ["0", "VERTEX", "8", "CUT", "10", f"{x:.3f}", "20", f"{y:.3f}"]
        L += ["0", "SEQEND"]
    L += ["0", "ENDSEC", "0", "EOF"]
    Path(path).write_text("\n".join(L))

def write_png(placed, sheet, path, scale=4):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False
    Wp, Hp = int(sheet[0] * scale), int(sheet[1] * scale)
    img = Image.new("RGB", (Wp, Hp), (250, 247, 241))
    d = ImageDraw.Draw(img)
    for _, pts in placed:
        poly = [(x * scale, Hp - y * scale) for x, y in pts]
        d.polygon(poly, outline=(15, 90, 168), fill=(222, 232, 244))
    img.save(path)
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--index", type=int, required=True, help="furniture 索引")
    ap.add_argument("--scale", type=float, default=10, help="縮尺分母(10=1:10)")
    ap.add_argument("--t", type=float, default=3.0, help="板厚 mm")
    ap.add_argument("--out", default="out")
    a = ap.parse_args()

    s = json.load(open(a.scene))
    o = s["furniture"][a.index]
    W, D, H = (v * 1000 / a.scale for v in obb_dims(o))
    t = a.t
    if min(W, D, H) < 6 * t:
        sys.exit(f"尺寸過小({W:.0f}×{D:.0f}×{H:.0f}mm):榫齒擺不下,請調小 --scale 或 --t")

    panels = build_panels(W, D, H, t)
    placed, sheet = layout(panels)
    label = o["label"].replace("/", "-").replace("(", "").replace(")", "")
    Path(a.out).mkdir(exist_ok=True)
    dxf = Path(a.out) / f"lasercut_{label}_{a.index}.dxf"
    png = Path(a.out) / f"lasercut_{label}_{a.index}.png"
    write_dxf(placed, dxf)
    has_png = write_png(placed, sheet, png)

    # 自檢:多邊形閉合性(頂點數)與板數
    assert len(placed) == 5, "板數應為 5"
    for name, pts in placed:
        assert len(pts) >= 4 and len(set(pts)) == len(pts), f"{name} 多邊形異常"
    print(f"{o['label']} {obb_dims(o)[0]:.2f}×{obb_dims(o)[1]:.2f}×{obb_dims(o)[2]:.2f}m"
          f" → 1:{a.scale:.0f} 盒 {W:.0f}×{D:.0f}×{H:.0f}mm,t={t}")
    print(f"→ {dxf}(5 片,板材 {sheet[0]:.0f}×{sheet[1]:.0f}mm)"
          + (f"\n→ {png}" if has_png else ""))

if __name__ == "__main__":
    main()
