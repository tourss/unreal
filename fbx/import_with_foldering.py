import unreal
import os

def find_fbx_file(folder_path):
    # 지정된 폴더 안에서 .fbx 파일 찾기
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".fbx"):
                return os.path.join(root, file)
    return None

def import_fbx(fbx_input):
    fbx_file_path = None

    # 입력이 폴더인지 파일인지 확인
    if os.path.isdir(fbx_input):
        # 폴더인 경우, FBX 파일 찾기
        fbx_file_path = find_fbx_file(fbx_input)
        if not fbx_file_path:
            unreal.log_error("No FBX file found in the specified folder.")
            return
    elif os.path.isfile(fbx_input) and fbx_input.lower().endswith(".fbx"):
        # 파일인 경우, 경로 사용
        fbx_file_path = fbx_input
    else:
        unreal.log_error("Invalid input. Please provide a valid FBX file or folder.")
        return

    # FBX 임포트 UI 및 옵션 설정
    import_options = unreal.FbxImportUI()
    import_options.set_editor_property("import_mesh", True)
    import_options.set_editor_property("import_textures", True)
    import_options.set_editor_property("import_materials", True)
    import_options.set_editor_property("import_animations", True)  # 애니메이션 임포트 활성화
    import_options.set_editor_property("import_as_skeletal", True)

    # FBX 파일의 이름으로 폴더 이름 설정
    fbx_name = os.path.basename(fbx_file_path).split(".")[0]
    base_folder = f"/Game/{fbx_name}"

    # FBX 임포트 패키지 경로
    package_path = base_folder
    unreal.EditorAssetLibrary.make_directory(package_path)

    # FBX 파일 임포트
    factory = unreal.FbxImportFactory()
    factory.set_editor_property("import_options", import_options)

    # 자산 임포트
    imported_asset = unreal.AssetToolsHelpers.get_asset_tools().import_asset(fbx_name, package_path, factory)

    if not imported_asset:
        unreal.log_error("Failed to import FBX asset.")
        return

    # 각 속성별로 자산 이동
    asset_class = imported_asset.get_class()
    asset_name = imported_asset.get_name()

    if asset_class == unreal.StaticMesh:
        folder_name = "Meshes/Static"
    elif asset_class == unreal.SkeletalMesh:
        folder_name = "Meshes/Skeletal"
    elif asset_class == unreal.Material:
        folder_name = "Materials"
    elif asset_class == unreal.Texture:
        folder_name = "Textures"
    elif asset_class == unreal.AnimSequence:
        folder_name = "Animations"
    else:
        unreal.log("Asset class not supported, skipping.")
        return  # 지원하지 않는 클래스는 무시

    # 폴더 경로 설정
    folder_path = f"{package_path}/{folder_name}"

    # 폴더가 없으면 생성
    unreal.EditorAssetLibrary.make_directory(folder_path)

    # 자산 이동
    unreal.EditorAssetLibrary.rename_asset(imported_asset.get_path_name(), f"{folder_path}/{asset_name}")

    unreal.EditorAssetLibrary.save_loaded_assets([imported_asset])

# FBX 파일 또는 폴더 경로 설정
fbx_input = r"C:\Users\admin\Desktop\fbx\walking_human_maya"  # FBX 파일이 있는 폴더 또는 FBX 파일 경로

# FBX 파일 임포트 함수 호출
import_fbx(fbx_input)
