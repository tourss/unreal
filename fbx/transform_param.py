from fbx import *

def print_node_transform(node, parent_transform=None):
    """FBX 노드의 변환 정보를 출력하는 함수"""
    if node:
        # 노드의 이름 출력
        node_name = node.GetName()
        print(f"Node: {node_name}")

        # 현재 노드의 위치, 로테이션, 스케일 값 가져오기
        translation = node.LclTranslation.Get()
        rotation = node.LclRotation.Get()
        scaling = node.LclScaling.Get()

        # 부모 노드의 변환을 고려하여 현재 노드의 위치 계산
        if parent_transform:
            # 각 성분을 개별적으로 더하여 새로운 FbxDouble3 객체 생성
            translation = FbxDouble3(
                translation[0] + parent_transform[0],
                translation[1] + parent_transform[1],
                translation[2] + parent_transform[2]
            )
        
        # 변환 정보 출력
        print(f"  Translation: X={translation[0]}, Y={translation[1]}, Z={translation[2]}")
        print(f"  Rotation: Pitch={rotation[0]}, Yaw={rotation[1]}, Roll={rotation[2]}")
        print(f"  Scaling: X={scaling[0]}, Y={scaling[1]}, Z={scaling[2]}")

        # 자식 노드에 대해 재귀 호출
        for i in range(node.GetChildCount()):
            print_node_transform(node.GetChild(i), translation)

def read_fbx_file(file_path):
    """FBX 파일을 읽고 노드의 변환 정보를 출력하는 함수"""
    # FBX 매니저 생성
    manager = FbxManager.Create()
    if not manager:
        print("Error: Unable to create FBX Manager.")
        return

    # FBX IO 설정
    importer = FbxImporter.Create(manager, "")
    if not importer.Initialize(file_path, -1, manager.GetIOSettings()):
        print("Error: Unable to initialize FbxImporter.")
        print(f"Error Message: {importer.GetStatus().GetErrorString()}")
        return

    # 장면 생성
    scene = FbxScene.Create(manager, "MyScene")
    importer.Import(scene)
    importer.Destroy()

    # 루트 노드 가져오기
    root_node = scene.GetRootNode()
    if root_node:
        # 노드 트리의 변환 정보를 출력
        print_node_transform(root_node)
    else:
        print("Error: Unable to get root node.")

    # 자원 해제
    manager.Destroy()

# FBX 파일 경로 설정
fbx_file_path = r"C:\Users\admin\Desktop\fbx\bread_maya\bread_maya.fbx"

# FBX 파일 읽고 위치 출력
read_fbx_file(fbx_file_path)
