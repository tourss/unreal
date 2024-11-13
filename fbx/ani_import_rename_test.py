import unreal

def import_fbx_animation_with_custom_suffix(fbx_path, suffix_list, custom_prefix=None, custom_suffix=None):
    # FBX 임포트 작업 설정
    task = unreal.AssetImportTask()
    task.filename = fbx_path
    task.destination_path = "/Game/CustomAnimations"
    task.automated = True
    task.save = True

    # FBX 임포트 UI 설정
    fbx_import_options = unreal.FbxImportUI()
    fbx_import_options.import_animations = True
    fbx_import_options.import_as_skeletal = True

    # 애니메이션 임포트 데이터 설정
    anim_import_options = unreal.FbxAnimSequenceImportData()
    anim_import_options.import_custom_attribute = True
    anim_import_options.import_bone_tracks = True
    anim_import_options.remove_redundant_keys = True
    anim_import_options.animation_length = unreal.FBXAnimationLengthImportType.FBXALIT_AnimatedKey
    anim_import_options.convert_scene = True
    anim_import_options.preserve_local_transform = True

    # 커스텀 접미사 설정
    if suffix_list:
        anim_import_options.material_curve_suffixes = suffix_list
    if custom_suffix:
        anim_import_options.material_curve_suffixes = [
            suffix + custom_suffix for suffix in suffix_list
        ]
    anim_import_options.set_material_drive_parameter_on_custom_attribute = True

    # 옵션 연결
    fbx_import_options.anim_sequence_import_data = anim_import_options
    task.options = fbx_import_options

    # 임포트 실행
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    # 임포트된 애셋에 접두사 및 접미사 적용
    imported_assets = task.imported_object_paths
    for asset_path in imported_assets:
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)

        # 애셋에 커스텀 접두사 및 접미사 추가
        if asset:
            original_name = asset.get_name()
            new_name = f"{custom_prefix or ''}{original_name}{custom_suffix or ''}"
            new_asset_path = f"/Game/CustomAnimations/{new_name}"
            if not unreal.EditorAssetLibrary.rename_asset(asset_path, new_asset_path):
                unreal.log_warning(f"Failed to rename {asset_path} to {new_asset_path}")
            unreal.log(f"Renamed {asset_path} to {new_asset_path}")

    unreal.log(f"Imported FBX with custom material curve suffixes: {suffix_list}")

# 사용 예시
import_fbx_animation_with_custom_suffix(
    fbx_path=r"C:\Users\admin\Desktop\fbx\spider\spider.fbx",
    suffix_list=["_A", "_ABP", "_RIG"],
    custom_prefix="Custom_",
    custom_suffix="_01"
)
