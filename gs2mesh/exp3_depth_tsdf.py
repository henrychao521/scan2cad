# === 實驗 3:3DGS 渲染深度圖 → TSDF 融合取網格 ===
# 貼進 Colab 一個 cell 執行。需要 A100(或任何 CUDA GPU)。
# 前提上傳:/content/workshop_3dgs.ply 與 /content/colmap_poses.json
#
# 為什麼這樣做:實驗 1/2 證明「用高斯中心點取網格」是死路——中心不落在表面上。
# 正解是用『渲染出來的深度圖』(那才真的是表面)做 TSDF 融合。不必重訓。

import subprocess, sys, json, numpy as np
subprocess.run([sys.executable,"-m","pip","-q","install","gsplat","plyfile","open3d"], check=False)
import torch, gsplat, open3d as o3d
from plyfile import PlyData
dev = "cuda"
print("torch", torch.__version__, "| CUDA", torch.cuda.is_available(), "| gsplat", gsplat.__version__)

# ---------- 讀 3DGS ----------
v = PlyData.read("/content/workshop_3dgs.ply")["vertex"]
means = torch.tensor(np.c_[v["x"],v["y"],v["z"]], dtype=torch.float32, device=dev)
scales = torch.tensor(np.exp(np.c_[v["scale_0"],v["scale_1"],v["scale_2"]]), dtype=torch.float32, device=dev)
quats = torch.tensor(np.c_[v["rot_0"],v["rot_1"],v["rot_2"],v["rot_3"]], dtype=torch.float32, device=dev)
quats = quats / quats.norm(dim=1, keepdim=True)
opac = torch.tensor(1/(1+np.exp(-v["opacity"])), dtype=torch.float32, device=dev)
C0 = 0.28209479177387814
cols = torch.tensor(np.clip(0.5 + C0*np.c_[v["f_dc_0"],v["f_dc_1"],v["f_dc_2"]],0,1), dtype=torch.float32, device=dev)
print(f"高斯 {len(means):,}")

# ---------- 讀相機 ----------
D = json.load(open("/content/colmap_poses.json"))
cam = list(D["cameras"].values())[0]
W, H = cam["w"], cam["h"]
fx, fy, cx, cy = cam["params"][:4]
K = torch.tensor([[fx,0,cx],[0,fy,cy],[0,0,1]], dtype=torch.float32, device=dev)

def q2R(q):
    w,x,y,z = q
    return np.array([[1-2*(y*y+z*z),2*(x*y-w*z),2*(x*z+w*y)],
                     [2*(x*y+w*z),1-2*(x*x+z*z),2*(y*z-w*x)],
                     [2*(x*z-w*y),2*(y*z+w*x),1-2*(x*x+y*y)]])

imgs = D["images"]
print(f"相機 {len(imgs)} 個, {W}x{H}, fx={fx:.1f} fy={fy:.1f}")

# ---------- TSDF 體積 ----------
# voxel 5mm:房間 9×3×13m 用得起,足夠解析桌面/牆面
vol = o3d.pipelines.integration.ScalableTSDFVolume(
    voxel_length=0.005, sdf_trunc=0.02,
    color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8)
intr = o3d.camera.PinholeCameraIntrinsic(W, H, fx, fy, cx, cy)

STRIDE = 1          # 每張都用;若 OOM 或太慢改 2
DEPTH_MAX = 12.0    # 超過視為背景,不融合

for i, im in enumerate(imgs[::STRIDE]):
    R = q2R(im["qvec"]); t = np.array(im["tvec"])
    w2c = np.eye(4); w2c[:3,:3] = R; w2c[:3,3] = t
    viewmat = torch.tensor(w2c, dtype=torch.float32, device=dev)[None]

    with torch.no_grad():
        out, alpha, _ = gsplat.rasterization(
            means, quats, scales, opac, cols,
            viewmat, K[None], W, H,
            render_mode="RGB+ED")      # ED = expected depth
    rgb = (out[0,...,:3].clamp(0,1)*255).byte().cpu().numpy()
    dep = out[0,...,3].cpu().numpy().astype(np.float32)
    dep[(dep > DEPTH_MAX) | (alpha[0,...,0].cpu().numpy() < 0.5)] = 0   # 濾背景/低覆蓋

    rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
        o3d.geometry.Image(np.ascontiguousarray(rgb)),
        o3d.geometry.Image(dep),
        depth_scale=1.0, depth_trunc=DEPTH_MAX, convert_rgb_to_intensity=False)
    vol.integrate(rgbd, intr, w2c)
    if i % 50 == 0: print(f"  融合 {i}/{len(imgs)//STRIDE} …")

print("TSDF 融合完成,取網格…")
mesh = vol.extract_triangle_mesh()
mesh.compute_vertex_normals()
o3d.io.write_triangle_mesh("exp3_tsdf.obj", mesh)
print(f"完成:{len(mesh.vertices):,} 頂點 {len(mesh.triangles):,} 面")
from google.colab import files
files.download("exp3_tsdf.obj")
