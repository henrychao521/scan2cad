# === gs2mesh 一格版：貼進 Colab 一個 cell,按執行即可 ===
# 前提:workshop_3dgs.ply 已上傳到 /content/, 執行階段 = A100
import subprocess, sys
subprocess.run([sys.executable,"-m","pip","-q","install","plyfile","open3d"])
import numpy as np, open3d as o3d
from plyfile import PlyData
print("open3d", o3d.__version__, "| CUDA:", o3d.core.cuda.is_available())

PLY = "/content/workshop_3dgs.ply"
OPACITY_MIN, SCALE_MAX = 0.3, 0.3

v = PlyData.read(PLY)["vertex"]
xyz = np.c_[v["x"], v["y"], v["z"]].astype(np.float64)
C0 = 0.28209479177387814
rgb = np.clip(0.5 + C0*np.c_[v["f_dc_0"],v["f_dc_1"],v["f_dc_2"]], 0, 1)
opacity = 1/(1+np.exp(-v["opacity"]))
scale = np.exp(np.c_[v["scale_0"],v["scale_1"],v["scale_2"]]).max(1)
keep = (opacity>OPACITY_MIN) & (scale<SCALE_MAX)
xyz, rgb = xyz[keep], rgb[keep]
print(f"總高斯 {len(keep):,} -> 濾後 {len(xyz):,} ({keep.mean()*100:.1f}%)")

pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(xyz)
pcd.colors = o3d.utility.Vector3dVector(rgb)
pcd.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
pcd.orient_normals_consistent_tangent_plane(30)
print("法向估計完成,開始 Poisson 取網格(最久,約1-3分鐘)...")

mesh, dens = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=10, n_threads=-1)
mesh.remove_vertices_by_mask(np.asarray(dens) < np.quantile(dens, 0.05))
mesh.remove_duplicated_vertices(); mesh.remove_degenerate_triangles()
mesh.remove_unreferenced_vertices()
mesh = mesh.filter_smooth_taubin(number_of_iterations=5)
mesh.compute_vertex_normals()
print(f"完成:{len(mesh.vertices):,} 頂點 {len(mesh.triangles):,} 面")

o3d.io.write_triangle_mesh("workshop_mesh.obj", mesh)
o3d.io.write_triangle_mesh("workshop_mesh.ply", mesh)
from google.colab import files
files.download("workshop_mesh.obj")
print(">>> 完成,workshop_mesh.obj 開始下載")
