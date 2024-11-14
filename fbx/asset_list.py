import unreal

# def listAssetPaths():
#     # print paths of all assets under project root directory
#     EAL = unreal.EditorAssetLibrary

#     assetPaths = EAL.list_assets('/Game/Scene_Saloon')

#     for assetPath in assetPaths: print (assetPath)

# listAssetPaths()

# def getSelectionContentBrowser():

#     EUL = unreal.EditorUtilityLibrary

#     selectedAssets = EUL.get_selected_assets()

#     for selectedAsset in selectedAssets: print (selectedAsset)

# getSelectionContentBrowser()

# def getAllActors():

#     EAS = unreal.EditorActorSubsystem()

#     actors = EAS.get_all_level_actors()
    
#     for actor in actors: print (actor)

# getAllActors()

# def getSelectedActors():
    
#     EAS = unreal.EditorActorSubsystem()

#     selectedActors = EAS.get_selected_level_actors()

#     for selectedActor in selectedActors: print (selectedActor)

# getSelectedActors()

def getAssetClass(classType):

    EAL = unreal.EditorAssetLibrary

    assetPaths = EAL.list_assets('/Game/Scene_Saloon')

    assets = []

    for assetPath in assetPaths:
        assetData = EAL.find_asset_data(assetPath)
        assetClass = assetData.asset_class

        if classType is None or assetClass == classType:
            assets.append(assetData.get_class())


    for asset in assets: 
        print (f"asset: {asset.get_name()}, Class: {asset.get_class()}")

    return assets

def getStaticMeshData():

    staticMeshes = getAssetClass('StaticMesh')

    for staticMesh in staticMeshes:
        # assetImportData = staticMesh.get_editor_property('asset_import_data')
        # fbxFilePath = assetImportData.extract_filenames()
        # print (fbxFilePath)

        lodGroupInfo = staticMesh.get_editor_property('lod_group')
        print (lodGroupInfo)

        if lodGroupInfo == 'None':
            if staticMesh.get_num_lods() == 1:
                staticMesh.set_editor_property('lod_group', 'LargeProp')

getStaticMeshData()