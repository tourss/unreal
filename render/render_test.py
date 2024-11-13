from shotgun_api3 import Shotgun
import subprocess
import os

# ShotGrid 서버 URL 및 인증 정보
SERVER_URL = "https://jhworld.shotgrid.autodesk.com"
SCRIPT_NAME = "hyo"
API_KEY = "qhxiu7rznptjzbonbv*bhxJvu"

def create_shotgun_session(server_url, script_name, api_key):
    """ShotGrid API 세션을 생성합니다."""
    return Shotgun(server_url, script_name, api_key)

def get_software_info(sg, software_name):
    """ShotGrid에서 주어진 소프트웨어의 경로와 인자 정보를 가져옵니다."""
    software = sg.find_one(
        "Software",
        [["code", "is", software_name]],
        ["windows_path", "windows_args"]
    )
    if software is not None:
        return software.get("windows_path"), software.get("windows_args")
    else:
        print(f"Error: '{software_name}' not found in ShotGrid Software")
        return None, None

def get_task_info(sg, task_id):
    """ShotGrid에서 주어진 태스크 ID로 정보를 가져옵니다."""
    task = sg.find_one(
        "Task",
        [["id", "is", task_id]],
        ["project", "entity.Shot.sg_ue_scene_path", "entity.Shot.sg_movie_pipeline_config"]
    )
    if task is not None:
        uproject_path = task.get("entity.Shot.sg_ue_scene_path")
        movie_pipeline_config = task.get("entity.Shot.sg_movie_pipeline_config")
        return uproject_path, movie_pipeline_config
    else:
        print("Error: 'task' is None. Unable to access task information.")
        return None, movie_pipeline_config
    
def get_uasset_files(movie_pipeline_config):
    """MoviePipelineConfig 디렉토리에서 .uasset 파일을 검색하는 함수"""
    movie_pipeline_directory = movie_pipeline_config.replace("/Game/", "C:/Users/admin/Desktop/Project/pipe_test/Content/") 
    config_files = []

    for f in os.listdir(movie_pipeline_directory):
        if f.endswith(".uasset"):
            config_files.append(f)
    return config_files

def generate_cmd_command(unreal_editor_path, uproject_path, movie_pipeline_config, config_files,render_args):
    """Unreal Editor 실행을 위한 CMD 명령어를 생성합니다."""
    return (
        f'"{unreal_editor_path}" "{uproject_path}" -game '
        f'-MoviePipelineConfig="{movie_pipeline_config}/myRenderQueue" '
        f'{render_args}'
    )

def execute_cmd_command(cmd_command):
    """생성된 CMD 명령어를 실행합니다."""
    print("Executing CMD command:")
    print(cmd_command)
    subprocess.run(cmd_command, shell=True)

def main():
    # ShotGrid 세션 생성
    sg = create_shotgun_session(SERVER_URL, SCRIPT_NAME, API_KEY)

    # 소프트웨어 정보 가져오기
    software_name = "Unreal Engine Editor"
    unreal_editor_path, render_args = get_software_info(sg, software_name)
    
    if unreal_editor_path is None:
        return

    # Task ID 설정
    task_id = 5849  # 실제 태스크 ID로 변경

    # 태스크 정보 가져오기
    uproject_path, movie_pipeline_config = get_task_info(sg, task_id)

    if uproject_path and movie_pipeline_config:
        # CMD 명령어 생성
        cmd_command = generate_cmd_command(unreal_editor_path, uproject_path, movie_pipeline_config, render_args)
        
        # CMD 명령어 실행
        execute_cmd_command(cmd_command)
    else:
        print("ShotGrid에서 uproject 경로나 movie_pipeline_config 값을 가져올 수 없습니다.")

if __name__ == "__main__":
    main()
