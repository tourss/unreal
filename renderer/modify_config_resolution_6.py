import logging
from logging import handlers
import os
import subprocess
import traceback
import time
import datetime
import sys
import unreal
from concurrent.futures import ThreadPoolExecutor

# Decorator for logging execution time
def log_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logging.info(f"Execution time for {func.__name__}: {execution_time:.2f} seconds")
        return result
    return wrapper

class MrqRender:
    def __init__(self):
        # Get the project's directory
        project_dir = unreal.SystemLibrary.get_project_directory()

        # Build the saved directory path within the project directory
        saved_dir = os.path.join(project_dir, "Saved")

        # Define the full path for the 'render_logs' folder
        log_dir = os.path.join(saved_dir, "Logs", "render_logs")

        # Convert to system-specific path (Windows format)
        sys_log_dir = log_dir.replace("/", "\\")

        # If the 'render_logs' folder does not exist, create it
        if not os.path.exists(sys_log_dir):
            os.makedirs(sys_log_dir)

        # Get the current date in the desired format (e.g., "2024-12-13")
        current_date = datetime.datetime.today().strftime("%Y-%m-%d")

        # Build the log filename dynamically
        self.log_filename = os.path.join(sys_log_dir, f"render_script_{current_date}.log")

        # Set up the TimedRotatingFileHandler
        self.handler = handlers.TimedRotatingFileHandler(
            self.log_filename, when="D", interval=1, backupCount=150
        )

        # Set the logging level and add the handler
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)  # Log level set to DEBUG
        self.handler.setLevel(logging.DEBUG)  # Set level for the handler
        logger.addHandler(self.handler)

        # Also log to the console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)  # Log level for console
        logger.addHandler(console_handler)

        # Log the log filename and initialization message
        logging.info(f"Log file will be saved to: {self.log_filename}")
        logging.info("*"*100)
        logging.info("RenderScript initialized")

    def load_assets(self):
        # Get the content directory of the project
        content_dir = unreal.SystemLibrary.get_project_content_directory()
        sys_config_dir = os.path.join(content_dir, 'Cinematics/', 'Queue')

        # Replace the content directory with '/Game/' to get the appropriate UE2 path
        ue_config_dir = sys_config_dir.replace(content_dir, "/Game/")

        # List all assets in the directory (recursively)
        asset_paths = unreal.EditorAssetLibrary.list_assets(ue_config_dir, recursive=True, include_folder=True)

        # Filter out the paths to get valid queues
        filtered_paths = []

        # Iterate through all asset paths
        for path in asset_paths:
            # Check if the path does not end with '/' (i.e., it's not a folder)
            if not path.endswith('/'):
                # Split the asset path at '.' and take the first part (to remove extensions)
                filtered_path = path.split('.')[0]
                
                # Add the filtered path to the list
                filtered_paths.append(filtered_path)

        # Reverse the list to process assets in the reverse order
        queues = list(reversed(filtered_paths))

        # Load each queue asset
        for queue in queues:
            queue_asset = unreal.EditorAssetLibrary.load_asset(queue)

            if queue_asset:
                jobs = queue_asset.get_jobs()
                for job in jobs:
                    config = job.get_configuration()
                    if config:
                        resolution_setting = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
                        if resolution_setting:
                            logging.info ("*"*150)
                            logging.info ("*"*150)
                            logging.info(f"Current Resolution: {resolution_setting.output_resolution.x}x{resolution_setting.output_resolution.y}")
                            new_width = 500
                            new_height = 600
                            resolution_setting.output_resolution.x = new_width
                            resolution_setting.output_resolution.y = new_height
                            logging.info(f"Updated Resolution: {resolution_setting.output_resolution.x}x{resolution_setting.output_resolution.y}")
                            logging.info ("*"*150)
                            logging.info ("*"*150)

                try:
                    # 변경 사항 저장
                    if unreal.EditorAssetLibrary.save_loaded_asset(queue_asset):
                        logging.info(f"Changes saved successfully for asset: {queue}")
                        
                        # 저장 후 패키지 강제 저장
                        logging.info (queue)
                        package = unreal.load_package(queue)
                        logging.info (package)
                        unreal.EditorLoadingAndSavingUtils.save_packages(packages_to_save=[package], only_dirty=False)  # package는 리스트로 전달
                except Exception as e:
                    logging.info(f"Error saving package for asset {queue}: {e}")
            else:
                logging.info(f"Failed to load asset: {queue}")

        logging.info ("Filtered queues:", queues)
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
            f'-MoviePipelineConfig={queue}'  # Queue should already provide the correct path or instance
        ]

        logging.info(f"Generated command: {' '.join(command)}")
        return command

    # Main execution method for the render task
    @log_execution_time
    def execute_mrq_render(self):
        try:
            logging.info("Starting MRQ render")
            queues = self.load_assets()
            if not queues:
                logging.info("No valid asset paths found for rendering.")
                return

            processed_queues = set()  # 이미 처리된 큐 추적
            for queue in queues:
                if queue in processed_queues:
                    logging.info(f"Skipping already processed queue: {queue}")
                    continue

                logging.info(f"Processing asset: {queue}")
                cmd_command = self.generate_cmd_command(queue)

                # 실제 실행
                try:
                    result = subprocess.run(cmd_command, shell=True, check=True)
                    logging.info(f"Command executed successfully: {queue}")
                    processed_queues.add(queue)  # 처리 완료로 기록
                except subprocess.CalledProcessError as e:
                    logging.error(f"Error executing command for {queue}: {e}")
                    traceback.print_exc()
        except Exception as e:
            logging.error(f"Error during MRQ render execution: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    render_job = MrqRender()
    render_job.execute_mrq_render()
