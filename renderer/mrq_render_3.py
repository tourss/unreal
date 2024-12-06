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

    def create_shotgun_session(self):
        """
        ShotGrid 세션을 생성하고 연결합니다.
        """
        self.sg = Shotgun(self.server_url, self.script_name, self.api_key)
        logging.info("ShotGrid 세션이 생성되었습니다.")

    def get_task_info(self, task_id):
        """
        주어진 task_id에 대한 ShotGrid 작업 정보를 가져옵니다.
        :param task_id: ShotGrid에서 사용할 작업 ID
        """
        task_data = self.sg.find_one(
            'Task', 
            [['id', 'is', task_id]], 
            ["project", 'entity.Shot.sg_ue_map', 'entity.Shot.sg_ue_level_sequence', 'entity.Shot.sg_output_path']
        )

        if task_data is None:
            logging.error("Task ID: {}에 대한 작업 데이터를 찾을 수 없습니다.".format(task_id))
            return None

        # sg_output_path, sg_ue_map, sg_level_sequence 경로 할당
        self.unreal_map_path = task_data['entity.Shot.sg_ue_map']  # '/Game/Scene_Saloon/Maps/Historic_Saloon'
        self.sequence_path = task_data['entity.Shot.sg_ue_level_sequence']  # '/Game/Scene_Saloon/Sequences/His_Sal_Seq_01'
        self.output_path = task_data['entity.Shot.sg_output_path']  

        logging.info("Task ID: {}의 정보를 성공적으로 가져왔습니다.".format(task_id))
        return task_data

    def _unreal_render_sequence_with_sequencer(self):
        """
        주어진 시퀀스를 Level Sequencer를 사용하여 렌더링합니다.
        :returns: 렌더링 성공 여부와 생성된 영화 파일의 경로
        """
        if not self.output_path:
            logging.error("출력 경로가 설정되지 않았습니다.")
            return False, None

        # 시퀀스 이름을 추출
        sequence_name = self.sequence_path.split("/")[-1]  # '/Game/Scene_Saloon/Sequences/His_Sal_Seq_01'에서 'His_Sal_Seq_01'을 추출

        # 최종 출력 파일 경로 설정 (확장자는 .mov)
        output_file = os.path.join(self.output_path, f"{sequence_name}.mov")

        # 기존에 파일이 있으면 삭제
        if os.path.isfile(output_file):
            try:
                os.remove(output_file)
            except OSError:
                logging.error(
                    "{}을(를) 삭제할 수 없습니다. Sequencer가 해당 파일에 영화를 출력할 수 없습니다.".format(output_file)
                )
                return False, None

        unreal_executable = r"C:\Program Files\Epic Games\UE_5.4\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
        cmdline_args = [
            unreal_executable,
            "%s" % os.path.join(
                unreal.SystemLibrary.get_project_directory(),
                "%s.uproject" % unreal.SystemLibrary.get_game_name(),
            ),
            self.unreal_map_path,  # '/Game/Scene_Saloon/Maps/Historic_Saloon' 
            "-LevelSequence=%s" % self.sequence_path,  # '/Game/Scene_Saloon/Sequences/His_Sal_Seq_01'
            "-MovieFolder=%s" % self.output_path,
            "-MovieName=%s" % sequence_name,  # 시퀀스 이름을 출력 파일명으로 사용
            "-game",
            # "-MovieSceneCaptureType=/Script/MovieSceneCapture.AutomatedLevelSequenceCapture",
            # FFmpeg 관련 설정
            "-FFmpegEncoderPath=C:\ffmpeg\bin\ffmpeg.exe",  # FFmpeg 경로 설정
            "-FFmpegEncoderOptions=-c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le -c:a pcm_s16le",  # FFmpeg 인코더 옵션 설정
            "-ResX=1280",
            "-ResY=720",
            "-ForceRes",s
            "-MovieCinematicMode=yes",
            "-MovieFormat=mov",  # mov 형식으로 변경
            "-MovieFrameRate=24",
            "-MovieQuality=75",
            "-NoTextureStreaming",
            "-NoLoadingScreen",
            "-NoScreenMessages",
            "-RenderOffscreen",
            "-noSplash"
        ]


        logging.info("Sequencer 명령어 인자: {}".format(" ".join(cmdline_args)))

        # 환경 변수 복사 및 ShotGrid 관련 환경 변수 제거
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
    logging.basicConfig(level=logging.DEBUG)  # 로그 레벨을 DEBUG로 설정
    render_job = MrqRender(
        server_url="https://hg.shotgrid.autodesk.com", 
        script_name="hyo", 
        api_key="4yhreigsfqmwlsz%yfnfuqqYo"
    )
    render_job.create_shotgun_session()
    task_id = 5827  # 예시 Task ID
    task_info = render_job.get_task_info(task_id)
    if task_info:
        success, movie_path = render_job._unreal_render_sequence_with_sequencer()
        if success:
            logging.info(f"렌더링 성공! 출력 파일: {movie_path}")
        else:
            logging.error("렌더링 실패")
