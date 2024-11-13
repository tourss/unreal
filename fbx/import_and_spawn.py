import unreal

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

    # 임포트된 에셋을 레벨에 배치
    for asset in imported_assets:
        if isinstance(asset, unreal.StaticMesh):  # Static Mesh인 경우만 레벨에 배치
            print(f"Successfully imported: {asset.get_name()}")

            # FBX의 원본 지오메트리 데이터를 사용하여 액터를 레벨에 배치
            static_mesh_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(asset, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))

            # 스케일은 기본값으로 그대로 유지
            print(f"Asset {asset.get_name()} was added to the level using original FBX geometry.")

# 예시 사용: FBX 파일 경로와 저장할 위치 지정
fbx_files = [r"C:\Users\admin\Desktop\fbx\pear\pear.fbx"]
dest_path = "/Game/fbx_python/pear"

# 임포트 후 레벨에 추가
automated_import_and_add_to_level(fbx_files, dest_path)
