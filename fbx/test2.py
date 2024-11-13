import os.path
from unreal import *

# Set the import path for spider
spider_fbx_path = r"C:\Users\admin\Desktop\fbx\spider\spider.fbx"
spider_dir = os.path.dirname(spider_fbx_path)

# Create FBX factory
fbx_factory = FbxFactory()
if fbx_factory is None:
    raise RuntimeError("Failed to create FbxFactory.")

# Configure the import task
import_task = AssetImportTask()
if import_task is None:
    raise RuntimeError("Failed to create asset import task.")

# Set the import options
import_task.automated = True
import_task.destination_path = '/Game/Spider'
import_task.filename = spider_fbx_path
import_task.factory = fbx_factory
import_task.replace_existing = True

# Create options for FBX import
fbx_import_options = FbxImportUI()
fbx_import_options.import_materials = False
fbx_import_options.import_textures = False
fbx_import_options.import_animations = False
fbx_import_options.create_physics_asset = False

# Set the import options to the task
import_task.options = fbx_import_options

# Import the mesh
try:
    AssetTools.create_asset(import_task.filename, import_task.destination_path, import_task.factory, import_task)
except Exception as e:
    print(f"Import failed: {e}")

# Create texture factory
texture_factory = TextureFactory()
# texture_factory.overwrite_yes_or_no_to_all_state = 2  # Force overwrite

# Import textures
def import_texture(filename, suffix):
    texture_path = os.path.join(spider_dir, f'Textures/spider_{suffix}.tga')
    return texture_factory.factory_import_object(texture_path, '/Game/Spider/Textures')

# Import body textures
body_textures = {
    'base_color': import_texture('body', 'BaseColor'),
    'normal': import_texture('body', 'Normal'),
    'orm': import_texture('body', 'OcclusionRoughnessMetallic')
}

# Import legs textures
legs_textures = {
    'base_color': import_texture('legs', 'BaseColor'),
    'normal': import_texture('legs', 'Normal'),
    'orm': import_texture('legs', 'OcclusionRoughnessMetallic')
}

# Turn off sRGB for ORM textures
body_textures['orm'].SRGB = False
legs_textures['orm'].SRGB = False

# Setup materials
def setup_material(material, textures):
    material.modify()
    
    # Create and position nodes
    base_color = material.create_material_expression_texture_sample(textures['base_color'], -400, 0)
    normal = material.create_material_expression_texture_sample(textures['normal'], -400, 200)
    normal.sampler_type = 'SAMPLERTYPE_Normal'
    orm = material.create_material_expression_texture_sample(textures['orm'], -400, 400)
    orm.sampler_type = 'SAMPLERTYPE_LinearColor'
    
    # Connect nodes
    material.base_color = base_color
    material.normal = normal
    material.roughness = material.create_expression_material_input(orm, mask=1, mask_g=1)
    material.metallic = material.create_expression_material_input(orm, mask=1, mask_b=1)
    material.ambient_occlusion = material.create_expression_material_input(orm, mask=1, mask_r=1)
    
    material.post_edit_change()

setup_material(material_body, body_textures)
setup_material(material_legs, legs_textures)

# Assign materials to mesh
spider_mesh.materials = [
    SkeletalMaterial(material_interface=material_body, material_slot_name='Body', 
                     uv_channel_data=MeshUVChannelInfo(b_initialized=True)),
    SkeletalMaterial(material_interface=material_legs, material_slot_name='Legs',
                     uv_channel_data=MeshUVChannelInfo(b_initialized=True))
]

# Save assets
EditorAssetLibrary.save_loaded_asset(spider_mesh)
EditorAssetLibrary.save_loaded_asset(material_body)
EditorAssetLibrary.save_loaded_asset(material_legs)

# Import animations
anim_factory = FbxFactory()
anim_factory.import_ui.skeleton = spider_mesh.skeleton
anim_factory.import_ui.basic_import_options.bImportMesh = False
anim_factory.import_ui.basic_import_options.bImportMaterials = False
anim_factory.import_ui.basic_import_options.bImportTextures = False
anim_factory.anim_sequence_import_data.import_uniform_scale = 1.0

# Import animation files
animations = {}
for anim_name in ['idle', 'walk', 'run', 'attack']:
    anim_path = os.path.join(spider_dir, f'Animations/spider_{anim_name}.fbx')
    animations[anim_name] = anim_factory.factory_import_object(anim_path, '/Game/Spider/Animations')

# Create blend space
blend_space_factory = BlendSpaceFactory1D()
blend_space_factory.target_skeleton = spider_mesh.skeleton

spider_locomotion = blend_space_factory.factory_create_new('/Game/Spider/Animations/spider_locomotion')

# Configure blend space
spider_locomotion.modify()
spider_locomotion.blend_parameters = BlendParameter(display_name='Speed', min=0, max=300, grid_num=2)

# Add animation samples
spider_locomotion.sample_data = [
    BlendSample(animation=animations['idle'], sample_value=Vector(0, 0, 0), b_is_valid=True, rate_scale=1),
    BlendSample(animation=animations['walk'], sample_value=Vector(150, 0, 0), b_is_valid=True, rate_scale=1),
    BlendSample(animation=animations['run'], sample_value=Vector(300, 0, 0), b_is_valid=True, rate_scale=1)
]

spider_locomotion.post_edit_change()
EditorAssetLibrary.save_loaded_asset(spider_locomotion)

# Create Animation Blueprint
anim_bp_factory = AnimBlueprintFactory()
anim_bp_factory.target_skeleton = spider_mesh.skeleton

anim_bp_path = '/Game/Spider/spider_AnimBP'
if EditorAssetLibrary.does_asset_exist(anim_bp_path):
    EditorAssetLibrary.delete_asset(anim_bp_path)

anim_bp = anim_bp_factory.factory_create_new(anim_bp_path)

# Add variables
EditorAssetLibrary.add_blueprint_variable(anim_bp, 'Attack', 'bool')
EditorAssetLibrary.add_blueprint_variable(anim_bp, 'Speed', 'float')

# Create state machine
state_machine = anim_bp.create_state_machine('Spider State Machine')

# Add states
locomotion_state = state_machine.add_state('Locomotion')
attack_state = state_machine.add_state('Attack')

# Configure states
locomotion_state.add_blend_space_player(spider_locomotion, 'Speed')
attack_state.add_sequence_player(animations['attack'])

# Add transitions
state_machine.add_transition(locomotion_state, attack_state, 'Attack')
state_machine.add_transition(attack_state, locomotion_state, '!Attack')

# Compile and save
EditorAssetLibrary.compile_blueprint(anim_bp)
EditorAssetLibrary.save_loaded_asset(anim_bp)

# Create Character Blueprint
spider_bp_path = '/Game/Spider/spider_Blueprint'
if EditorAssetLibrary.does_asset_exist(spider_bp_path):
    EditorAssetLibrary.delete_asset(spider_bp_path)

spider_bp = EditorAssetLibrary.create_blueprint_from_class(Character, spider_bp_path)

# Configure character
cdo = spider_bp.get_class_default_object()
cdo.capsule_component.capsule_half_height = 90
cdo.capsule_component.capsule_radius = 55

# Set mesh and animation
cdo.mesh.skeletal_mesh = spider_mesh
cdo.mesh.anim_class = anim_bp.generated_class
cdo.mesh.relative_location = Vector(0, 0, -88)

# Compile and save
EditorAssetLibrary.compile_blueprint(spider_bp)
EditorAssetLibrary.save_loaded_asset(spider_bp)
