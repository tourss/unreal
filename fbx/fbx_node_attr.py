from fbx import *

def print_node_info(node, level=0):
    """노드의 이름과 타입을 출력하는 함수"""
    indent = "  " * level  # 노드 깊이에 따라 들여쓰기
    node_name = node.GetName()
    attr = node.GetNodeAttribute()
    attr_type = attr.GetAttributeType() if attr else "No Attribute"

    print(f"{indent}Node Name: {node_name}, Attribute Type: {attr_type}")

    # 자식 노드에 대해 재귀 호출
    for i in range(node.GetChildCount()):
        print_node_info(node.GetChild(i), level + 1)

def main():
    # FBX 매니저 생성
    manager = FbxManager.Create()
    if not manager:
        print("Error: Unable to create FBX Manager.")
        return

    # FBX IO 설정
    importer = FbxImporter.Create(manager, "")
    if not importer.Initialize("C:\\Users\\admin\\Desktop\\fbx\\spider\\Spider_2.fbx", -1, manager.GetIOSettings()):
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
        # 모든 노드 정보 출력
        print_node_info(root_node)
    else:
        print("Error: Unable to get root node.")

    # 자원 해제
    manager.Destroy()
    print("FBX node information extraction completed.")

if __name__ == "__main__":
    main()
