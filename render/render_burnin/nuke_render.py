import os
import json
from shotgun_api3 import Shotgun

class VerifyEXRFileNames:
    def __init__(self, server_url, script_name, api_key, exr_directory):
        # ShotGrid 서버 URL과 인증 정보
        self.server_url = server_url
        self.script_name = script_name
        self.api_key = api_key
        self.exr_directory = exr_directory

        # ShotGrid 세션
        self.sg = None  
        self.level_sequence = None

    def create_shotgun_session(self):
        """ShotGrid API 세션 생성"""
        self.sg = Shotgun(self.server_url, self.script_name, self.api_key)

    def get_shot_info(self, task_id):
        """ShotGrid에서 해당 task ID에 대한 샷 정보 가져오기"""
        task = self.sg.find_one(
            "Task",
            [["id", "is", task_id]],
            ["entity.Shot.sg_ue_level_sequence"]
        )
        if task is not None:
            self.level_sequence = task.get("entity.Shot.sg_ue_level_sequence")
        else:
            raise ValueError(f"Task ID {task_id}에 해당하는 샷 정보를 찾을 수 없습니다.")

    def get_exr_files(self):
        """EXR 파일을 지정된 디렉토리에서 찾아 리스트로 반환"""
        exr_files = []  # 유효한 EXR 파일 리스트를 저장할 변수
    
        if os.path.exists(self.exr_directory):
            # 디렉토리 내 파일 목록 가져오기
            for f in os.listdir(self.exr_directory):
                # EXR 파일만 처리
                if f.lower().endswith(".exr"):
                    exr_file_path = os.path.join(self.exr_directory, f)
                    # EXR 파일 이름 추출 (확장자 제외)
                    exr_filename = os.path.basename(exr_file_path)
                    exr_name = exr_filename.split('.')[0]  # 'name.####.exr'에서 name 부분만 추출
                    
                    # sg_ue_level_sequence와 비교
                    if exr_name == self.level_sequence:
                        exr_files.append(exr_file_path)  # 유효한 파일만 exr_files에 추가
        else:
            raise FileNotFoundError(f"디렉토리 {self.exr_directory}가 존재하지 않습니다.")
        
        return exr_files

    def verify_exr_filenames(self, exr_files):
        """EXR 파일 이름과 ShotGrid의 level sequence가 일치하는지 확인"""
        if self.level_sequence:
            valid_files = []
            for exr_file in exr_files:
                exr_filename = os.path.splitext(os.path.basename(exr_file))[0]
                exr_name = exr_filename.split('.')[0]  # 'name.####.exr'에서 name 부분만 추출
                if exr_name == self.level_sequence:
                    valid_files.append(exr_file)
            return valid_files
        else:
            raise ValueError("No level sequence found to compare EXR files.")
            
    def save_exr_files_to_json(self, exr_files):   #디버깅으로 exr_files의 출력값이 다 나오지 않아서 추가한 함수
        """exr_files를 JSON 파일로 저장"""
        output_file = "exr_files.json"  # 현재 디렉토리에 저장
        with open(output_file, 'w') as json_file:
            json.dump(exr_files, json_file, indent=4)
        print(f"EXR 파일 목록을 '{output_file}'에 저장했습니다.")

    def execute(self, task_id):
        """전체 작업을 실행하는 함수"""
        # ShotGrid 세션 생성
        self.create_shotgun_session()

        # ShotGrid에서 해당 task에 대한 샷 정보 가져오기
        self.get_shot_info(task_id)

        # EXR 파일 검색
        exr_files = self.get_exr_files()

        if exr_files:
            # EXR 파일 이름이 level_sequence와 일치하는지 확인
            valid_files = self.verify_exr_filenames(exr_files)
            # 유효한 EXR 파일을 JSON 파일로 저장
            self.save_exr_files_to_json(valid_files)
            return valid_files
        else:
            return []

if __name__ == "__main__":
    # 사용자 설정: ShotGrid 서버 URL, 스크립트 이름, API 키, EXR 파일이 있는 디렉토리
    server_url = "https://hg.shotgrid.autodesk.com"
    script_name = "hyo"
    api_key = "4yhreigsfqmwlsz%yfnfuqqYo"
    exr_directory = "C:\\Users\\admin\\Desktop\\Project\\pipe_test\\Saved\\MovieRenders\\test_1"

    task_id = 5827  # 실제 태스크 ID로 변경

    # EXR 파일 이름 검증 실행
    verify_exr = VerifyEXRFileNames(server_url, script_name, api_key, exr_directory)
    valid_exr_files = verify_exr.execute(task_id)
    
    # 유효한 EXR 파일들 출력
    # print(f"Valid EXR files: {valid_exr_files}")


# 상단: 파일이름 (왼쪽) / 프로젝트명(샷그리드기준, 가운데) / pub시간 (오른쪽)
# 하단: 프레임넘버 (왼쪽) / 메시지 (가운데) / 작업자명 (오른쪽)