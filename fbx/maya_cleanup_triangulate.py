import maya.cmds as cmds

def clean_selected_objects():
    selected_objects = cmds.ls(selection=True)
    if not selected_objects:
        cmds.warning("선택된 오브젝트가 없습니다.")
        return None  # Return None if no objects are selected
    
    cleaned_objects = []  # List to store cleaned objects
    for obj in selected_objects:
        cmds.polyClean(obj,
                       cleanEdges=True,
                       cleanPartialUVMapping=True,
                       cleanUVs=True,
                       cleanVertices=True,
                       constructionHistory=False,
                       frozen=False)
        cleaned_objects.append(obj)  # Add cleaned object to the list
    
    return cleaned_objects  # Return list of cleaned objects

def triangulate_objects(cleaned_objects):
    for obj in cleaned_objects:
        cmds.polyTriangulate(obj)
        print(f"{obj} has been triangulated.")

def print_result():
    cleaned_objects = clean_selected_objects()  # Call the cleanup function and get the result
    if cleaned_objects:
        print("Selected Objects are cleaned up:")
        for obj in cleaned_objects:
            print(f"- {obj}")
        
        triangulate_objects(cleaned_objects)  # Triangulate cleaned objects
    else:
        print("No objects were selected for cleanup.")

# 함수 호출
if __name__ == "__main__":
    print_result()  # Call the print_result function
