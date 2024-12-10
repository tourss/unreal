import os
import subprocess
import sys
import logging
from shotgun_api3 import Shotgun
import unreal

class MrqRender:
    def __init__(self, server_url, script_name, api_key):
        self.server_url = server_url
        self.script_name = script_name
        self.api_key = api_key
        self.sg = None

        # Logger 설정
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def create_shotgun_session(self):
        """
        ShotGrid 세션을 생성하고 연결합니다.
        """
        self.sg = Shotgun(self.server_url, self.script_name, self.api_key)
        self.logger.info("ShotGrid 세션이 생성되었습니다.")

    def get_task_info(self, task_id):
        """
        주어진 task_id에 해당하는 작업 정보를 가져옵니다.
        """
        try:
            task_data = self.sg.find_one(
                'Task',
                [['id', 'is', task_id]],
                [
                    'project',
                    'entity.Shot.sg_ue_map',
                    'entity.Shot.sg_ue_level_sequence',
                    'entity.Shot.sg_output_path',
                    'entity.Shot.sg_movie_pipeline_config'
                ]
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
        Movie Pipeline Job 객체를 생성합니다.
        """
        queue_subsystem = unreal.get_engine_subsystem(unreal.MoviePipelineQueueEngineSubsystem)
        queue = queue_subsystem.get_queue()

        # Map 로드
        unreal.EditorLoadingAndSavingUtils.load_map(unreal_map_path)

        # Job 생성
        job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
        job.map = unreal.SoftObjectPath(unreal_map_path)
        job.sequence = unreal.SoftObjectPath(sequence_path)
        job.author = "ShotGrid Integration"

        # 출력 경로 설정
        job.job_name = "ShotGrid Render Job"
        job.set_output_directory(output_path)

        return job

    def _build_render_command(self, job, config_path=None):
        """
        Unreal Engine 렌더링 명령어를 생성합니다.
        """
        queue_subsystem = unreal.get_engine_subsystem(unreal.MoviePipelineQueueEngineSubsystem)
        queue = queue_subsystem.get_queue()
        job_index = queue.get_job_index(job)

        render_command = [
            "C:/Program Files/Epic Games/UE_5.4/Engine/Binaries/Win64/UnrealEditor-Cmd.exe",
            os.path.join(unreal.SystemLibrary.get_project_directory(), f"{unreal.SystemLibrary.get_game_name()}.uproject"),
            "MoviePipelineEntryMap?game=/Script/MovieRenderPipelineCore.MoviePipelineGameMode",
            "-game",
            "-Multiprocess",
            "-NoLoadingScreen",
            "-FixedSeed",
            "-log",
            "-Unattended",
            "-messaging",
            "-nohmd",
            "-windowed",
            "-ResX=1280",
            "-ResY=720",
            "-execcmds=r.HLOD 0",
            f"-MoviePipelineJob={job_index}"
        ]

        if config_path:
            render_command.append(f"-MoviePipelineConfig={config_path}")

        return render_command

    def submit_to_deadline(self, render_command):
        """
        Deadline에 렌더 작업을 제출합니다.
        """
        deadline_command = "C:/DeadlinePath/deadlinecommand.exe"
        submission_args = ["SubmitCommandLineJob"] + render_command
        try:
            subprocess.call([deadline_command] + submission_args)
            self.logger.info("Deadline에 작업 제출 성공.")
        except Exception as e:
            self.logger.error(f"Deadline 작업 제출 실패: {e}")

    def render(self, task_id):
        """
        렌더링 작업을 실행합니다.
        """
        task_data = self.get_task_info(task_id)
        if not task_data:
            return False, None

        sequence_path = task_data.get('entity.Shot.sg_ue_level_sequence', None)
        unreal_map_path = task_data.get('entity.Shot.sg_ue_map', None)
        output_path = task_data.get('entity.Shot.sg_output_path', None)
        config_path = task_data.get('entity.Shot.sg_movie_pipeline_config', None)

        if not sequence_path or not unreal_map_path or not output_path:
            self.logger.error(f"필수 정보가 누락되었습니다: Sequence Path: {sequence_path}, Map Path: {unreal_map_path}, Output Path: {output_path}")
            return False, None

        job = self.generate_movie_pipeline_job(sequence_path, unreal_map_path, output_path)
        render_command = self._build_render_command(job, config_path=config_path)

        success = subprocess.call(render_command) == 0
        if success:
            self.submit_to_deadline(render_command)

        return success, output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    render_job = MrqRender(
        server_url="https://hg.shotgrid.autodesk.com",
        script_name="hyo",
        api_key="4yhreigsfqmwlsz%yfnfuqqYo"
    )
    render_job.create_shotgun_session()
    task_id = 5827
    success, movie_path = render_job.render(task_id)
    if success:
        logging.info(f"렌더링 성공! 출력 파일: {movie_path}")
    else:
        logging.error("렌더링 실패")
