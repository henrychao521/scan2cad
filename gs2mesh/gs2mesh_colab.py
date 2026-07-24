#!/usr/bin/env python3
# ==============================================================
# 3DGS → 乾淨網格  Colab notebook (以 .py cell 標記,可直接貼進 Colab)
# 來源: animation-research 第 4/5 批 (2DGS/SuGaR/DN-Splatter)
# 目標鏈: 3DGS → 取網格 → (QUADify → OpenSubdiv) → scan2cad CAD
#
# 本機 M4 Max 無 CUDA + open3d 大規模 segfault (實測 139)，故上 Colab。
# 取網格邏輯已在本機小樣本 (2萬點) 驗證正確，此處放大到全場並用 GPU。
# ==============================================================

# %% [markdown]
# ## Cell 0 — 上傳素材
# 把 `工坊_標準3DGS.ply` (62MB, 110萬高斯) 上傳到 Colab，或掛 Drive。

# %% Cell 1 — 環境
# !pip -q install plyfile open3d
# Colab 已有 numpy/scipy。open3d 在 Colab 有 CUDA build。
import numpy as np, open3d as o3d
from plyfile import PlyData
print("open3d", o3d.__version__, "| CUDA:", o3d.core.cuda.is_available())

# %% Cell 2 — 讀 3DGS 並轉點雲 (含飄絲高斯過濾)
# 整場模式 (A100 40GB): 不裁切,全 110 萬高斯
PLY = "工坊_標準3DGS.ply"          # ← 改成你上傳的路徑
OPACITY_MIN = 0.3                   # 濾掉低不透明度的飄絲高斯 (呼應 deneedle 夾針)
SCALE_MAX   = 0.3                   # 濾掉過大的高斯 (通常是背景霧,非表面)
CROP = None                        # 整場; 若要裁局部設 (xmin,xmax,ymin,ymax,zmin,zmax)

ply = PlyData.read(PLY); v = ply["vertex"]
xyz = np.c_[v["x"], v["y"], v["z"]].astype(np.float64)
C0 = 0.28209479177387814
rgb = np.clip(0.5 + C0 * np.c_[v["f_dc_0"], v["f_dc_1"], v["f_dc_2"]], 0, 1)
opacity = 1 / (1 + np.exp(-v["opacity"]))
# scale 存的是 log,取 exp 後看最大軸
scale = np.exp(np.c_[v["scale_0"], v["scale_1"], v["scale_2"]]).max(1)

keep = (opacity > OPACITY_MIN) & (scale < SCALE_MAX)
if CROP:
    x0,x1,y0,y1,z0,z1 = CROP
    keep &= (xyz[:,0]>=x0)&(xyz[:,0]<=x1)&(xyz[:,1]>=y0)&(xyz[:,1]<=y1)&(xyz[:,2]>=z0)&(xyz[:,2]<=z1)
print(f"總高斯 {len(xyz):,} → 濾後 {keep.sum():,} ({keep.mean()*100:.1f}%)")
xyz, rgb = xyz[keep], rgb[keep]

# %% Cell 3 — 取網格 (兩條路線,先跑 A,不滿意再試 B)
pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(xyz)
pcd.colors = o3d.utility.Vector3dVector(rgb)
pcd.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
pcd.orient_normals_consistent_tangent_plane(30)

# --- 路線 A: Poisson (面較完整、會外插補洞,適合牆面/大平面) ---
mesh, dens = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
    pcd, depth=10, n_threads=-1)
mesh.remove_vertices_by_mask(np.asarray(dens) < np.quantile(dens, 0.05))  # 剪假面
print(f"[A] Poisson: {len(mesh.vertices):,} 頂點 {len(mesh.triangles):,} 面")

# --- 路線 B: Ball-pivoting (只連真實點,不外插,幾何最忠實,較易破面) ---
# d = np.mean(pcd.compute_nearest_neighbor_distance())
# mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
#     pcd, o3d.utility.DoubleVector([d, d*2, d*4]))

# %% Cell 4 — 清理 + 匯出
mesh.remove_duplicated_vertices()
mesh.remove_degenerate_triangles()
mesh.remove_unreferenced_vertices()
mesh = mesh.filter_smooth_taubin(number_of_iterations=5)  # Taubin 不縮體積
mesh.compute_vertex_normals()
o3d.io.write_triangle_mesh("workshop_mesh.ply", mesh)
o3d.io.write_triangle_mesh("workshop_mesh.obj", mesh)  # 給 QUADify/Blender
print("已存 workshop_mesh.ply / .obj")

# %% [markdown]
# ## Cell 5 — 下一環 (下載 mesh 回本機接鏈)
# workshop_mesh.obj → 本機:
#   1. QUADify 重拓樸 (quad mesh)  ← 需另一個 repo,見佇列 P1
#   2. Blender subdiv modifier 或 OpenSubdiv → 極限曲面
#   3. 進 scan2cad 幾何清理鏈,對 CAD 重繪
# 先目視檢查 workshop_mesh 的牆面/桌面是否乾淨、有無 3DGS 飄絲殘留成的疙瘩。
