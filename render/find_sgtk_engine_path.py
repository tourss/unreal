import os
import sys
sgtk_path = r"C://Users//admin//AppData//Roaming//Shotgun//hg//sitec2.basic.desktop//cfg//install//core//python"
if sgtk_path not in sys.path:
    sys.path.append(sgtk_path)
import sgtk

def get_unreal_engine_path():
    """
    ShotGrid Toolkit을 사용하여 Unreal Engine 실행 경로를 검색
    """

    project_root = r"C://Users//admin//AppData//Roaming//Shotgun//hg//sitec2.basic.desktop"

    sgtk.platform.bootstrap_toolkit_from_path(project_root)

    # 엔진을 초기화한 후에 작업 수행
    print("SGTK Engine initialized!")

    # 현재 컨텍스트 가져오기
    engine = sgtk.platform.current_engine()
    if not engine:
        print("No active SGTK engine found. Are you running this in an SGTK environment?")
        return

    # Unreal Engine 실행 정보를 찾기
    app_launcher = engine.apps.get("tk-multi-launchapp")
    if not app_launcher:
        print("The 'tk-multi-launchapp' is not configured in this environment.")
        return

    # Unreal 관련 경로 검색
    app_settings = app_launcher.get_setting("apps")
    unreal_settings = next(
        (app for app in app_settings if "unreal" in app["engine_name"].lower()), 
        None
    )

    if unreal_settings:
        unreal_path = unreal_settings.get("path")
        print (unreal_path)
        if unreal_path:
            print(f"Unreal Engine Executable Path: {unreal_path}")
        else:
            print("Unreal Engine executable path is not set in the configuration.")
    else:
        print("Unreal Engine is not configured in the current ShotGrid Toolkit environment.")

if __name__ == "__main__":
    get_unreal_engine_path()
