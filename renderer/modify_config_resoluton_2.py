import os
import subprocess
import traceback
import time
import sys
import unreal

# Decorator for logging execution time
def log_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time for {func.__name__}: {execution_time:.2f} seconds")
        return result
    return wrapper

class MrqRender:
    def __init__(self):
        self.unreal_editor_path = None  
        self.render_args = None
        self.uproject_path = None
        self.config_dir = None

        # 절대 경로로 로그 파일 설정
        self.log_filename = os.path.join(os.getcwd(), r"C:\Users\admin\.repo\unreal\renderer\render_script.log")

        print("RenderScript initialized")

    def load_assets(self):
        if not self.config_dir:
            print("Movie pipeline config not set.")
            return []

        print(f"Loading assets from movie pipeline config: {self.config_dir}")
        asset_paths = unreal.EditorAssetLibrary.list_assets(self.config_dir, recursive=True, include_folder=True)
        queues = list(reversed([path.split('.')[0] for path in asset_paths if not path.endswith('/')]))

        print(f"Filtered asset paths: {queues}")

        for queue in queues:
            queue_asset = unreal.EditorAssetLibrary.load_asset(queue)

            if queue_asset:
                jobs = queue_asset.get_jobs()
                for job in jobs:
                    config = job.get_configuration()
                    if config:
                        resolution_setting = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
                        if resolution_setting:
                            print ("*"*150)
                            print ("*"*150)
                            print(f"Current Resolution: {resolution_setting.output_resolution.x}x{resolution_setting.output_resolution.y}")
                            new_width = 100
                            new_height = 200    
                            resolution_setting.output_resolution.x = new_width
                            resolution_setting.output_resolution.y = new_height
                            print(f"Updated Resolution: {resolution_setting.output_resolution.x}x{resolution_setting.output_resolution.y}")
                            print ("*"*150)
                            print ("*"*150)

                try:
                    # 변경 사항 저장
                    if unreal.EditorAssetLibrary.save_loaded_asset(queue_asset):
                        print(f"Changes saved successfully for asset: {queue}")
                        
                        # 저장 후 패키지 강제 저장
                        package = unreal.load_package(queue)
                        unreal.EditorLoadingAndSavingUtils.save_packages(packages_to_save=[package], only_dirty=False)  # package는 리스트로 전달
                except Exception as e:
                    print(f"Error saving package for asset {queue}: {e}")
            else:
                print(f"Failed to load asset: {queue}")

        print ("Filtered queues:", queues)
        return queues

    # Generate command string for Unreal Engine render
    def generate_cmd_command(self, queue):
        command = [
            sys.executable,
            "%s" % os.path.join(
                unreal.SystemLibrary.get_project_directory(),
                "%s.uproject" % unreal.SystemLibrary.get_game_name(),
            ),  # Unreal project
            "-game",
            "-NoSplash",
            "-log",
            "-RenderOffscreen",
            "-NoTextureStreaming",
            f'-MoviePipelineConfig={queue}'  # queue는 이미 적절한 경로 또는 인스턴스를 제공한다고 가정
        ]
        print(f"Generated command: {command}")
        return command

    # Main execution method for the render task
    @log_execution_time
    def execute_mrq_render(self):
        try:
            print(f"Starting MRQ render...")

            # 1. 에셋 로드 및 필터링
            queues = self.load_assets()
            if not queues:
                print("No valid asset paths found for rendering.")
                return

            # 2. 각 필터링된 에셋 경로에 대해 명령어 생성 및 실행
            for queue in queues:
                print(f"Processing asset: {queue}")

                # Unreal Engine 명령어 생성
                cmd_command = self.generate_cmd_command(queue)
                if cmd_command:
                    print(f"Executing command for asset: {queue}")

                    # 명령어 실행 (여기서는 출력으로 대체, 필요 시 subprocess로 실행 가능)
                    print(cmd_command)

                    # 실제 명령어 실행 코드 (주석 해제 시 활성화)
                    # subprocess.run(cmd_command, shell=True)

            print("All render jobs executed successfully.")
        except Exception as e:
            print(f"Error executing MRQ render: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    render_job = MrqRender()
    render_job.execute_mrq_render()
