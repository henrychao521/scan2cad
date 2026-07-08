#!/usr/bin/env python3
"""對照圖: 真實 vs 重繪 + 三引擎並排 → page/img/cmp_*.png"""
import os
from PIL import Image, ImageDraw, ImageFont
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.makedirs("page/img", exist_ok=True)

def font(sz):
    for p in ["/System/Library/Fonts/PingFang.ttc", "/Library/Fonts/Arial Unicode.ttf",
              "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"]:
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()

def label(im, txt, sz=32, pad=10):
    d = ImageDraw.Draw(im); f = font(sz); w = d.textlength(txt, font=f)
    d.rectangle([0, 0, w+2*pad, sz+2*pad], fill=(20, 22, 28))
    d.text((pad, pad), txt, fill=(255, 180, 80), font=f); return im

def fit(im, W): return im.resize((W, int(im.height*W/im.width)), Image.LANCZOS)

# 也把來源大圖同步到 page/img
sync = {"out/room_detail.png": "page/img/cad_openscad.png",
        "out/room_prov_iso.png": "page/img/cad_prov.png",
        "out/room_blender.png": "page/img/cad_blender.png",
        "work/verify_overlay.png": "page/img/verify.png",
        "work/clash_map.png": "page/img/clash.png",
        "work/turntable.gif": "page/img/turntable.gif",
        "work/discover_debug.png": "page/img/discover.png",
        "work/pano_seg1.png": "page/img/vlm_seg.png"}
for a, b in sync.items():
    if os.path.exists(a):
        if a.endswith(".gif"): __import__("shutil").copy(a, b)
        else: Image.open(a).convert("RGB").save(b)
if not os.path.exists("page/img/pano.png") and os.path.exists("work/real_pano.png"):
    Image.open("work/real_pano.png").convert("RGB").save("page/img/pano.png")

# A: 真實 vs 重繪
pano = fit(Image.open("page/img/pano.png").convert("RGB"), 1400)
hero = fit(Image.open("out/room_detail.png").convert("RGB"), 1400)
label(pano, "真實 3DGS 環景（輸入）", 34); label(hero, "scan2cad 自動重繪（輸出・OpenSCAD）", 34)
A = Image.new("RGB", (1400, pano.height+hero.height+16), (21, 23, 28))
A.paste(pano, (0, 0)); A.paste(hero, (0, pano.height+16)); A.save("page/img/cmp_real_cad.png")

# B: 三引擎
imgs = [("out/room_detail.png", "OpenSCAD（CSG）"), ("out/room_blender.png", "Blender（Mesh）"),
        ("out/room_step_wire.png", "CadQuery（B-Rep→STEP 線框）")]
cells = []
for p, t in imgs:
    if not os.path.exists(p): continue
    im = fit(Image.open(p).convert("RGB"), 700); label(im, t, 26); cells.append(im)
if cells:
    h = max(c.height for c in cells)
    B = Image.new("RGB", (700*len(cells)+12*(len(cells)-1), h), (21, 23, 28))
    for i, c in enumerate(cells): B.paste(c, (i*(700+12), (h-c.height)//2))
    B.save("page/img/cmp_tri_engine.png")

# C: 檢索件 before/after (鑽床)
if os.path.exists("work/dp_before.png") and os.path.exists("work/dp_hero.png"):
    b = Image.open("work/dp_before.png").convert("RGB"); a = Image.open("work/dp_hero.png").convert("RGB")
    label(b, "改造前：粗 primitive", 30, 10)
    label(a, "改造後：精密檢索件", 30, 10)
    C = Image.new("RGB", (b.width+a.width+16, max(b.height, a.height)), (21, 23, 28))
    C.paste(b, (0, 0)); C.paste(a, (b.width+16, 0)); C.save("page/img/retrieval_ba.png")
    a.save("page/img/drillpress_hero.png")
print("→ page/img/cmp_real_cad.png, cmp_tri_engine.png, retrieval_ba.png (+同步來源圖)")
