import os
import logging
from shotgun_api3 import Shotgun
import unreal

class MrqRender:
    def __init__(self, server_url, script_name, api_key):
        """
        :param server_url: ShotGrid 서버 URL
        :param script_name: ShotGrid 스크립트 이름
        :param api_key: ShotGrid API 키
        """
        self.server_url = server_url
        self.script_name = script_name
        self.api_key = api_key
        self.sg = None
        self.unreal_map_path = None
        self.sequence_path = None
        self.output_path = None  # output_path 초기화

    def create_shotgun_session(self):
        """
        ShotGrid 세션을 생성하고 연결합니다.
        """
        logging.info(f"서버 URL: {self.server_url}")
        logging.info(f"스크립트 이름: {self.script_name}")
        logging.info(f"API 키: {self.api_key}")

        # 서버 URL이 올바르게 지정되었는지 확인
        if not isinstance(self.server_url, str) or not self.server_url:
            logging.error("유효하지 않은 서버 URL입니다.")
            return
        
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
        self.output_path = task_data['entity.Shot.sg_output_path']  # 'C:/Users/admin/Desktop/Project/render_output'

        logging.info("Task ID: {}의 정보를 성공적으로 가져왔습니다.".format(task_id))
        return task_data

    def render(self):
        """
        Movie Render Queue를 사용하여 렌더링 작업을 실행합니다.
        :returns: 렌더링 성공 여부와 출력 파일 경로
        """
        if not self.output_path:
            logging.error("출력 경로가 설정되지 않았습니다.")
            return False, None

        # Movie Render Queue Subsystem 가져오기
        mrq_subsystem = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
        
        # Queue 생성
        queue = mrq_subsystem.get_queue()

        # 새 작업 추가
        job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)

        # Map, Sequence 설정
        job.map = unreal.SoftObjectPath(self.unreal_map_path)
        job.sequence = unreal.SoftObjectPath(self.sequence_path)

        # Job 이름 설정
        sequence_name = os.path.basename(self.sequence_path)  # 시퀀스 이름 추출
        job.job_name = f"Render_{sequence_name}"

        # 출력 경로 및 설정
        output_setting = job.get_configuration().find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
        output_setting.output_directory = unreal.DirectoryPath(self.output_path)
        output_setting.file_name_format = f"{sequence_name}"
        output_setting.output_resolution = unreal.IntPoint(1920, 1080)  # 해상도 설정

        # 렌더 품질 설정
        aa_setting = job.get_configuration().find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
        aa_setting.spatial_sample_count = 1
        aa_setting.temporal_sample_count = 1

        # Executor 인스턴스 생성
        executor = unreal.MoviePipelinePythonHostExecutor()  # Executor 생성

        # Movie Render Queue 실행
        mrq_subsystem.render_queue_with_executor_instance(executor)  # Executor를 전달하여 렌더링 시작

        # 렌더 완료 대기
        while executor.is_rendering():
            unreal.SystemLibrary.delay(1.0)  # 1초 대기

        if executor.is_rendering() is False:
            output_file = os.path.join(self.output_path, f"{sequence_name}.mov")
            if os.path.isfile(output_file):
                logging.info(f"렌더링 완료: {output_file}")
                return True, output_file
            else:
                logging.error("렌더링 후 출력 파일을 찾을 수 없습니다.")
                return False, None
        else:
            logging.error("Movie Render Queue 렌더링이 취소되었습니다.")
            return False, None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    server_url = "https://hg.shotgrid.autodesk.com"
    script_name = "hyo"
    api_key = "4yhreigsfqmwlsz%yfnfuqqYo"

    renderer = MrqRender(server_url, script_name, api_key)

    # ShotGrid 세션 생성
    renderer.create_shotgun_session()

    # Task ID에 해당하는 작업 정보 가져오기
    task_id = 5827  # 실제 작업 ID로 교체
    task_data = renderer.get_task_info(task_id)

    if task_data:
        # MRQ 렌더링 실행
        success, output_file = renderer.render()

        if success:
            print(f"렌더링 성공! 출력 파일: {output_file}")
        else:
            print("렌더링 실패.")
    else:
        print("작업 정보 가져오기에 실패했습니다.")

