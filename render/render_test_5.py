import logging
from logging import handlers
from shotgun_api3 import Shotgun
import os
import subprocess
import traceback
import time

class RenderExecutor:
    def __init__(self, server_url, script_name, api_key, log_filename="render_script.log"):
        self.server_url = server_url
        self.script_name = script_name
        self.api_key = api_key
        self.log_filename = log_filename
        self.sg = self.create_shotgun_session()
        
        # Set up logging with TimedRotatingFileHandler
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
        handler = handlers.TimedRotatingFileHandler(log_filename, when="D", interval=15, backupCount=150)
        logging.getLogger().addHandler(handler)
    
    def log_execution_time(func):
        # Decorator to log the execution time of a function
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            result = func(self, *args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            logging.info(f"Execution time for {func.__name__}: {elapsed_time:.2f} seconds.")
            print(f"Execution time for {func.__name__}: {elapsed_time:.2f} seconds.")
            return result
        return wrapper
    
    def create_shotgun_session(self):
        # Create ShotGrid API session
        logging.info(f"Creating Shotgun session with script: {self.script_name}")
        return Shotgun(self.server_url, self.script_name, self.api_key)
    
    def get_software_info(self, software_name):
        # Get ShotGrid software entity and field info
        logging.info(f"Fetching software info for {software_name}")
        software = self.sg.find_one(
            "Software",
            [["code", "is", software_name]],
            ["windows_path", "windows_args"]
        )
        if software is not None:
            logging.info(f"Found software: {software_name}")
            return software.get("windows_path"), software.get("windows_args")
        else:
            logging.error(f"Error: '{software_name}' not found in ShotGrid Software")
            return None, None
    
    def get_task_info(self, task_id):
        # Get task info
        logging.info(f"Fetching task info for task ID: {task_id}")
        task = self.sg.find_one(
            "Task",
            [["id", "is", task_id]],
            ["project", "entity.Shot.sg_ue_scene_path", "entity.Shot.sg_movie_pipeline_config"]
        )
        if task is not None:
            uproject_path = task.get("entity.Shot.sg_ue_scene_path")
            movie_pipeline_config = task.get("entity.Shot.sg_movie_pipeline_config")
            logging.info(f"Found uproject path: {uproject_path} and movie pipeline config: {movie_pipeline_config}")
            return uproject_path, movie_pipeline_config
        else:
            logging.error("Error: 'task' is None. Unable to access task information.")
            return None, None
    
    def get_uasset_files(self, movie_pipeline_config):
        # Get all .uasset files in the directory and subdirectories
        movie_pipeline_directory = movie_pipeline_config.replace("/Game/", "C:/Users/admin/Desktop/Project/pipe_test/Content/")
        config_files = []

        if os.path.exists(movie_pipeline_directory):
            logging.info(f"Searching for .uasset files in {movie_pipeline_directory}")
            for root, dirs, files in os.walk(movie_pipeline_directory):
                for f in files:
                    if f.endswith(".uasset"):
                        config_files.append(os.path.join(root, f))
                        logging.info(f"Found .uasset: {os.path.join(root, f)}")
        for config_file in config_files:
            print("config file context:", config_file)
        else:
            logging.error(f"Error: Directory {movie_pipeline_directory} does not exist.")
        
        return config_files
    
    def generate_cmd_command(self, unreal_editor_path, uproject_path, config_file, render_args):
        # Get the correct relative path for MoviePipelineConfig
        config_path = config_file.replace("C:/Users/admin/Desktop/Project/pipe_test/Content/", "/Game/")
        
        # Remove the .uasset extension from the Unreal path
        config_name = os.path.splitext(config_path)[0]

        # Replace backslashes with forward slashes for compatibility
        config_name = config_name.replace("\\", "/")
        
        # Ensure we are referencing the correct path and the config file is correctly added
        command = (
            f'"{unreal_editor_path}" "{uproject_path}" -game '
            f'-MoviePipelineConfig="{config_name}" '
            f'-RenderOffscreen -NoSplash -log '
        )
        
        logging.info(f"Generated command: {command}")
        return command
    
    @log_execution_time
    def execute_cmd_command(self, cmd_command):
        # Execute CMD command
        try:
            logging.info(f"Executing command: {cmd_command}")
            subprocess.run(cmd_command, shell=True, check=True)  # check=True will raise an exception if the command fails
        except subprocess.CalledProcessError as e:
            logging.error(f"Error occurred while executing the command: {cmd_command}")
            logging.error(f"Return code: {e.returncode}")
            logging.error("Output:")
            logging.error(e.output)
            traceback.print_exc()
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            traceback.print_exc()

    def execute(self, task_id):
        logging.info("Starting script execution")
        
        # Get software info (Unreal Engine)
        software_name = "Unreal Engine Editor"
        unreal_editor_path, render_args = self.get_software_info(software_name)
        
        if unreal_editor_path is None:
            return

        # Get task info from ShotGrid
        uproject_path, movie_pipeline_config = self.get_task_info(task_id)

        if uproject_path and movie_pipeline_config:
            config_files = self.get_uasset_files(movie_pipeline_config)

            if config_files:
                for config_file in config_files:
                    cmd_command = self.generate_cmd_command(unreal_editor_path, uproject_path, config_file, render_args)
                    logging.info('*' * 50)
                    logging.info(f"Processing: {config_file}")
                    logging.info(f"Generated CMD: {cmd_command}")
                    logging.info('*' * 50)
                    print("CMD COMMAND:", cmd_command)
                    self.execute_cmd_command(cmd_command)
            else:
                logging.warning(f"No .uasset files found in {movie_pipeline_config}")
        else:
            logging.error("Not found uproject path or movie_pipeline_config in ShotGrid")

        logging.info("Script execution finished")

# Running the script
if __name__ == "__main__":
    render_executor = RenderExecutor(
        server_url="https://jhworld.shotgrid.autodesk.com", 
        script_name="hyo", 
        api_key="qhxiu7rznptjzbonbv*bhxJvu"
    )
    
    # Specify the task ID to process
    task_id = 5849  # Update with actual task ID
    render_executor.execute(task_id)
