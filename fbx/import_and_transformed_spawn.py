import unreal

def get_fbx_position(fbx_file_path):
    """주어진 FBX 파일에서 위치 값을 읽어오는 함수"""
    manager = unreal.FbxManager.create()
    importer = unreal.FbxImporter.create(manager, "")
    
    if not importer.initialize(fbx_file_path, -1, manager.get_io_settings()):
        print(f"Error initializing FBX Importer: {importer.get_status().get_error_string()}")
        return None

    scene = unreal.FbxScene.create(manager, "MyScene")
    importer.import_scene(scene)
    importer.destroy()

    root_node = scene.get_root_node()
    positions = []

    if root_node:
        def traverse_nodes(node):
            """재귀적으로 노드를 순회하며 위치 값을 추출하는 함수"""
            translation = node.get_translation(unreal.FbxGlobalTransform.eSourcePivot)
            unreal_position = (translation[0], translation[2], -translation[1])  # Y와 Z 스위치 및 부호 반전
            positions.append(unreal_position)

            for i in range(node.get_child_count()):
                traverse_nodes(node.get_child(i))

        traverse_nodes(root_node)
    else:
        print("Error: Unable to get root node.")

    # 자원 해제
    manager.destroy()
    return positions

def automated_import_and_add_to_level(fbx_file_paths, destination_path):
    # AutomatedAssetImportData 생성
    import_data = unreal.AutomatedAssetImportData()
    import_data.set_editor_property('destination_path', destination_path)  # 에셋 저장 경로 설정
    import_data.set_editor_property('filenames', fbx_file_paths)  # 파일 리스트 설정
    import_data.set_editor_property('replace_existing', True)  # 기존 에셋 대체 여부

    # 임포트 실행
    imported_assets = unreal.AssetToolsHelpers.get_asset_tools().import_assets_automated(import_data)

    if not imported_assets:
        print("Import failed.")
        return

    # FBX에서 위치 값 가져오기
    positions = get_fbx_position(fbx_file_paths[0])  # 첫 번째 FBX 파일의 위치 값 읽기

    # 임포트된 에셋을 레벨에 배치
    for idx, asset in enumerate(imported_assets):
        if isinstance(asset, unreal.StaticMesh):  # Static Mesh인 경우만 레벨에 배치
            print(f"Successfully imported: {asset.get_name()}")

            # FBX의 원본 지오메트리 데이터를 사용하여 액터를 레벨에 배치
            if positions and idx < len(positions):  # 위치 값이 있는 경우
                position = positions[idx]
                static_mesh_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(asset, unreal.Vector(*position), unreal.Rotator(0, 0, 0))

                # 스케일은 기본값으로 그대로 유지
                print(f"Asset {asset.get_name()} was added to the level at position {position}.")
            else:
                static_mesh_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(asset, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
                print(f"Asset {asset.get_name()} was added to the level at default position (0, 0, 0).")

# 예시 사용: FBX 파일 경로와 저장할 위치 지정
fbx_files = [r"C:\Users\admin\Desktop\fbx\bread_maya\bread_maya.fbx"]
dest_path = "/Game/fbx_python/bread_maya"

# 임포트 후 레벨에 추가
automated_import_and_add_to_level(fbx_files, dest_path)
