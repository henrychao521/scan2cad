#!/usr/bin/env python3
"""Phase 3 合併: scene_v2(已知+發掘) + vlm_objects.json → scene_v3.json
- 用 VLM 分析替 discovered 物件命名(語意升級)
- 加入頂視幾何抓不到的 wall_items / ceiling_items(牆掛/天花板新物件)
"""
import json, os, math
s = json.load(open("work/scene_v2.json"))
v = json.load(open("work/vlm_objects.json"))

def obb_box(cx, cz, w, d, ang_deg=0.0):
    a = math.radians(ang_deg); ca, sa = math.cos(a), math.sin(a)
    corners = [(-w/2, -d/2), (w/2, -d/2), (w/2, d/2), (-w/2, d/2)]
    return [[round(cx + x*ca - z*sa, 3), round(cz + x*sa + z*ca, 3)] for x, z in corners]

# 替 discovered 命名
disc_idx = 0
relabel = v.get("relabel_discovered", {})
for o in s["furniture"]:
    if o.get("src") == "discovered":
        key = str(disc_idx)
        if key in relabel:
            o["label"] = relabel[key]
            o["src"] = "discovered+vlm"
        disc_idx += 1

# VLM 機台(落地) → 併入家具
for m in v.get("machines", []):
    s["furniture"].append({
        "box": obb_box(m["cx"], m["cz"], m["w"], m["d"], m.get("ang", 0)),
        "cx": m["cx"], "cz": m["cz"], "w": m["w"], "d": m["d"], "h": m["h"],
        "label": m["label"], "src": "vlm", "h_src": "vlm標準尺寸", "conf": m.get("conf")})

s["wall_items"] = v.get("wall_items", [])
s["ceiling_items"] = v.get("ceiling_items", [])
s["vlm_source"] = v.get("source")
s["vlm_categories"] = v.get("identified_categories", [])

json.dump(s, open("work/scene_v3.json", "w"), ensure_ascii=False, indent=1)
n_known = sum(1 for o in s["furniture"] if o.get("src") in (None, "arch"))
n_disc = sum(1 for o in s["furniture"] if o.get("src", "").startswith("discovered"))
n_wall = len(s["wall_items"]); n_ceil = len(s["ceiling_items"])
print(f"scene_v3: 已知家具 {n_known} + 發掘 {n_disc} + 牆掛 {n_wall} + 天花 {n_ceil}"
      f" + 燈 {len(s['lights'])}  = 可繪製 {n_known+n_disc+n_wall+n_ceil+len(s['lights'])} 件")
print(f"VLM 命名: {[o['label'] for o in s['furniture'] if o.get('src','')=='discovered+vlm']}")
print(f"VLM 新增牆掛: {[o['label'] for o in s['wall_items']]}")
print(f"VLM 新增天花: {[o['label'] for o in s['ceiling_items']]}")
