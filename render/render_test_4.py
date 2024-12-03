import logging
from logging import handlers
from shotgun_api3 import Shotgun
import os
import subprocess
import traceback
import time

# ShotGrid 서버 URL과 인증 정보
SERVER_URL = "https://hg.shotgrid.autodesk.com"
SCRIPT_NAME = "hyo"
API_KEY = "4yhreigsfqmwlsz%yfnfuqqYo"

# 로깅 설정
log_filename = "render_script.log"
logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# TimedRotatingFileHandler로 15일마다 로그 파일 회전
handler = handlers.TimedRotatingFileHandler(
    log_filename, when="D", interval=15, backupCount=150
)
logging.getLogger().addHandler(handler)

def log_execution_time(func):
    # 함수 실행 시간을 로그로 기록하는 데코레이터
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"Execution time for {func.__name__}: {elapsed_time:.2f} seconds.")
        print(f"Execution time for {func.__name__}: {elapsed_time:.2f} seconds.")
        return result
    return wrapper

def create_shotgun_session(server_url, script_name, api_key):
    # ShotGrid API 세션 생성
    logging.info(f"Creating Shotgun session with script: {script_name}")
    return Shotgun(server_url, script_name, api_key)

def get_software_info(sg, software_name):
    # ShotGrid에서 소프트웨어 정보 가져오기
    logging.info(f"Fetching software info for {software_name}")
    software = sg.find_one(
        "Software",
        [["code", "is", software_name]],
        ["windows_path", "windows_args"]
    )
    if software is not None:
        logging.info(f"Found software: {software_name}")
        return software.get("windows_path"), software.get("windows_args")
    else:
        logging.error(f"Error: '{software_name}' not found in ShotGrid Software")
        return None, None

def get_task_info(sg, task_id):
    # Task 정보 가져오기
    logging.info(f"Fetching task info for task ID: {task_id}")
    task = sg.find_one(
        "Task",
        [["id", "is", task_id]],
        ["project", "entity.Shot.sg_ue_scene_path", "entity.Shot.sg_movie_pipeline_config"]
    )
    if task is not None:
        uproject_path = task.get("entity.Shot.sg_ue_scene_path")
        movie_pipeline_config = task.get("entity.Shot.sg_movie_pipeline_config")
        logging.info(f"Found uproject path: {uproject_path} and movie pipeline config: {movie_pipeline_config}")
        return uproject_path, movie_pipeline_config
    else:
        logging.error("Error: 'task' is None. Unable to access task information.")
        return None, None

def get_uasset_files(movie_pipeline_config):
    # .uasset 파일을 찾아서 리스트로 반환
    movie_pipeline_directory = movie_pipeline_config.replace("/Game/", "C:/Users/admin/Desktop/Project/pipe_test/Content/") 
    config_files = []

    if os.path.exists(movie_pipeline_directory):
        logging.info(f"Searching for .uasset files in {movie_pipeline_directory}")
        for root, dirs, files in os.walk(movie_pipeline_directory):
            for f in files:
                if f.endswith(".uasset"):
                    config_files.append(os.path.join(root, f))
                    logging.info(f"Found .uasset: {os.path.join(root, f)}")
    for config_file in config_files:
        print("config file context:", config_file)
    else:
        logging.error(f"Error: Directory {movie_pipeline_directory} does not exist.")
    
    return config_files

def generate_cmd_command(unreal_editor_path, uproject_path, config_file, render_args):
    # MoviePipelineConfig의 상대 경로 가져오기
    config_path = config_file.replace("C:/Users/admin/Desktop/Project/pipe_test/Content/", "/Game/")
    
    # .uasset 확장자를 제거하고 Unreal 경로로 설정
    config_name = os.path.splitext(config_path)[0]

    # 백슬래시를 슬래시로 바꾸어 호환성 확보
    config_name = config_name.replace("\\", "/")
    
    # job_name 생성 (config 파일 이름을 사용)
    job_name = f"Render_{os.path.basename(config_file)}"

    # MoviePipelineConfig을 정확히 참조하도록 커맨드 생성
    command = (
        f'"{unreal_editor_path}" '
        f'"{uproject_path}" '
        f'-game '
        f'-NoSplash ' 
        f'-log '
        f'-RenderOffscreen '
        f'-NoTextureStreaming '
        f'-MoviePipelineConfig="{config_name}" '
    )

    logging.info(f"Generated command: {command}")
    return job_name, command

def submit_to_deadline(job_name, command):
    """데드라인에 렌더 작업 제출"""
    deadline_command = [
        "deadlinecommand",
        "-SubmitCommandLineJob",
        f"-name {job_name}",
        f"-executable {command}"
    ]
    try:
        result = subprocess.run(deadline_command, capture_output=True, text=True, check=True)
        logging.info("데드라인 작업 제출 성공")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error("데드라인 작업 제출 실패")
        logging.error(e.stderr)
        return None

@log_execution_time
def execute_cmd_command(job_name, cmd_command):
    # CMD 명령어 실행 및 데드라인에 작업 제출
    try:
        logging.info(f"Executing command: {cmd_command}")
        subprocess.run(cmd_command, shell=True, check=True)  # check=True will raise an exception if the command fails

        # 데드라인에 작업 제출
        logging.info(f"Submitting job '{job_name}' to Deadline")
        submit_to_deadline(job_name, cmd_command)  # 데드라인에 작업 제출
    except subprocess.CalledProcessError as e:
        logging.error(f"Error occurred while executing the command: {cmd_command}")
        logging.error(f"Return code: {e.returncode}")
        logging.error("Output:")
        logging.error(e.output)
        traceback.print_exc()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        traceback.print_exc()

def execute():
    logging.info("Starting script execution")
    
    sg = create_shotgun_session(SERVER_URL, SCRIPT_NAME, API_KEY)

    software_name = "Unreal Engine Editor"
    unreal_editor_path, render_args = get_software_info(sg, software_name)
    
    if unreal_editor_path is None:
        return

    # Task ID
    task_id = 5827  # 실제 태스크 ID로 변경

    uproject_path, movie_pipeline_config = get_task_info(sg, task_id)

    if uproject_path and movie_pipeline_config:
        config_files = get_uasset_files(movie_pipeline_config)

        if config_files:
            for config_file in config_files:
                job_name, cmd_command = generate_cmd_command(unreal_editor_path, uproject_path, config_file, render_args)
                logging.info('*' * 50)
                logging.info(f"Processing: {config_file}")
                logging.info(f"Generated CMD: {cmd_command}")
                logging.info('*' * 50)
                print("CMD COMMAND:", cmd_command)
                execute_cmd_command(job_name, cmd_command)
        else:
            logging.warning(f"No .uasset files found in {movie_pipeline_config}")
    else:
        logging.error("Not found uproject path or movie_pipeline_config in ShotGrid")

    logging.info("Script execution finished")

if __name__ == "__main__":
    execute()
