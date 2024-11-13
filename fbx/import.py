from pathlib import Path
from typing import List
import unreal

# path
destination_path = "/Game/fbx_python/pear"  # 언리얼 자산 디렉토리 위치
source_path = r"C:\Users\admin\Desktop\fbx\pear\pear.fbx"  # 로컬 자산 디렉토리 위치
assets_to_import = list(Path(source_path).glob("*.fbx"))

# import data 
static_mesh_import_data = unreal.FbxStaticMeshImportData()
static_mesh_import_data.combine_meshes = True
static_mesh_import_data.remove_degenerates = True

# import options setting
options = unreal.FbxImportUI()
options.import_mesh = True
options.import_as_skeletal = True
options.import_animations = True
options.import_textures = False
options.import_materials = False
options.automated_import_should_detect_type = True
options.skeletal_mesh_import_data = fbx_import_data

# import tasks list
tasks: List[unreal.AssetImportTask] = []

# generate import tasks
for input_file_path in assets_to_import:
    task = unreal.AssetImportTask()
    task.automated = True
    task.destination_path = destination_path
    task.destination_name = Path(input_file_path).stem  # 파일 이름을 자산 이름으로 사용 #안되면 input_file_path.stem
    task.filename = str(input_file_path)
    task.replace_existing = True
    task.save = True
    task.options = options

    tasks.append(task)

# execute import tasks
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(unreal.Array(unreal.Asset.cast(unreal.AssetImportTask, tasks)

# log print
for task in tasks:
    for path in task.imported_object_paths:
        unreal.log(f"Imported {path}")
