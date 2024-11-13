import unreal

# 임포트할 FBX 파일 경로와 타겟 디렉토리 설정
fbx_file_path = r"C:\Users\admin\Desktop\fbx\walking_human\walking_human.fbx"  # FBX 파일의 경로를 입력하세요
target_directory = "/Game/test"      # 타겟 디렉토리 경로를 입력하세요

# AssetImportTask 생성
task = unreal.AssetImportTask()
task.set_editor_property('filename', fbx_file_path)
task.set_editor_property('destination_path', target_directory)
task.set_editor_property('automated', True)  # 자동화 설정

# FbxAssetImportData 설정
import_data = unreal.FbxAssetImportData()
import_data.set_editor_property('import_mesh', True)
import_data.set_editor_property('import_textures', True)
import_data.set_editor_property('import_materials', True)

# AssetImportTask에 FbxAssetImportData 추가
task.set_editor_property('options', import_data)

# 임포트 실행
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

# 완료 메시지 출력
print("FBX 임포트 완료: {}".format(fbx_file_path))
