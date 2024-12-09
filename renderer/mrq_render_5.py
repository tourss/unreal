import os
import unreal
import subprocess
from shotgun_api3 import Shotgun
import logging
import sys

class MrqRender:
    def __init__(self, server_url, script_name, api_key, logger=None):
        self.server_url = server_url
        self.script_name = script_name
        self.api_key = api_key
        self.shotgrid_session = None
        self.logger = logger or logging.getLogger(__name__)

        log_folder = r'C:\Users\admin\.repo\unreal\renderer'
        log_file = os.path.join(log_folder, 'mrq_render_log.txt')

        if not os.path.exists(log_folder):
            os.makedirs(log_folder)  # 폴더가 없으면 생성

        logging.basicConfig(
            level=logging.DEBUG,  # 로그 레벨 설정
            format='%(asctime)s - %(levelname)s - %(message)s',  # 로그 포맷
            handlers=[
                logging.FileHandler(log_file),  # 로그 파일에 기록
                logging.StreamHandler()  # 콘솔에 출력
            ]
        )

        self.logger = logging.getLogger(__name__)
        
        self.logger.info("MRQ Render 인스턴스가 생성되었습니다.")

    def create_shotgun_session(self):
        """
        ShotGrid 세션을 생성합니다.
        """
        try:
            self.shotgrid_session = Shotgun(self.server_url, self.script_name, self.api_key)
            self.logger.info("ShotGrid 세션이 성공적으로 생성되었습니다.")
        except Exception as e:
            self.logger.error(f"ShotGrid 세션 생성 실패: {e}")
            raise

    def get_task_info(self, task_id):
        """
        주어진 task_id에 해당하는 작업 정보를 가져옵니다.
        """
        try:
            task_data = self.shotgrid_session.find_one(
                'Task',
                [['id', 'is', task_id]],
                ['project', 'entity.Shot.sg_ue_map', 'entity.Shot.sg_ue_level_sequence', 'entity.Shot.sg_output_path']
            )
            
            if task_data:
                self.logger.info(f"Task ID {task_id}에 대한 작업 정보 가져오기 성공.")
                return task_data
            else:
                self.logger.error(f"Task ID {task_id}에 대한 작업 정보를 찾을 수 없습니다.")
                return None
        except Exception as e:
            self.logger.error(f"Task 정보 가져오기 실패: {e}")
            return None

    def generate_movie_pipeline_job(self, sequence_path, unreal_map_path, output_path):
        """
        MoviePipelineExecutorJob 객체를 생성하여 반환합니다.
        """
        # MoviePipelineQueueEngineSubsystem을 통해 MoviePipelineQueue를 가져옵니다.
        queue_subsystem = unreal.get_engine_subsystem(unreal.MoviePipelineQueueEngineSubsystem)
        queue = queue_subsystem.get_queue()

        # 새로운 MoviePipelineExecutorJob 생성
        job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)  # `allocate_new_job()` 사용

        # Job에 시퀀스와 맵 설정
        job.sequence = unreal.SoftObjectPath(sequence_path)
        job.map = unreal.SoftObjectPath(unreal_map_path)

        # Output 설정
        config = job.get_configuration()
        output_folder, output_filename = os.path.split(output_path)
        movie_name = os.path.splitext(output_filename)[0]

        output_setting = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
        output_setting.output_directory = unreal.DirectoryPath(output_folder)
        output_setting.file_name_format = movie_name
        output_setting.override_existing_output = True

        # 렌더링 설정 추가
        self._add_render_settings(config)

        # Job이 큐에 자동으로 추가됨 (allocate_new_job()에서 처리)
        return job  # 생성한 job 객체를 반환
    
    def _add_render_settings(self, config):
        """
        렌더링 설정을 MoviePipelineConfig에 추가합니다.
        """
        config.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
        config.find_or_add_setting_by_class(unreal.MoviePipelineAppleProResOutput)

    def _build_render_command(self, job):
        """
        Unreal Engine 렌더링 명령어를 생성합니다.
        """
        # MoviePipelineQueue에 작업이 추가되었으므로, MoviePipelineQueue를 통해 명령어 생성
        queue_subsystem = unreal.get_engine_subsystem(unreal.MoviePipelineQueueEngineSubsystem)
        queue = queue_subsystem.get_queue()
        job_index = queue.get_job_index(job)  # Job의 인덱스를 얻을 수 있음

        # Movie Pipeline 명령어를 생성
        render_command = [
            sys.executable,
            os.path.join(unreal.SystemLibrary.get_project_directory(), f"{unreal.SystemLibrary.get_game_name()}.uproject"),
            "MoviePipelineEntryMap?game=/Script/MovieRenderPipelineCore.MoviePipelineGameMode",
            "-game",
            "-Multiprocess",
            "-NoLoadingScreen",
            "-FixedSeed",
            "-log",
            "-Unattended",
            "-messaging",
            "-SessionName=\"Publish2 Movie Render\"",
            "-nohmd",
            "-windowed",
            "-ResX=1280",
            "-ResY=720",
            "-execcmds=r.HLOD 0",
            f"-MoviePipelineJob={job_index}"  # Job 인덱스를 사용하여 MoviePipelineJob을 실행
        ]

        return render_command

    def submit_to_deadline(self, command):
        """
        Deadline에 렌더링 작업을 제출합니다.
        """
        deadline_command = f"deadlinecommand {command}"
        self.logger.info(f"Submitting to Deadline: {deadline_command}")
        subprocess.call(deadline_command, shell=True)

    def render(self, task_id):
        """
        렌더링 작업을 실행합니다.
        """
        # Task ID에 대한 작업 정보 가져오기
        task_data = self.get_task_info(task_id)
        
        if not task_data:
            return False, None

        # 렌더링을 위한 경로 및 파일 이름 구성
        sequence_path = task_data.get('entity.Shot.sg_ue_level_sequence', None)
        unreal_map_path = task_data.get('entity.Shot.sg_ue_map', None)
        output_path = task_data.get('entity.Shot.sg_output_path', None)

        if not sequence_path or not unreal_map_path or not output_path:
            self.logger.error(f"필수 정보가 누락되었습니다: Sequence Path: {sequence_path}, Map Path: {unreal_map_path}, Output Path: {output_path}")
            return False, None

        # Movie Pipeline Job 생성
        job = self.generate_movie_pipeline_job(sequence_path, unreal_map_path, output_path)

        # 렌더링 명령어 생성
        render_command = self._build_render_command(job)

        # 렌더링 명령어 실행
        success = subprocess.call(render_command) == 0
        
        if success:
            self.submit_to_deadline(render_command)

        return success, output_path


# 샷그리드 API 정보
server_url = "https://hg.shotgrid.autodesk.com"
script_name = "hyo"
api_key = "4yhreigsfqmwlsz%yfnfuqqYo"

# 렌더링 인스턴스 생성
renderer = MrqRender(server_url, script_name, api_key)

# ShotGrid 세션 생성
renderer.create_shotgun_session()

# Task ID에 해당하는 작업 정보 가져오기
task_id = 5827  # 실제 작업 ID로 교체
task_data = renderer.get_task_info(task_id)

if task_data:
    # MRQ 렌더링 실행
    success, output_file = renderer.render(task_id)

    if success:
        print(f"렌더링 성공! 출력 파일: {output_file}")
    else:
        print("렌더링 실패.")
else:
    print("작업 정보 가져오기에 실패했습니다.")
