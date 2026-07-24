#!/usr/bin/env python3
"""固定條件渲染取網格結果,供不同文獻方法並排比對。
用法: blender -b --python render_compare.py -- <mesh.obj> <方法標籤>
輸出: screenshots/<日期>_<方法標籤>_{iso,side}.png (日期由呼叫端傳,見下)
相機/材質/取樣全部固定,才可公平比較。"""
import bpy, sys, mathutils, os
argv = sys.argv[sys.argv.index('--')+1:]
obj_path, tag, datestr = argv[0], argv[1], argv[2]
outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(outdir, exist_ok=True)

def setup(obj_path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.obj_import(filepath=obj_path)
    o=bpy.context.selected_objects[0]
    mat=bpy.data.materials.new("clay"); mat.use_nodes=True
    b=mat.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(0.7,0.7,0.72,1); b.inputs['Roughness'].default_value=0.7
    o.data.materials.clear(); o.data.materials.append(mat)
    corners=[o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
    c=(sum(v.x for v in corners)/8, sum(v.y for v in corners)/8, sum(v.z for v in corners)/8)
    sc=bpy.context.scene
    sun_d=bpy.data.lights.new("S",'SUN'); sun_d.energy=3.5
    sun=bpy.data.objects.new("S",sun_d); sc.collection.objects.link(sun); sun.rotation_euler=(0.6,0.2,0.5)
    sc.world=bpy.data.worlds.new("W"); sc.world.use_nodes=True
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0.6
    sc.render.engine='CYCLES'; sc.cycles.device='GPU'; sc.cycles.samples=48; sc.cycles.use_denoising=True
    sc.render.resolution_x=1000; sc.render.resolution_y=700; sc.render.image_settings.file_format='PNG'
    return sc, c

# 固定兩視角相機位置(相對 bbox 中心的固定偏移)
VIEWS = {"iso": (15,-15,10, 22), "side": (0,-22,1, 28)}
for name,(dx,dy,dz,lens) in VIEWS.items():
    sc,c = setup(obj_path)
    cam_d=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cam_d)
    sc.collection.objects.link(cam); sc.camera=cam; cam_d.lens=lens
    cam.location=(c[0]+dx, c[1]+dy, c[2]+dz)
    dirv=mathutils.Vector(c)-cam.location; cam.rotation_euler=dirv.to_track_quat('-Z','Y').to_euler()
    out=os.path.join(outdir, f"{datestr}_{tag}_{name}.png")
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    print("SAVED", out)
