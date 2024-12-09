import os
import subprocess
import sys
import logging
import copy
from shotgun_api3 import Shotgun
import unreal

class MrqRender:
    def __init__(self, server_url, script_name, api_key):
        self.server_url = server_url
        self.script_name = script_name
        self.api_key = api_key
        self.sg = None
        self.unreal_map_path = None
        self.sequence_path = None
        self.output_path = None
        self.movie_pipeline_config_path = None

    def create_shotgun_session(self):
        self.sg = Shotgun(self.server_url, self.script_name, self.api_key)
        logging.info("ShotGrid 세션이 생성되었습니다.")

    def get_task_info(self, task_id):
        task_data = self.sg.find_one(
            'Task', 
            [['id', 'is', task_id]], 
            ["project", 'entity.Shot.sg_ue_map', 'entity.Shot.sg_ue_level_sequence', 'entity.Shot.sg_output_path', 'entity.Shot.sg_movie_pipeline_config']
        )

        if task_data is None:
            logging.error("Task ID: {}에 대한 작업 데이터를 찾을 수 없습니다.".format(task_id))
            return None

        self.unreal_map_path = task_data['entity.Shot.sg_ue_map']
        self.sequence_path = task_data['entity.Shot.sg_ue_level_sequence']
        self.output_path = task_data['entity.Shot.sg_output_path']
        self.movie_pipeline_config_path = task_data['entity.Shot.sg_movie_pipeline_config']

        logging.info("Task ID: {}의 정보를 성공적으로 가져왔습니다.".format(task_id))
        return task_data

    def get_and_set_resolution(self, new_resolution=(1280, 720)):
        """
        MoviePipelineConfig의 해상도를 새로 설정합니다.
        :param new_resolution: 새로 설정할 해상도 (width, height)
        """
        pipeline_config_asset = unreal.EditorAssetLibrary.load_asset(self.movie_pipeline_config_path)
        
        if not pipeline_config_asset:
            logging.error(f"MoviePipelineConfig을 로드할 수 없습니다: {self.movie_pipeline_config_path}")
            return False

        # MovieRenderPipelineSettings 가져오기
        pipeline_settings = pipeline_config_asset.get_editor_property("settings")
        if not pipeline_settings:
            logging.error("MovieRenderPipelineSettings을 가져올 수 없습니다.")
            return False
        
        # 해상도 설정을 변경
        new_resolution = unreal.IntPoint(*new_resolution)
        pipeline_settings.set_editor_property("output_resolution", new_resolution)

        # 변경된 설정 저장
        unreal.EditorAssetLibrary.save_asset(self.movie_pipeline_config_path)

        logging.info(f"해상도가 {new_resolution}으로 변경되었습니다.")
        return True

    def _unreal_render_with_movie_pipeline(self):
        if not self.output_path or not self.movie_pipeline_config_path:
            logging.error("출력 경로 또는 Movie Pipeline Config 경로가 설정되지 않았습니다.")
            return False, None

        sequence_name = self.sequence_path.split("/")[-1]
        output_file = os.path.join(self.output_path, f"{sequence_name}.mov")

        if os.path.isfile(output_file):
            try:
                os.remove(output_file)
            except OSError:
                logging.error(
                    "{}을(를) 삭제할 수 없습니다. Movie Pipeline이 해당 파일에 영상을 출력할 수 없습니다.".format(output_file)
                )
                return False, None

        unreal_executable = r"C:\Program Files\Epic Games\UE_5.4\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
        cmdline_args = [
            unreal_executable,
            "%s" % os.path.join(
                unreal.SystemLibrary.get_project_directory(),
                "%s.uproject" % unreal.SystemLibrary.get_game_name(),
            ),
            self.unreal_map_path,
            "-MoviePipelineConfig=%s" % self.movie_pipeline_config_path,
            "-MovieFolder=%s" % self.output_path,
            "-MovieName=%s" % sequence_name,
            "-game",
            "-NoTextureStreaming",
            "-NoLoadingScreen",
            "-NoScreenMessages",
            "-RenderOffscreen",
            "-noSplash"
        ]

        logging.info("Movie Pipeline 렌더링 명령어 인자: {}".format(" ".join(cmdline_args)))

        run_env = copy.copy(os.environ)
        if "UE_SHOTGUN_BOOTSTRAP" in run_env:
            del run_env["UE_SHOTGUN_BOOTSTRAP"]
        if "UE_SHOTGRID_BOOTSTRAP" in run_env:
            del run_env["UE_SHOTGRID_BOOTSTRAP"]

        return_code = subprocess.call(cmdline_args, env=run_env)
        if return_code != 0:
            logging.error(f"Unreal Engine 렌더링 명령어 실행 실패. 반환 코드: {return_code}")
            return False, None

        if os.path.isfile(output_file):
            return True, output_file
        else:
            logging.error("렌더링 후 출력 파일을 찾을 수 없습니다.")
            return False, None

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    render_job = MrqRender(
        server_url="https://hg.shotgrid.autodesk.com", 
        script_name="hyo", 
        api_key="4yhreigsfqmwlsz%yfnfuqqYo"
    )
    render_job.create_shotgun_session()
    task_id = 5827
    task_info = render_job.get_task_info(task_id)
    if task_info:
        # 해상도 설정 업데이트
        render_job.get_and_set_resolution(new_resolution=(1280, 720))
        
        success, movie_path = render_job._unreal_render_with_movie_pipeline()
        if success:
            logging.info(f"렌더링 성공! 출력 파일: {movie_path}")
        else:
            logging.error("렌더링 실패")
