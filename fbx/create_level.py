import unreal

def create_level():
    # Create a new level
    level_name = "test"
    unreal.EditorLevelLibrary.new_level(level_name)
    
    # Load the new level
    unreal.EditorLevelLibrary.load_level(level_name)

    # Create a floor plane
    floor_plane = unreal.EditorAssetLibrary.load_blueprint_class('/Game/Geometry/Plane')
    floor_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(floor_plane, unreal.Vector(0, 0, 0))
    
    # Create a point light
    light_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PointLight, unreal.Vector(0, 0, 300))
    light_actor.set_editor_property('intensity', 5000)  # Set light intensity

    # Create a camera
    camera_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(0, -300, 300))
    camera_actor.set_actor_rotation(unreal.Rotator(-30, 0, 0))  # Set camera rotation

    # Print the created actors
    unreal.log("Level setup complete!")
    unreal.log(f"Floor Plane: {floor_actor.get_name()}")
    unreal.log(f"Point Light: {light_actor.get_name()}")
    unreal.log(f"Camera: {camera_actor.get_name()}")

# Execute the level creation function
create_level()
