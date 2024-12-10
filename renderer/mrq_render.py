import logging
from logging import handlers
from shotgun_api3 import Shotgun
import os
import subprocess
import traceback
import time

class MrqRender:
    def __init__(self, server_url, script_name, api_key):
        # ShotGrid 서버 URL과 인증 정보
        self.server_url = server_url
        self.script_name = script_name
        self.api_key = api_key

        # 로깅 설정
        self.log_filename = "render_script.log"
        logging.basicConfig(
            level=logging.DEBUG, 
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        
        # TimedRotatingFileHandler로 15일마다 로그 파일 회전
        self.handler = handlers.TimedRotatingFileHandler(
            self.log_filename, when="D", interval=15, backupCount=150
        )
        logging.getLogger().addHandler(self.handler)

        self.sg = None  # ShotGrid 세션
        self.unreal_editor_path = None  
        self.render_args = None
        self.uproject_path = None
        self.movie_pipeline_config = None

    def log_execution_time(func):
        # 함수 실행 시간을 로그로 기록하는 데코레이터
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            result = func(self, *args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            logging.info(f"Execution time for {func.__name__}: {elapsed_time:.2f} seconds.")
            print(f"Execution time for {func.__name__}: {elapsed_time:.2f} seconds.")
            return result
        return wrapper

    def create_shotgun_session(self):
        # ShotGrid API 세션 생성
        logging.info(f"Creating Shotgun session with script: {self.script_name}")
        self.sg = Shotgun(self.server_url, self.script_name, self.api_key)

    def get_software_info(self, software_name):
        # ShotGrid에서 소프트웨어 정보 가져오기
        logging.info(f"Fetching software info for {software_name}")
        software = self.sg.find_one(
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

    def get_task_info(self, task_id):
        # Task 정보 가져오기
        logging.info(f"Fetching task info for task ID: {task_id}")
        task = self.sg.find_one(
            "Task",
            [["id", "is", task_id]],
            ["project", "entity.Shot.sg_ue_scene_path", "entity.Shot.sg_movie_pipeline_config"]
        )
        if task is not None:
            self.uproject_path = task.get("entity.Shot.sg_ue_scene_path")
            self.movie_pipeline_config = task.get("entity.Shot.sg_movie_pipeline_config")
            logging.info(f"Found uproject path: {self.uproject_path} and movie pipeline config: {self.movie_pipeline_config}")
        else:
            logging.error("Error: 'task' is None. Unable to access task information.")

    def get_uasset_files(self):
        # .uasset 파일을 찾아서 리스트로 반환
        movie_pipeline_directory = self.movie_pipeline_config.replace("/Game/", "C:/Users/admin/Desktop/Project/pipe_test/Content/") 
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

    def generate_cmd_command(self, config_file):
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
            f'"{self.unreal_editor_path}" '
            f'"{self.uproject_path}" '
            f'-game '
            f'-NoSplash ' 
            f'-log '
            f'-RenderOffscreen '
            f'-NoTextureStreaming '
            f'-MoviePipelineConfig="{config_name}" '
        )

        logging.info(f"Generated command: {command}")
        return job_name, command

    def submit_to_deadline(self, job_name, command):
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
    def execute_cmd_command(self, job_name, cmd_command):
        # CMD 명령어 실행 및 데드라인에 작업 제출
        try:
            logging.info(f"Executing command: {cmd_command}")
            subprocess.run(cmd_command, shell=True, check=True)  # check=True will raise an exception if the command fails

            # 데드라인에 작업 제출
            logging.info(f"Submitting job '{job_name}' to Deadline")
            self.submit_to_deadline(job_name, cmd_command)  # 데드라인에 작업 제출
        except subprocess.CalledProcessError as e:
            logging.error(f"Error occurred while executing the command: {cmd_command}")
            logging.error(f"Return code: {e.returncode}")
            logging.error("Output:")
            logging.error(e.output)
            traceback.print_exc()
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            traceback.print_exc()
    
    def execute_nuke_render(self):
        # nuke_render.py 실행
        nuke_command = [
            "C:\\Program Files\\Nuke15.1v2\\Nuke15.1.exe",
            "-t",  # 터미널 모드로 실행 (GUI 없이)
            "C:\\Users\\admin\\.repo\\unreal\\render\\renderer\\nuke_render.py"
        ]

        try:
            logging.info("Starting Nuke rendering process...")
            subprocess.run(nuke_command, check=True)
            logging.info("Nuke rendering finished.")
        except subprocess.CalledProcessError as e:
            logging.error("Nuke render process failed.")
            logging.error(e.stderr)
        except Exception as e:
            logging.error(f"Unexpected error in Nuke render: {e}")
            traceback.print_exc()

    def execute_mrq_render(self, task_id):
        """mrq렌더 완료 후 execute_nuke_render 함수 실행"""
        logging.info("Starting script execution")
        
        self.create_shotgun_session()

        software_name = "Unreal Engine Editor"
        self.unreal_editor_path, render_args = self.get_software_info(software_name)
        
        if self.unreal_editor_path is None:
            return

        self.get_task_info(task_id)

        if self.uproject_path and self.movie_pipeline_config:
            config_files = self.get_uasset_files()

            if config_files:
                for config_file in config_files:
                    job_name, cmd_command = self.generate_cmd_command(config_file)
                    logging.info('*' * 50)
                    logging.info(f"Processing: {config_file}")
                    logging.info(f"Generated CMD: {cmd_command}")
                    logging.info('*' * 50)
                    print("CMD COMMAND:", cmd_command)
                    self.execute_cmd_command(job_name, cmd_command)
                
                self.execute_nuke_render() # Nuke 렌더 실행

            else:
                logging.warning(f"No .uasset files found in {self.movie_pipeline_config}")
        else:
            logging.error("Not found uproject path or movie_pipeline_config in ShotGrid")

        logging.info("Script execution finished")

if __name__ == "__main__":
    render_job = MrqRender(
        server_url="https://hg.shotgrid.autodesk.com", 
        script_name="hyo", 
        api_key="4yhreigsfqmwlsz%yfnfuqqYo"
    )
    render_job.execute_mrq_render(task_id=5827)  # 실제 태스크 ID로 변경