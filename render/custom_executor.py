import logging
from logging import handlers
import os
import subprocess
import traceback
import time
import unreal

# 로깅 설정
log_filename = "render_script.log"
logger = logging.getLogger("RenderScript")
logger.setLevel(logging.DEBUG)

handler = handlers.TimedRotatingFileHandler(
    log_filename, when="D", interval=15, backupCount=150
)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class CustomMoviePipelineExecutor(unreal.MoviePipelinePythonHostExecutor):
    """
    Custom executor to integrate with Unreal Engine's Movie Render Pipeline.
    """

    @staticmethod
    def log_execution_time(func):
        """Decorator to log execution time for a function."""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            logger.info(f"Execution time for {func.__name__}: {elapsed_time:.2f} seconds.")
            return result
        return wrapper

    def __init__(self):
        super().__init__()
        logger.info("CustomMoviePipelineExecutor initialized.")

    @staticmethod
    def get_uasset_files(movie_pipeline_config_path):
        """Find all .uasset files under a specific directory."""
        content_path = movie_pipeline_config_path.replace("/Game/", unreal.Paths.project_content_dir())
        logger.info(f"Converted pipeline config path: {content_path}")

        if not os.path.exists(content_path):
            logger.error(f"Error: Directory {content_path} does not exist.")
            return []

        uasset_files = []
        logger.info(f"Searching for .uasset files in {content_path}")
        for root, dirs, files in os.walk(content_path):
            for f in files:
                if f.endswith(".uasset"):
                    uasset_files.append(os.path.join(root, f))
                    logger.info(f"Found .uasset: {os.path.join(root, f)}")

        return uasset_files

    def on_begin_frame(self):
        """
        Called once per frame during execution.
        """
        logger.info("Starting execution in CustomMoviePipelineExecutor.on_begin_frame")
        super().on_begin_frame()

    @log_execution_time
    def execute_rendering(self, config_path):
        """Execute the rendering process using Unreal Engine."""
        try:
            uasset_files = self.get_uasset_files(config_path)
            if not uasset_files:
                logger.warning(f"No .uasset files found in {config_path}")
                return

            for config_file in uasset_files:
                # Build a command using Unreal Engine's editor binary
                editor_path = unreal.Paths.engine_executable()
                uproject_path = unreal.Paths.project_file_path()

                unreal_path = config_file.replace(unreal.Paths.project_content_dir(), "/Game/").replace("\\", "/")
                unreal_config_name = os.path.splitext(unreal_path)[0]

                cmd_command = (
                    f'"{editor_path}" "{uproject_path}" '
                    f'-game '
                    f'-NoSplash -log '
                    f'-MoviePipelineLocalExecutorClass=/Script/MovieRenderPipelineCore.MoviePipelinePythonHostExecutor '
                    f'-ExecutorPythonClass=/Game/Python/custom_executor.CustomMoviePipelineExecutor '
                    f'-RenderOffscreen '
                    f' -resX=1280 -resY=720 '
                )

                logger.info(f"Generated Command: {cmd_command}")
                self.execute_cmd_command(cmd_command)

        except Exception as e:
            logger.error(f"An error occurred while rendering: {e}")
            traceback.print_exc()

    @staticmethod
    def execute_cmd_command(cmd_command):
        """Run a command line process."""
        try:
            logger.info(f"Executing command: {cmd_command}")
            subprocess.run(cmd_command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {cmd_command}")
            logger.error(f"Return code: {e.returncode}")
            logger.error(e.output)
            traceback.print_exc()
        except Exception as e:
            logger.error(f"Unexpected error while executing command: {e}")
            traceback.print_exc()

    def start_render(self):
        """
        Start the render process when executed in the Movie Render Queue.
        """
        logger.info("Starting custom render process via CustomMoviePipelineExecutor.start_render")
        movie_pipeline_config_path = "/Game/Cinematics/Queue"
        self.execute_rendering(movie_pipeline_config_path)

    def execute_delayed(self):
        """
        This function will execute tasks that are delayed or need to be executed later.
        """
        logger.info("Executing delayed tasks.")
        try:
            # Example: You can implement specific tasks here, like waiting for a condition or another process.
            # For now, we simply log the task execution.
            self.start_render()  # Example delayed task: start render process
        except Exception as e:
            logger.error(f"An error occurred during delayed execution: {e}")
            traceback.print_exc()
