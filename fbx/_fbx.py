import fbx_bind

def load_fbx(file_path):
    # FBX 매니저 및 장면 생성
    manager = fbx_bind.FbxManager.Create()
    scene = fbx_bind.FbxScene.Create(manager, "MyScene")

    # FBX 가져오기 설정
    importer = fbx_bind.FbxImporter.Create(manager, "")
    if not importer.Initialize(file_path, -1, manager.GetIOSettings()):
        print("FBX 파일을 초기화할 수 없습니다.")
        print("에러 메시지:", importer.GetStatus().GetErrorString())
        return

    # FBX 파일 가져오기
    if not importer.Import(scene):
        print("FBX 파일을 가져올 수 없습니다.")
        print("에러 메시지:", importer.GetStatus().GetErrorString())
        return

    # 가져온 후 리소스 정리
    importer.Destroy()

    # 노드 정보 출력
    root_node = scene.GetRootNode()
    if root_node:
        print("FBX 파일의 노드:")
        for i in range(root_node.GetChildCount()):
            child_node = root_node.GetChild(i)
            print("노드 이름:", child_node.GetName())
    else:
        print("루트 노드를 찾을 수 없습니다.")

    # 매니저 및 장면 정리
    manager.Destroy()

if __name__ == "__main__":
    # 로드할 FBX 파일 경로
    fbx_file_path = r"C:\Users\admin\Desktop\fbx\pear\pear.fbx"  # 경로 수정
    load_fbx(fbx_file_path)
