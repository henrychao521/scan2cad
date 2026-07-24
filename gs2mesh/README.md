# 3DGS → 乾淨網格 PoC（scan2cad 幾何清理鏈第一環）

來源：animation-research 佇列 第 4/5 批
- 2DGS (2DGaussianSplatting 2024)：3D 高斯壓成貼表面 2D 圓盤 → TSDF 取網格，幾何最準
- SuGaR (2023)：正則化貼齊 + Poisson 取網格，最快
- DN-Splatter (2024)：手機深度/法向先驗，室內幾何最強

目標鏈：**3DGS → 2D高斯表面 → 取網格 → QUADify 重拓樸 → OpenSubdiv 極限曲面 → CAD**

## 為什麼走 Colab
本機 Mac Studio M4 Max **無 CUDA**。2DGS/SuGaR 的 TSDF/Poisson 取網格步驟需要
CUDA rasterizer（diff-gaussian-rasterization），MPS 跑不動。→ Colab T4/A100。

## 輸入素材（已驗證是真 3DGS）
| 檔案 | 高斯數 | 尺度 | 用途 |
|---|---|---|---|
| `~/Desktop/Blender_3DGS/工坊_標準3DGS.ply` | 1,108,557 | 8.9×3.8×13.4m | 工坊全景,先 PoC 這個 |
| `/Volumes/3D/x5-3dgs/homeec/.../dec.ply` | 2,438,191 | 8.8×5.9×7.7m | homeec 房間,備選 |

⚠ 這是**訓練好的 3DGS ply**（INRIA 格式：scale+rot+SH），不是 COLMAP 點雲。
2DGS 官方 repo 需要「訓練過程」才輸出 2D 高斯；直接吃 3DGS ply 要走
**post-hoc 取網格**路線（見 notebook cell 3 的兩個選項）。

## 執行前要 Henry 確認（GPU 時數）
記憶 [[colab-gsplat-depthreg]] 教訓：Colab 免費版 JIT 編譯 rasterizer 太慢，
正解是預編 wheel 或 Colab Pro。開跑前確認：(a) 用哪個帳號的 Colab、
(b) 免費 T4 還是 Pro A100、(c) 先 PoC 工坊一個**局部區域**（如一面牆+一張桌）
還是整場——整場 110 萬高斯取網格可能爆記憶體。

---

## 2026-07-17 首跑結果：流程通、方法不行（誠實記錄）

**跑通的部分**（基礎設施可重用）：
- Colab Pro+ / A100 / 上傳 62MB ply / 一格版腳本 / 下載 obj / 本機驗證，端到端無阻。
- 產出 `workshop_mesh.obj`：490k 頂點、964k 面、bbox 8.99×3.38×13.17m（尺度對）、
  winding 一致、94% 為單一主殼、碎片濾掉後 52 元件。**數字看起來很健康。**

**但目視是致命的**：算圖兩個角度（`/tmp/mesh_view.png` 斜俯視、`/tmp/mesh_side.png` 側視）
都是**坑疤塊狀物**——沒有平牆、沒有平地、沒有可辨識的桌椅。對 CAD 重繪毫無用處。

**根因（方法錯，非執行錯）**：
我走的是「取高斯中心點 → open3d Poisson」的捷徑，**丟掉了每個高斯的異向協方差
（scale + rotation）**——那正是定義表面朝向與延展的資訊。只用中心點做 Poisson，
等於把一堆有向橢圓盤退化成無向點雲再硬包等值面，必然長成疙瘩。

**這正是佇列指定 2DGS/SuGaR 的原因**：它們把 3D 高斯壓成**貼齊表面的 2D 圓盤**
再做 TSDF 融合，幾何才會平。我的 post-hoc 捷徑是遠比它們粗糙的近似。

**下一步（要真的可用）**：
- 走官方 **2DGS**（`surfel_rasterization` + TSDF）或 **SuGaR**（正則化貼齊 + Poisson）。
  兩者都需要 CUDA rasterizer + 通常要「訓練/微調」階段,不是純 post-hoc。
- 或 **DN-Splatter**（手機深度先驗）——但 x5 的 ply 已是訓練好的,要回到 nerfstudio 生態重跑。
- 結論:**乾淨網格拿不到捷徑**,要嘛上真的 2DGS 訓練管線,要嘛這條鏈暫時卡住。

---

## 方法比對表（同一輸入 workshop_3dgs.ply,不同取網格法）

> 每跑一個新文獻方法就追加一列 + 存渲染到 `screenshots/日期_方法_視角.png`。
> 渲染條件固定:clay 材質、同相機(iso 斜俯 + side 側視)、Cycles 48spp,才可公平並排。

| 方法 | 日期 | 頂點/面 | 主殼佔比 | 目視(牆面平整?) | 可用於CAD? | 截圖 |
|---|---|---|---|---|---|---|
| **exp1 naive Poisson**(中心點) | 2026-07-17 | 490k/964k | 94% | ✗ 坑疤塊狀 | ✗ | `screenshots/2026-07-17_naive-poisson_{iso,side}.png` |
| **exp2 有向法線 Poisson**(中心點+協方差法線) | 2026-07-17 | 506k/997k | 94% | ✗ 仍坑疤(更海綿) | ✗ | `screenshots/2026-07-17_exp2-oriented_{iso,side}.png` |
| exp3 深度圖 TSDF(3DGS渲染深度) | 待做 | — | — | — | — | — |
| 2DGS 重訓 | 待做 | — | — | — | — | — |
| SuGaR | 待做 | — | — | — | — | — |

> **exp1+2 共同結論**:post-hoc 用高斯中心點取網格是死路——中心不落在表面上,
> 法線再準也沒用。正解要用**渲染深度圖**(exp3)或**重訓**(2DGS)。詳見 EXPERIMENTS.md。

### 基準渲染(naive Poisson,對 CAD 不可用,留作反面對照)
- 斜俯視:`screenshots/2026-07-17_naive-poisson_iso.png`
- 側視:`screenshots/2026-07-17_naive-poisson_side.png`
- 兩圖皆為坑疤等值面,證實「只用高斯中心 Poisson」的下限。將來 2DGS/SuGaR 的
  同視角渲染應明顯平整,可一眼看出改善幅度。

### 渲染腳本(重現用)
`/tmp/render_mesh.py`(iso)與 `/tmp/render_side.py`(side)——已在 gs2mesh 目錄外,
下次要對新方法出同視角圖,把這兩支複製進專案並固定相機參數。
