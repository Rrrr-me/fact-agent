import bpy
import math
from mathutils import Vector

# Clear the default scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 900
scene.render.fps = 30

# Materials
def make_material(name, color, emission=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = 0.65

    if emission > 0:
        shader.inputs["Emission Color"].default_value = (*color, 1)
        shader.inputs["Emission Strength"].default_value = emission

    mat.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return mat

ground_mat = make_material("Dark forest ground", (0.018, 0.035, 0.045))
tree_mat = make_material("Shadow trees", (0.012, 0.025, 0.035))
orb_mat = make_material("Mysterious blue glow", (0.05, 0.55, 1.0), 5)
ring_mat = make_material("Ancient silver rings", (0.25, 0.55, 0.75), 1)

# Ground
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
ground = bpy.context.object
ground.name = "Forest floor"
ground.data.materials.append(ground_mat)

# Trees on both sides of the path
for side in (-1, 1):
    for i in range(9):
        y = -2 + i * 2.5
        x = side * (3.5 + (i % 3) * 0.7)

        bpy.ops.mesh.primitive_cone_add(
            vertices=8, radius1=0.35, radius2=0.12,
            depth=5, location=(x, y, 2.5)
        )
        trunk = bpy.context.object
        trunk.name = "Dark tree trunk"
        trunk.data.materials.append(tree_mat)

        bpy.ops.mesh.primitive_cone_add(
            vertices=8, radius1=1.25, radius2=0,
            depth=3, location=(x, y, 5.5)
        )
        leaves = bpy.context.object
        leaves.name = "Forest canopy"
        leaves.data.materials.append(tree_mat)

# Glowing mysterious orb
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=32, ring_count=16, radius=0.75,
    location=(0, 0, 2.5)
)
orb = bpy.context.object
orb.name = "Mysterious floating orb"
orb.data.materials.append(orb_mat)

# Floating rings around the orb
for radius in (1.05, 1.35):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=radius,
        minor_radius=0.025,
        major_segments=48,
        minor_segments=8,
        location=(0, 0, 2.5)
    )
    ring = bpy.context.object
    ring.name = "Floating energy ring"
    ring.data.materials.append(ring_mat)
    ring.rotation_euler[0] = math.radians(65)

# Animate the orb
orb.rotation_euler[2] = 0
orb.keyframe_insert(data_path="rotation_euler", frame=1)
orb.rotation_euler[2] = math.tau
orb.keyframe_insert(data_path="rotation_euler", frame=900)

# Camera
bpy.ops.object.camera_add(location=(0, -13, 4.5))
camera = bpy.context.object
camera.name = "Cinematic camera"
target = Vector((0, 0, 2.5))
camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.lens = 35
scene.camera = camera

# Slow camera movement
camera.keyframe_insert(data_path="location", frame=1)
camera.location.y = -10
camera.keyframe_insert(data_path="location", frame=900)

# Lighting
bpy.ops.object.light_add(type='AREA', location=(0, -3, 7))
key_light = bpy.context.object
key_light.data.energy = 900
key_light.data.shape = 'DISK'
key_light.data.size = 5

bpy.ops.object.light_add(type='POINT', location=(0, 0, 3))
orb_light = bpy.context.object
orb_light.data.energy = 180
orb_light.data.color = (0.1, 0.45, 1.0)
orb_light.data.shadow_soft_size = 2

# Dark atmosphere
world = bpy.data.worlds.new("Midnight forest")
scene.world = world
world.use_nodes = True
background = world.node_tree.nodes.get("Background")
background.inputs["Color"].default_value = (0.003, 0.008, 0.02, 1)
background.inputs["Strength"].default_value = 0.25

# Vertical composition
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.resolution_percentage = 100

scene.frame_set(1)
print("FACT AGENT MYSTERY SCENE CREATED")
