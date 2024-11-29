import os
import subprocess
import logging
import time
from shotgun_api3 import Shotgun

# ShotGrid 설정
SERVER_URL = "https://jhworld.shotgrid.autodesk.com"
SCRIPT_NAME = "hyo"
API_KEY = "qhxiu7rznptjzbonbv*bhxJvu"

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",  # 날짜와 시간 포함
    handlers=[
        logging.FileHandler("render_script.log", encoding="utf-8"),  # 인코딩 설정
        logging.StreamHandler() 
    ]
)

def log_execution_time(func):
    """함수 실행 시간을 로깅하는 데코레이터"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logging.info(f"{func.__name__} 실행 시간: {end_time - start_time:.2f}초")
        return result
    return wrapper

@log_execution_time
def create_shotgun_session(server_url, script_name, api_key):
    """ShotGrid 세션 생성"""
    logging.info("ShotGrid 세션 생성 중...")
    return Shotgun(server_url, script_name, api_key)

@log_execution_time
def get_task_info(sg, task_id):
    """ShotGrid에서 태스크 정보 가져오기 및 Movie Pipeline Config의 하위 폴더 탐색"""
    logging.info(f"Fetching task info for task ID: {task_id}")
    task = sg.find_one(
        "Task",
        [["id", "is", task_id]],
        ["project", "entity.Shot.sg_ue_scene_path", "entity.Shot.sg_movie_pipeline_config"]
    )

    if task:
        logging.info("Task information retrieved successfully.")
        uproject_path = task.get("entity.Shot.sg_ue_scene_path")
        movie_pipeline_config_path = task.get("entity.Shot.sg_movie_pipeline_config")

        # sg_movie_pipeline_config 경로에서 하위 폴더를 검색하는 부분
        if movie_pipeline_config_path:
            logging.info(f"Searching for Movie Pipeline Config in subdirectories of {movie_pipeline_config_path}")
            
            # 하위 폴더에서 파일을 찾기 위한 로직 추가
            for root, dirs, files in os.walk(movie_pipeline_config_path):
                for f in files:
                    if f.endswith(".uasset"):  # .uasset 파일 찾기
                        logging.info(f"Found Movie Pipeline Config file: {os.path.join(root, f)}")
                        # 여기에서 필요한 파일을 처리하거나 반환할 수 있습니다.
        return {
            "uproject_path": uproject_path,
            "movie_pipeline_config": movie_pipeline_config_path
        }

    logging.error("Failed to retrieve task information.")
    return None

def get_uasset_files(content_directory):
    """Content 폴더에서 'seq'가 포함된 .uasset 파일만 찾는 함수"""
    sequence_files = []
    if os.path.exists(content_directory):
        logging.info(f"Searching for .uasset files containing 'seq' in {content_directory}")
        for root, dirs, files in os.walk(content_directory):
            for f in files:
                # 'seq'가 이름에 포함된 .uasset 파일만 찾기
                if f.endswith(".uasset") and "seq" in f.lower():
                    sequence_files.append(os.path.join(root, f))
                    logging.info(f"Found .uasset: {os.path.join(root, f)}")
    else:
        logging.error(f"Error: Directory {content_directory} does not exist.")
    
    return sequence_files

def get_uasset_files_in_queue(queue_directory):
    """Queue 폴더 및 하위 폴더에서 모든 .uasset 파일을 찾는 함수"""
    uasset_files = []
    
    # 경로가 존재하는지 확인
    if os.path.exists(queue_directory):
        logging.info(f"Searching for .uasset files in {queue_directory} and its subdirectories.")
        
        # os.walk()를 사용하여 모든 하위 폴더와 파일을 순차적으로 탐색
        for root, dirs, files in os.walk(queue_directory):
            for f in files:
                if f.endswith(".uasset"):
                    uasset_files.append(os.path.join(root, f))
                    logging.info(f"Found .uasset: {os.path.join(root, f)}")
    else:
        logging.error(f"Error: Directory {queue_directory} does not exist.")
    
    return uasset_files

def generate_render_command(unreal_editor_path, uproject_path, sequence_path, output_dir, resolution, movie_pipeline_config):
    """언리얼 렌더링 명령어 생성"""
    # sequence_path에서 Content 경로를 /Game/ 경로로 변환
    sequence_path = sequence_path.replace("C:/Users/admin/Desktop/Project/pipe_test/Content/", "/Game/").replace("\\", "/").replace(".uasset", "")
    
    # 로그 파일 경로와 output_dir 경로를 역슬래시로 변경
    log_file = os.path.join(output_dir, "render_log.txt").replace("/", "\\")
    output_dir = output_dir.replace("/", "\\")
    unreal_editor_path = unreal_editor_path.replace("/", "\\")
    uproject_path = uproject_path.replace("/", "\\")
    
    # 경로에 공백이 있을 수 있으므로 큰따옴표로 감싸기
    log_file = f'"{log_file}"'
    output_dir = f'"{output_dir}"'
    unreal_editor_path = f'"{unreal_editor_path}"'
    uproject_path = f'"{uproject_path}"'
    movie_pipeline_config = f'"{movie_pipeline_config}"'
    
    # 생성된 명령어 반환
    return (
        f'{unreal_editor_path} {uproject_path} '
        f'-LevelSequence="{sequence_path}" '
        # f'-MovieFolder={output_dir} '
        f'-MoviePipelineConfig={movie_pipeline_config} '
        f'-ResX={resolution[0]} -ResY={resolution[1]} '
        f'-ForceRes -NoTextureStreaming -game '
        f'-NoSplash -RenderOffscreen -log={log_file}'
    )

@log_execution_time
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
def execute_render_task(sg, unreal_editor_path, task_id, output_dir, resolution):
    """렌더 태스크 실행"""
    task_info = get_task_info(sg, task_id)
    if not task_info:
        logging.error("렌더 태스크 실행 실패: 태스크 정보를 가져올 수 없음.")
        return

    uproject_path = task_info["uproject_path"]
    movie_pipeline_config = task_info["movie_pipeline_config"]
  
    content_directory = "C:/Users/admin/Desktop/Project/pipe_test/Content"
    sequence_files = get_uasset_files(content_directory)  # Content 폴더 내에서 'seq'가 포함된 .uasset 파일들 찾기

    if not sequence_files:
        logging.error("렌더링에 사용할 .uasset 파일을 찾을 수 없습니다.")
        return

    # Queue 폴더 내에서 .uasset 파일 찾기 (하위 폴더까지 포함)
    queue_directory = os.path.join("C:", "Users", "admin", "Desktop", "Project", "pipe_test", "Content", "Game", "Cinematics", "Queue")
    queue_files = get_uasset_files_in_queue(queue_directory)

    if not queue_files:
        logging.error("Queue 폴더 내에 .uasset 파일이 없습니다.")
        return

    # 각 시퀀스 파일에 대해 렌더링 및 데드라인 제출
    for sequence_file in sequence_files:
        sequence_path = sequence_file.replace("C:/Users/admin/Desktop/Project/pipe_test/Content/", "/Game/").replace("\\", "/").replace(".uasset", "")
        
        # Queue 폴더 내의 각 파일에 대해 렌더링 명령어 생성
        for queue_file in queue_files:
            queue_path = queue_file.replace("C:/Users/admin/Desktop/Project/pipe_test/Content/", "/Game/").replace("\\", "/").replace(".uasset", "")
            command = generate_render_command(unreal_editor_path, uproject_path, sequence_path, output_dir, resolution, queue_path)
            logging.info(f"명령어 생성 완료: {command}")

            # 명령어를 cmd에서 바로 실행
            try:
                logging.info(f"렌더 명령어 실행 중: {command}")
                result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
                logging.info("렌더링 작업 완료.")
                logging.info(f"출력: {result.stdout}")
                logging.error(f"오류: {result.stderr}")
            except subprocess.CalledProcessError as e:
                logging.error(f"렌더링 실패: {e.stderr}")

            # 데드라인에 작업 제출
            job_name = f"Render_{task_id}"
            submit_to_deadline(job_name, command)

def main():
    """메인 실행 함수"""
    sg = create_shotgun_session(SERVER_URL, SCRIPT_NAME, API_KEY)
    unreal_editor_path = "C:/Program Files/Epic Games/UE_5.4/Engine/Binaries/Win64/UnrealEditor.exe"
    task_id = 1234  # 예시 Task ID, 실제 Task ID로 교체
    output_dir = "C:/Users/admin/Desktop/Project/pipe_test/Output"
    resolution = (1920, 1080)

    execute_render_task(sg, unreal_editor_path, task_id, output_dir, resolution)

if __name__ == "__main__":
    main()
