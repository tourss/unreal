from pathlib import Path
import unreal

# Export할 자산의 디렉토리 경로와 저장할 경로 설정
source_directory = "/Game/fbx_python/pear"  # 언리얼 자산 디렉토리 위치
export_directory = r"C:\Users\admin\Desktop\fbx\exportedAssets"  # 로컬로 저장할 디렉토리
combined_mesh_name = "CombinedMesh"  # 결합된 메쉬의 이름

# AssetRegistry를 통해 자산 가져오기
asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
assets = asset_registry.get_assets_by_path(source_directory, recursive=True)

# Static Mesh 자산만 필터링
static_meshes = []
for asset in assets:
    if asset.asset_class == "StaticMesh":
        static_meshes.append(asset)

# Static Mesh들을 결합
if static_meshes:
    combined_mesh = unreal.EditorAssetLibrary.find_asset("/Game/CombinedMeshes/" + combined_mesh_name)

    if not combined_mesh:
        # 새 Static Mesh 생성
        combined_mesh = unreal.StaticMeshFactoryNew().factory_create_new(unreal.StaticMesh, None, combined_mesh_name, None)

    # Static Mesh 결합 작업 수행
    static_mesh_component = unreal.StaticMeshComponent()
    for mesh in static_meshes:
        loaded_mesh = unreal.EditorAssetLibrary.load_asset(mesh.object_path)
        if loaded_mesh:
            static_mesh_component.set_static_mesh(loaded_mesh)

    # 결합된 Static Mesh 저장
    unreal.EditorAssetLibrary.save_asset(combined_mesh.get_path_name())

    # FBX Export 작업 생성
    export_path = Path(export_directory) / f"{combined_mesh_name}.fbx"
    export_task = unreal.ExportTask()
    export_task.set_editor_property('filename', str(export_path))
    export_task.set_editor_property('object', combined_mesh)
    export_task.set_editor_property('automated', True)

    # Export 작업 실행
    unreal.EditorAssetLibrary.export_assets([export_task])

    unreal.log(f"Exported combined mesh to {export_path}")
else:
    unreal.log("No static meshes found in the specified directory.")
