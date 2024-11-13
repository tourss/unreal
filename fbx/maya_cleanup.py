import maya.cmds as cmds

def clean_selected_objects():
    selected_objects = cmds.ls(selection=True)
    if not selected_objects:
        cmds.warning("선택된 오브젝트가 없습니다.")
        return False  # Return False if no objects are selected
    
    for obj in selected_objects:
        cmds.polyClean(obj,
                       cleanEdges=True,
                       cleanPartialUVMapping=True,
                       cleanUVs=True,
                       cleanVertices=True,
                       constructionHistory=False,
                       frozen=False)
    
    return True  # Return True if cleanup was successful

def print_result():
    result = clean_selected_objects()  # Call the cleanup function and get the result
    if result:
        print("Selected Object is cleaned up")
    else:
        print("No objects were selected for cleanup")

# 함수 호출
if __name__ == "__main__":
    print_result()  # Call the print_result function
