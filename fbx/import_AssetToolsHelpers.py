import unreal

def importAssets(file_names):
    """
    Import assets into project
    """
    # Create Asset Tools object
    assetTools = unreal.AssetToolsHelpers.get_asset_tools()

    # Define Import Task
    task = unreal.AssetImportTask()
    task.automated = True
    task.destination_path = "/Game/import_test"
    task.replace_existing = True
    task.filename = file_names[0]  # 단일 파일
    task.save = True
    print (file_names)

    # Execute Import Task
    assetTools.import_asset_tasks([task])

    # Check if the import was successful
    if task.imported_object_paths:
        unreal.log("Assets imported successfully: " + str(task.imported_object_paths))
    else:
        unreal.log_error("Failed to import assets. Check file compatibility and paths.")

def buildSelectedAssets(folder_path, file_names):
    textures = []
    geo = []

    for asset_path in unreal.EditorAssetLibrary.list_assets(folder_path):
        asset_path = asset_path.split('.')[0]
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        try:
            assetImportData = asset.get_editor_property("asset_import_data")
            import_file_path = assetImportData.get_first_filename()
            if import_file_path in file_names:
                if isinstance(asset, unreal.StaticMesh) or isinstance(asset, unreal.SkeletalMesh):
                    geo.append(asset)
                elif isinstance(asset, unreal.Texture):
                    textures.append(asset)
        except AttributeError:
            pass  # Some assets may not have asset import data

if __name__ == "__main__":
    file_names = [r"C:/Users/admin/Desktop/fbx/mint_girl/mint_girl.fbx"]
    importAssets(file_names)
