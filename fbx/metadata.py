import unreal

# FBX 파일 경로
fbx_file_path = r"C:\Users\admin\Desktop\fbx\pear\pear.fbx"

# 임포트할 목적지 경로
destination_path = r"C:\Users\admin\Desktop\fbx\pear"

# FBX 임포트 옵션 설정
import_options = unreal.FbxImportOptions()
import_options.set_editor_property("import_mesh", True)
import_options.set_editor_property("import_textures", True)
import_options.set_editor_property("import_materials", True)

# FBX 에셋 임포트 데이터 생성
fbx_import_data = unreal.FbxAssetImportData()
fbx_import_data.set_editor_property("import_options", import_options)

# 에셋 임포트
unreal.AssetToolsHelpers.get_asset_tools().import_asset(destination_path, fbx_file_path, fbx_import_data)
