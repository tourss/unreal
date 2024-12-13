import logging
from logging import handlers
from shotgun_api3 import Shotgun
import os
import subprocess
import traceback
import time
import unreal

class MrqRender:
    def __init__(self, server_url, script_name, api_key):
        self.server_url = server_url
        self.script_name = script_name
        self.api_key = api_key

        # 절대 경로로 로그 파일 설정
        self.log_filename = os.path.join(os.getcwd(), r"C:\Users\admin\.repo\unreal\renderer\render_script.log")
        
        # 로깅 핸들러 설정
        self.handler = handlers.TimedRotatingFileHandler(
            self.log_filename, when="D", interval=15, backupCount=150
        )
        
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger().addHandler(self.handler)

        self.sg = None
        self.unreal_editor_path = None  
        self.render_args = None
        self.uproject_path = None
        self.movie_pipeline_config = None

        logging.info("RenderScript initialized")

    def log_execution_time(func):
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            result = func(self, *args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            logging.info(f"Execution time for {func.__name__}: {elapsed_time:.2f} seconds.")
            return result
        return wrapper

    def create_shotgun_session(self):
        logging.info(f"Creating Shotgun session with script: {self.script_name}")
        self.sg = Shotgun(self.server_url, self.script_name, self.api_key)

    def get_software_info(self, software_name):
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
        movie_pipeline_directory = self.movie_pipeline_config.replace("/Game/", "C:/Users/admin/Desktop/Project/pipe_test/Content/")
        config_files = []

        if os.path.exists(movie_pipeline_directory):
            logging.info(f"Searching for .uasset files in {movie_pipeline_directory}")
            for root, dirs, files in os.walk(movie_pipeline_directory):
                for f in files:
                    if f.endswith(".uasset"):
                        # .uasset 파일의 경로에서 '/'를 '\\'로 변환
                        file_path = os.path.join(root, f).replace("/", "\\")
                        config_files.append(file_path)
                        logging.info(f"Found .uasset: {file_path}")
        else:
            logging.error(f"Error: Directory {movie_pipeline_directory} does not exist.")
        
        return config_files
        
    def _get_and_set_resolution(self):
        # get_uasset_files에서 반환된 파일을 사용
        config_files = self.get_uasset_files()  # .uasset 파일 목록을 가져옵니다.
        logging.info ("*"*50)
        logging.info ("config_files")
        logging.info (config_files)
        logging.info ("*"*50)
        logging.info ("*"*50)
        ue_config_paths = []  # ue_config_path를 저장할 리스트
        logging.info ("*"*50)
        logging.info ("ue_config_paths")
        logging.info (ue_config_paths)

        if config_files:
            for config_file in config_files:
                # 경로에서 역슬래시를 슬래시로 변환하고, .uasset 확장자를 제거
                ue_config_path = config_file.replace("C:\\Users\\admin\\Desktop\\Project\\pipe_test\\Content\\", "/Game/")
                ue_config_path = ue_config_path.replace("\\", "/")
                ue_config_path = ue_config_path.replace(".uasset", "")
                logging.info ("*"*50)
                logging.info ("ue_config_path")
                logging.info (ue_config_path)
                logging.info ("*"*50)
                logging.info ("*"*50)
                
                # Unreal Editor에서 MoviePipelineConfig의 해상도를 가져와 수정
                pipeline_config_asset = unreal.EditorAssetLibrary.load_asset(ue_config_path)
                if pipeline_config_asset:
                    # config(or queue) 안에 있는 job 확인
                    jobs = pipeline_config_asset.get_jobs()
                    for job in jobs:
                        # job의 렌더링 설정 가져오기
                        job_config = job.get_configuration()
                        if job_config:
                            # 해상도 설정 가져오기
                            resolution_setting = job_config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
                            if resolution_setting:
                                # 현재 해상도
                                logging.info(
                                    f"Current Resolution: "
                                    f"{resolution_setting.output_resolution.x}x{resolution_setting.output_resolution.y}"
                                    )

                                # 해상도 변경
                                new_width = 1260
                                new_height = 720
                                resolution_setting.output_resolution.x = new_width
                                resolution_setting.output_resolution.y = new_height

                                logging.info(
                                    f"Updated Resolution: "
                                    f"{resolution_setting.output_resolution.x}x{resolution_setting.output_resolution.y}"
                                    )
                            else:
                                logging.warning("No resolution setting found.")

                    # 변경 사항 저장
                    unreal.EditorAssetLibrary.save_asset(ue_config_path)
                    logging.info(f"Changes saved successfully for {ue_config_path}")

                # ue_config_path를 리스트에 추가
                ue_config_paths.append(ue_config_path)
                logging.info ("*"*50)
                logging.info ("ue_config_path")
                logging.info ("*"*50)
            else:
                logging.error(f"Failed to load queue asset: {ue_config_path}")
        else:
            logging.warning("No .uasset files found.")

        return ue_config_paths

    def generate_cmd_command(self, config_files, ue_config_paths):
        cmd_commands = []  
        for config_file in config_files:
            job_name = f"Render_{os.path.basename(config_file)}"
            for ue_config_path in ue_config_paths:
                command = (
                    f'"{self.unreal_editor_path}" '
                    f'"{self.uproject_path}" '
                    f'-game '
                    f'-NoSplash ' 
                    f'-log '
                    f'-RenderOffscreen '
                    f'-NoTextureStreaming '
                    f'-MoviePipelineConfig="{ue_config_path}"'
                )
                cmd_commands.append((job_name, command)) 

        return cmd_commands

    def submit_to_deadline(self, job_name, command):
        deadline_command = [
            "deadlinecommand",
            "-SubmitCommandLineJob",
            f"-name {job_name}",
            f"-executable {command}"
        ]
        
        try:
            result = subprocess.run(deadline_command, capture_output=True, text=True, check=True)
            logging.info("Deadline job submission successful")
            return result.stdout
        except subprocess.CalledProcessError as e:
            logging.error("Deadline job submission failed")
            logging.error(e.stderr)
            return None

    @log_execution_time
    def execute_cmd_command(self, job_name, cmd_command):
        try:
            logging.info(f"Executing command: {cmd_command}")
            subprocess.run(cmd_command, shell=True, check=True)  # check=True will raise an exception if the command fails
            logging.info(f"Submitting job '{job_name}' to Deadline")
            self.submit_to_deadline(job_name, cmd_command)
        except subprocess.CalledProcessError as e:
            logging.error(f"Error occurred while executing the command: {cmd_command}")
            logging.error(f"Return code: {e.returncode}")
            logging.error("Output:")
            logging.error(e.output)
            traceback.print_exc()
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            traceback.print_exc()

    def execute_mrq_render(self, task_id):
        logging.info("Starting script execution")
        
        self.create_shotgun_session()

        software_name = "Unreal Engine Editor"
        self.unreal_editor_path, render_args = self.get_software_info(software_name)
        
        if self.unreal_editor_path is None:
            return

        self.get_task_info(task_id)

        config_files = self.get_uasset_files()

        if self.uproject_path and self.movie_pipeline_config:
            ue_config_paths = self._get_and_set_resolution()  # 해상도 설정 업데이트

            if ue_config_paths:
                cmd_commands = self.generate_cmd_command(config_files, ue_config_paths)  # 명령어 목록 생성
                for job_name, cmd_command in cmd_commands:
                    logging.info('*' * 50)
                    logging.info(f"Generated CMD: {cmd_command}")
                    logging.info('*' * 50)
                    self.execute_cmd_command(job_name, cmd_command)
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
    render_job.execute_mrq_render(task_id=5827)
