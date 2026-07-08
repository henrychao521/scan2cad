# scan2cad — 3DGS 掃描 → 自動 CAD 重繪

把教室／工坊的 **3DGS 高斯潑濺掃描**，自動分析出物件與空間尺寸，再用**三套建模軟體（OpenSCAD／Blender／CadQuery）自動重繪**成參數化、可製造、通過裝配驗證的模型。

串接兩套系統：**x5-roomtour**（把真實空間掃成 3DGS）＋ **MCL39**（文字→CAD＋L1–L5 驗證）。

👉 **開發全記錄與圖片**：https://henrychao521.github.io/scan2cad/

## 管線（`bash run_pipeline.sh` 一鍵，約 11 秒可重現）

```
3DGS 壓縮 splat
  └ 解碼 → raw 點雲(公制對齊, k=0.859 m/單位)
    ① 分析已知(arch_elements.json) + 回點雲量高度      → 8 件
    ② 幾何發掘(占據分群, 侵蝕分裂)                      → +6 件
    ③ VLM 物件分析(環景辨識+標準尺寸測量, 牆掛/天花板)  → +5 件
    ④ 生成 CAD: OpenSCAD(CSG) / Blender(Mesh) / CadQuery(B-Rep→STEP)
    ⑤ L1(實體 isValid) / L3(裝配穿插) 驗證 + 自動修正
```

工坊成果：室內 8.82×10.48×1.98m、92m²、**21 件重繪物件**、L1·L3 通過、三引擎一致。

## 主要檔案

| 路徑 | 說明 |
|---|---|
| `run_pipeline.sh` | 全流程一鍵 |
| `scripts/analyze_scene.py` | 點雲量高度 + arch → scene.json |
| `scripts/discover_objects.py` | 幾何發掘新物件 |
| `scripts/merge_vlm.py` | VLM 物件合併 |
| `scripts/emit_openscad.py` + `out/furniture_lib.scad` | OpenSCAD 細緻家具 |
| `scripts/emit_blender.py` | Blender bpy |
| `scripts/emit_cadquery.py` | CadQuery B-Rep → STEP |
| `scripts/verify_scene.py` + `declash_scene.py` | L1/L3 驗證 + 自動修正 |
| `scripts/emit_drillpress_step.py` | 檢索件：精密鑽床 B-Rep |
| `docs/` | 開發全記錄公開站（GitHub Pages） |

## 依賴

- Python 3（numpy / scipy / opencv-python / matplotlib / Pillow）
- `@playcanvas/splat-transform`（npm；解碼壓縮 splat）
- OpenSCAD、Blender（headless 算圖）
- CadQuery（`cadquery-venv`；B-Rep / STEP）

## 說明

- 尺寸為 3DGS 管長標定＋點雲量測（±10%）；淨高為「相機掃到的高度」，可能未含真天花板。
- 公開站的真實工坊環景照已**去識別化模糊**，以保護入鏡人員；未模糊原圖不入版控。
- 誠實界線：box 模型抓大件家具/空間；特定機台的精密曲面/機構用**檢索**（擺入精密參數化件），非重建。

---
🤖 開發過程見 [開發全記錄](https://henrychao521.github.io/scan2cad/)
