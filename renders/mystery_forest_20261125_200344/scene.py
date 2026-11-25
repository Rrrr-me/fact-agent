# Auto-generated Mystery Forest Scene
# Based on original first_scene.py

import bpy
import math
from mathutils import Vector, Euler
import random

# ============================================================
# SCENE SETUP
# ============================================================

# Clear existing scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 10
scene.render.fps = 30

# Render settings
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.cycles.device = 'GPU'

scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100

scene.render.image_settings.file_format = 'PNG'

# ============================================================
# MATERIALS
# ============================================================

def make_material(name, color, roughness=0.5, metallic=0, emission=0, emission_color=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = (*color, 1)
    principled.inputs['Roughness'].default_value = roughness
    principled.inputs['Metallic'].default_value = metallic

    if emission > 0:
        principled.inputs['Emission Color'].default_value = (*(emission_color or color), 1)
        principled.inputs['Emission Strength'].default_value = emission

    mat.node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    return mat

# ============================================================
# WORLD ENVIRONMENT
# ============================================================

# Solid color background
world = bpy.data.worlds.new('Background')
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
bg.inputs['Color'].default_value = (0.01, 0.01, 0.02, 1)
bg.inputs['Strength'].default_value = 0.1

# ============================================================
# CAMERA
# ============================================================

bpy.ops.object.camera_add(location=(0, -13, 4.5))
camera = bpy.context.object
camera.name = 'Main_Camera'
camera.data.lens = 35

# Point camera at origin
target = Vector((0, 0, 0))
camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = camera

# ============================================================
# LIGHTING
# ============================================================

bpy.ops.object.light_add(type='AREA', location=(0, -3, 7))
key_light = bpy.context.object
key_light.name = 'Key_Light'
key_light.data.energy = 900
key_light.data.shape = 'DISK'
key_light.data.size = 5

bpy.ops.object.light_add(type='AREA', location=(5, 3, 4))
fill_light = bpy.context.object
fill_light.name = 'Fill_Light'
fill_light.data.energy = 300
fill_light.data.shape = 'RECTANGLE'
fill_light.data.size = 4

bpy.ops.object.light_add(type='AREA', location=(-5, -5, 5))
rim_light = bpy.context.object
rim_light.name = 'Rim_Light'
rim_light.data.energy = 200
rim_light.data.shape = 'RECTANGLE'
rim_light.data.size = 3

# ============================================================
# MYSTERY FOREST CONTENT
# ============================================================

ground_mat = make_material('Dark forest ground', (0.018, 0.035, 0.045))
tree_mat = make_material('Shadow trees', (0.012, 0.025, 0.035))
orb_mat = make_material('Mysterious blue glow', (0.05, 0.55, 1.0), emission=5)
ring_mat = make_material('Ancient silver rings', (0.25, 0.55, 0.75), emission=1)

# Ground plane
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
ground = bpy.context.object
ground.name = 'Forest floor'
ground.data.materials.append(ground_mat)

# Tree rows
for side in (-1, 1):
    for i in range(9):
        y = -2 + i * 2.5
        x = side * (3.5 + (i % 3) * 0.7)
        
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.35, radius2=0.12, depth=5, location=(x, y, 2.5))
        trunk = bpy.context.object
        trunk.name = 'Dark tree trunk'
        trunk.data.materials.append(tree_mat)
        
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.25, radius2=0, depth=3, location=(x, y, 5.5))
        leaves = bpy.context.object
        leaves.name = 'Forest canopy'
        leaves.data.materials.append(tree_mat)

# Glowing orb
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.75, location=(0, 0, 2.5))
orb = bpy.context.object
orb.name = 'Mysterious floating orb'
orb.data.materials.append(orb_mat)

# Floating rings
for radius in (1.05, 1.35):
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=0.025, major_segments=48, minor_segments=8, location=(0, 0, 2.5))
    ring = bpy.context.object
    ring.name = 'Floating energy ring'
    ring.data.materials.append(ring_mat)
    ring.rotation_euler[0] = math.radians(65)

# Orb rotation animation
orb.rotation_euler[2] = 0
orb.keyframe_insert(data_path='rotation_euler', frame=1)
orb.rotation_euler[2] = math.tau
orb.keyframe_insert(data_path='rotation_euler', frame=10)

# Camera dolly
camera = bpy.data.objects['Main_Camera']
camera.keyframe_insert(data_path='location', frame=1)
camera.location.y = -10
camera.keyframe_insert(data_path='location', frame=10)

scene.frame_set(1)
print("MYSTERY FOREST SCENE CREATED")