import os
from shotgun_api3 import Shotgun
import nuke

class NukeRender:
    def __init__(self, server_url, script_name, api_key, exr_directory, output_base_directory):
        # ShotGrid 설정
        self.server_url = server_url
        self.script_name = script_name
        self.api_key = api_key

        # 파일 경로 설정
        self.exr_directory = exr_directory
        self.output_base_directory = output_base_directory

        # ShotGrid 세션
        self.sg = None
        self.level_sequence = None

    def create_shotgun_session(self):
        """ShotGrid API 세션 생성"""
        self.sg = Shotgun(self.server_url, self.script_name, self.api_key)

    def get_shot_info(self, task_id):
        """ShotGrid에서 해당 Task ID에 대한 샷 정보 가져오기"""
        task = self.sg.find_one(
            "Task",
            [["id", "is", task_id]],
            ["entity.Shot.sg_ue_level_sequence"]
        )
        if task is not None:
            self.level_sequence = task.get("entity.Shot.sg_ue_level_sequence")
        else:
            raise ValueError(f"Task ID {task_id}에 대한 샷 정보를 찾을 수 없습니다.")

    def get_exr_files(self):
        """EXR 파일을 지정된 디렉토리에서 검색하고 level_sequence와 비교"""
        exr_files = []
        if os.path.exists(self.exr_directory):
            for f in os.listdir(self.exr_directory):
                if f.lower().endswith(".exr"):
                    exr_file_path = os.path.join(self.exr_directory, f)
                    exr_name = os.path.basename(exr_file_path).split('.')[0]
                    if exr_name == self.level_sequence:
                        exr_files.append(exr_file_path)
        else:
            raise FileNotFoundError(f"디렉토리 {self.exr_directory}가 존재하지 않습니다.")
        if not exr_files:
            raise ValueError(f"'{self.level_sequence}'와 일치하는 EXR 파일을 찾을 수 없습니다.")
        return exr_files

    def project_setting(self, start_frame, last_frame):
        """
        **설정값들은 추후 Shotgrid에서 가져오도록 변경**
        """
        # frame 설정
        nuke.root()["first_frame"].setValue(int(start_frame))
        nuke.root()["last_frame"].setValue(int(last_frame))

        # color 설정
        nuke.root()["colorManagement"].setValue("OCIO")
        nuke.root()["OCIO_config"].setValue("aces_1.2")
        nuke.root()["workingSpaceLUT"].setValue("ACES - ACES2065-1")

    def create_read_node(self, exr_files):
        """Read 노드 생성 후 EXR 파일 경로 입력"""
        # 첫 번째 EXR 파일의 이름에서 프레임 번호를 추출
        exr_name = os.path.basename(exr_files[0]).split('.')[0]
        exr_input = os.path.join(self.exr_directory, f"{exr_name}.####.exr")
        exr_input = exr_input.replace("\\", "/")

        # Read 노드 생성
        read_node = nuke.createNode("Read")
        read_node["file"].setValue(exr_input)

        # EXR 파일 이름에서 프레임 번호를 추출하여 정렬
        frame_numbers = []
        for exr_file in exr_files:
            file_name = os.path.basename(exr_file)
            frame_number_str = file_name.split('.')[-2]
            if frame_number_str != "0000":
                frame_numbers.append(int(frame_number_str))

        # 첫 번째 프레임과 마지막 프레임을 찾음
        start_frame = min(frame_numbers)
        end_frame = max(frame_numbers)   

        # Read 노드에서 프레임 범위 자동으로 설정
        read_node["first"].setValue(int(start_frame))
        read_node["last"].setValue(int(end_frame))

        return start_frame, end_frame, exr_name
    
    def create_write_node(self, exr_name, start_frame, end_frame):
        """MOV 파일로 출력을 위한 Write 노드를 생성"""

        # 버전 관리: 기존에 동일한 이름의 파일이 있는지 확인하고 버전 번호 증가
        version_str = self.version_control(exr_name)

        # 출력 MOV 파일 경로 설정
        output_mov_path = os.path.join(self.output_base_directory, f"{exr_name}.v{version_str}.mov")
        output_mov_path = output_mov_path.replace("\\", "/")

        # Write 노드 설정
        write_node = nuke.createNode("Write") 
        write_node["file"].setValue(output_mov_path)
        write_node["file_type"].setValue("mov")
        write_node["mov64_codec"].setValue("apch")  # Apple ProRes 422 설정
        # write_node["mov_prores_codec_profile"].setValue("ProRes 4444")

        # Write 노드의 frame range 설정
        write_node["first"].setValue(int(start_frame))
        write_node["last"].setValue(int(end_frame))

        write_node["transformType"].setValue("colorspace")
        write_node["colorspace"].setValue("Output - Rec.709")

        return write_node

    def setup_nodes(self, exr_files):
        """Nuke에서 노드를 설정하여 EXR 파일을 입력받고 MOV로 출력"""
        start_frame, end_frame, exr_name = self.create_read_node(exr_files)
        #프로젝트 frame range 설정
        self.project_setting(start_frame, end_frame)

        write_node = self.create_write_node(exr_name, start_frame, end_frame)
        return write_node, start_frame, end_frame

    def render(self, write_node, start_frame, end_frame):
        """Nuke에서 렌더링 실행"""
        nuke.execute(write_node, start_frame, end_frame)

    def version_control(self, exr_name):
        """기존 버전이 있다면 +1씩 증가시키는 함수"""
        version = 1
        base_path = self.output_base_directory

        while True:
            version_str = f"{version:03}"
            output_file = os.path.join(base_path, f"{exr_name}.v{version_str}.mov")
            if not os.path.exists(output_file):
                break
            version += 1
        return version_str

    def execute(self, task_id):
        """전체 작업 실행"""
        # ShotGrid API 세션 생성
        self.create_shotgun_session()

        # Shot 정보 가져오기
        self.get_shot_info(task_id)

        # EXR 파일 가져오기
        exr_files = self.get_exr_files()

        # Nuke 노드 설정 및 렌더링
        write_node, start_frame, end_frame = self.setup_nodes(exr_files)
        self.render(write_node, start_frame, end_frame)
        print(f"렌더링 완료: {write_node['file'].value()}")


if __name__ == "__main__":
    # 사용자 설정
    server_url = "https://hg.shotgrid.autodesk.com"
    script_name = "hyo"
    api_key = "4yhreigsfqmwlsz%yfnfuqqYo"
    exr_directory = "C:\\Users\\admin\\Desktop\\Project\\pipe_test\\Saved\\MovieRenders\\test_1"
    output_base_directory = "C:\\Users\\admin\\Desktop\\Project\\render_output\\"
    task_id = 5827  # ShotGrid 태스크 ID

    # 렌더 실행
    renderer = NukeRender(server_url, script_name, api_key, exr_directory, output_base_directory)
    renderer.execute(task_id)
