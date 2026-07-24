# === 實驗 4:官方 2DGS 從影像重訓 → TSDF 取網格 ===
# 貼進 Colab 一個 cell。需要 A100。約 30-60 分鐘(7000 iter)。
# 前提上傳:/content/workshop_colmap.zip (154MB, 含 images/ 與 sparse/)
#
# 與實驗 3 的差別:exp3 用「已訓練的 3DGS」渲染深度;exp4 從頭訓練 2D 高斯,
# 訓練時就把高斯壓成貼齊表面的圓盤(加了法線一致性與深度扭曲正則),幾何理論最準。

import os, subprocess, sys
os.chdir("/content")

# ---------- 解壓資料 ----------
if not os.path.exists("/content/data/images"):
    os.makedirs("/content/data", exist_ok=True)
    subprocess.run(["unzip","-q","-o","/content/workshop_colmap.zip","-d","/content/data"], check=True)
print("資料:", os.listdir("/content/data"))
print("影像數:", len(os.listdir("/content/data/images")))

# ---------- 取得 2DGS ----------
if not os.path.exists("/content/2d-gaussian-splatting"):
    subprocess.run(["git","clone","--recursive",
                    "https://github.com/hbb1/2d-gaussian-splatting.git"], check=True)
os.chdir("/content/2d-gaussian-splatting")

# ---------- 裝相依 ----------
# 坑(記憶 colab-gsplat-depthreg):自行編譯 CUDA kernel 在 Colab 很慢。
# 2DGS 的 submodules 必須編,沒有預編 wheel。A100 上約 3-8 分鐘,可接受。
subprocess.run([sys.executable,"-m","pip","-q","install",
                "submodules/diff-surfel-rasterization",
                "submodules/simple-knn",
                "open3d","plyfile","tqdm","opencv-python-headless"], check=False)

# ---------- 訓練 ----------
# 7000 iter 已足夠看幾何品質(官方預設 30000,但我們是驗證方法不是出成品)
subprocess.run([sys.executable,"train.py",
                "-s","/content/data",
                "-m","/content/out_2dgs",
                "--iterations","7000",
                "-r","2"], check=True)      # -r 2 = 影像降半解析度,省時省記憶體

# ---------- 取網格(官方 TSDF 融合) ----------
subprocess.run([sys.executable,"render.py",
                "-s","/content/data",
                "-m","/content/out_2dgs",
                "--iteration","7000",
                "--skip_train","--skip_test",
                "--mesh_res","1024"], check=True)

# ---------- 找出網格並下載 ----------
import glob
cands = glob.glob("/content/out_2dgs/**/*.ply", recursive=True)
cands = [c for c in cands if "fuse" in c.lower() or "mesh" in c.lower()]
print("產出:", cands)
if cands:
    import shutil
    shutil.copy(cands[0], "/content/exp4_2dgs.ply")
    from google.colab import files
    files.download("/content/exp4_2dgs.ply")
else:
    print("找不到融合網格,列出 out_2dgs 內容:")
    for r,d,f in os.walk("/content/out_2dgs"):
        for x in f[:20]: print(" ", os.path.join(r,x))
