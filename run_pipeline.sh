#!/bin/bash
# scan2cad 全流程: 3DGS 點雲 → 分析 → 幾何發掘 → VLM → 三引擎 CAD → L1/L3 驗證+修正 → 記錄頁
set -e
cd "$(dirname "$0")"
OSC="/Applications/OpenSCAD-2021.01.app/Contents/MacOS/OpenSCAD"
BL="/Applications/Blender.app/Contents/MacOS/Blender"
CQPY="$HOME/3d/cadquery-venv/bin/python"
ST="tools/node_modules/.bin/splat-transform"
PLY="$HOME/x5-roomtour-pages/assets/lt4_defog.compressed.ply"
ARCH="$HOME/x5-roomtour-pages/assets/arch_elements.json"
CAM="--viewall --projection=perspective --colorscheme=Tomorrow --imgsize=1500,1050 --camera=-0.5,0.17,0.6,62,0,28,26"

echo "▸ [0] 解碼 splat → raw 點雲";          [ -f work/lt4_raw.ply ] || "$ST" "$PLY" work/lt4_raw.ply
echo "▸ [1] 分析已知+量高度 → scene.json";    python3 scripts/analyze_scene.py work/lt4_raw.ply "$ARCH" work/scene.json
echo "▸ [2] 幾何發掘 → scene_v2";             python3 scripts/discover_objects.py work/scene.json
echo "▸ [3] VLM 合併 → scene_v3";             python3 scripts/merge_vlm.py
echo "▸ [4] STEP(v3 暫) 供 declash 前 L1";    "$CQPY" scripts/emit_cadquery.py work/scene_v3.json >/dev/null 2>&1 || true
echo "▸ [5] L3 自動修正穿插/出界 → scene_v4"; python3 scripts/declash_scene.py
echo "▸ [6] CadQuery B-Rep→STEP (最終 v4)";   "$CQPY" scripts/emit_cadquery.py work/scene_v4.json 2>/dev/null | grep -v FutureWarning | tail -2
echo "▸ [7] L1/L3 驗證(v4)";                  python3 scripts/verify_scene.py work/scene_v4.json | grep summary
echo "▸ [8] OpenSCAD real+prov";             python3 scripts/emit_openscad.py work/scene_v4.json out/room.scad real >/dev/null; python3 scripts/emit_openscad.py work/scene_v4.json out/room_prov.scad prov >/dev/null
"$OSC" -o out/room_detail.png    $CAM out/room.scad 2>/dev/null
"$OSC" -o out/room_prov_iso.png  $CAM out/room_prov.scad 2>/dev/null
echo "▸ [9] Blender 網格";                   python3 scripts/emit_blender.py work/scene_v4.json real >/dev/null; "$BL" -b -P out/build_blender.py >/dev/null 2>&1 || echo "  (Blender 略過)"
echo "▸ [10] 轉盤 12 幀 + GIF";              mkdir -p work/turn; for a in 0 30 60 90 120 150 180 210 240 270 300 330; do "$OSC" -o work/turn/f_$(printf %03d $a).png --projection=perspective --colorscheme=Tomorrow --imgsize=900,650 --camera=-0.5,0.17,0.7,60,0,$a,26 --viewall out/room.scad 2>/dev/null; done; (convert -delay 14 -loop 0 work/turn/f_*.png work/turntable.gif 2>/dev/null || true)
echo "▸ [11] STEP 線框 + 疊圖 + 點雲視圖";     "$BL" -b -P scripts/_wire.py >/dev/null 2>&1 || true; python3 scripts/verify_overlay.py work/scene_v4.json >/dev/null; python3 scripts/render_cloud_views.py >/dev/null
echo "▸ [11b] 檢索件: 精密鑽床 hero + before + STEP"
cat > work/dp_hero.scad   <<< '$fn=48;
use <../out/furniture_lib.scad>;
color([0.62,0.64,0.68]) drillpress(0.5,0.5,1.55);'
"$OSC" -o work/dp_hero.png   --projection=perspective --colorscheme=Tomorrow --imgsize=700,950 --camera=0,0,0.75,68,0,25,3.0 --viewall work/dp_hero.scad 2>/dev/null
"$OSC" -o work/dp_before.png --projection=perspective --colorscheme=Tomorrow --imgsize=700,950 --camera=0,0,0.75,68,0,25,3.0 --viewall scripts/dp_crude.scad 2>/dev/null
"$CQPY" scripts/emit_drillpress_step.py 2>/dev/null | grep -v FutureWarning | tail -1
echo "▸ [12] 對照圖 + 記錄頁";                python3 scripts/make_composites.py; python3 scripts/build_page.py
echo "✓ 完成. 記錄頁 page/scan2cad.html · STEP out/room.step · 場景 work/scene_v4.json"
