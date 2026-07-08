import bpy, math, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
bpy.ops.wm.read_factory_settings(use_empty=True)
try: bpy.ops.wm.stl_import(filepath=os.path.abspath("out/room_cq.stl"))
except Exception: bpy.ops.import_mesh.stl(filepath=os.path.abspath("out/room_cq.stl"))
o = bpy.context.selected_objects[0]
m = bpy.data.materials.new("w"); m.use_nodes = False; m.diffuse_color = (0.55, 0.75, 0.95, 1)
o.data.materials.append(m); o.modifiers.new("wire", "WIREFRAME").thickness = 0.012
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); bpy.context.scene.collection.objects.link(cam)
cam.location = (-9, -12, 7.5); cam.rotation_euler = (math.radians(60), 0, math.radians(-33)); cam.data.lens = 26
bpy.context.scene.camera = cam
sun = bpy.data.objects.new('s', bpy.data.lights.new('s', 'SUN')); bpy.context.scene.collection.objects.link(sun); sun.data.energy = 3
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x = 1200; sc.render.resolution_y = 850
sc.render.filepath = os.path.abspath("out/room_step_wire.png"); bpy.ops.render.render(write_still=True)
print("WIRE OK")
