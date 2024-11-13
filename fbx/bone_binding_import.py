import unreal

def rename_assets_from_fbx(fbx_path, base_name):
    # FBX 임포트 옵션 설정
    task = unreal.AssetImportTask()
    task.filename = fbx_path
    task.destination_path = "/Game/CustomAssets"  # 임포트할 폴더 경로
    task.automated = True
    task.save = True
    task.replace_existing = True

    # FBX 임포트 옵션 추가: 스켈레탈 메시와 본(bone) 바인딩 관련 설정
    fbx_import_options = unreal.FbxImportUI()
    fbx_import_options.import_mesh = True  # 메시 임포트
    fbx_import_options.import_as_skeletal = True  # 스켈레탈 메시로 임포트
    fbx_import_options.skeletal_mesh_import_data.import_bones = True  # 본(bone) 임포트 활성화
    fbx_import_options.skeletal_mesh_import_data.import_bone_weights = True  # 본 가중치 임포트
    fbx_import_options.skeletal_mesh_import_data.import_morph_targets = True  # 모프 타겟(필요 시)
    fbx_import_options.skeletal_mesh_import_data.use_t0_as_ref_pose = True  # 바인드 포즈로 사용

    # 옵션 적용
    task.options = fbx_import_options

    # FBX 임포트 실행
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    # 임포트된 애셋 목록 가져오기
    imported_assets = task.imported_object_paths
    asset_count = 1  # 순차 번호 초기화

    for asset_path in imported_assets:
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)

        if asset:
            # 애셋 타입에 따라 이름 변경 규칙 정의
            if isinstance(asset, unreal.StaticMesh):
                new_name = f"SM_{base_name}_{asset_count}"
            elif isinstance(asset, unreal.SkeletalMesh):
                new_name = f"SK_{base_name}_{asset_count}"
            elif isinstance(asset, unreal.AnimationAsset):
                new_name = f"{base_name}_Anim_{asset_count}"
            elif isinstance(asset, unreal.Material):
                new_name = f"{base_name}_Material_{asset_count}"
            elif isinstance(asset, unreal.Texture):
                new_name = f"{base_name}_Texture_{asset_count}"
            else:
                new_name = f"{base_name}_Asset_{asset_count}"

            # 새 이름으로 애셋 변경
            new_asset_path = f"/Game/CustomAssets/{new_name}"
            if not unreal.EditorAssetLibrary.rename_asset(asset_path, new_asset_path):
                unreal.log_warning(f"Failed to rename {asset_path} to {new_asset_path}")

            unreal.log(f"Renamed {asset_path} to {new_asset_path}")
            asset_count += 1  # 순차 번호 증가

# 예시 사용법
rename_assets_from_fbx(r"C:\Users\admin\Desktop\fbx\spider\spider.fbx", "MyCustomAsset")
