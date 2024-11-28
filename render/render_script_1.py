import argparse
import logging
from logging import handlers
from shotgun_api3 import Shotgun
import os
import subprocess
import traceback
import time

# ShotGrid server URL and certification info
SERVER_URL = "https://jhworld.shotgrid.autodesk.com"
SCRIPT_NAME = "hyo"
API_KEY = "qhxiu7rznptjzbonbv*bhxJvu"

def setup_logging():
    log_filename = "render_script.log"
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    handler = handlers.TimedRotatingFileHandler(
        log_filename, when="D", interval=15, backupCount=150
    )
    logging.getLogger().addHandler(handler)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Unreal Engine Render Script')
    parser.add_argument('--task-id', type=int, required=True,
                      help='ShotGrid Task ID')
    parser.add_argument('--output-path', type=str, required=True,
                      help='Render output path')
    parser.add_argument('--resolution', type=str, required=True,
                      help='Resolution in format WIDTHxHEIGHT (e.g. 1920x1080)')
    parser.add_argument('--formats', nargs='+', required=True,
                      help='Output formats (e.g. EXR PNG JPG)')
    parser.add_argument('--frame-rate', type=float, default=24.0,
                      help='Frame rate (default: 24.0)')
    parser.add_argument('--samples', type=int, default=64,
                      help='Samples per pixel (default: 64)')
    return parser.parse_args()

def create_shotgun_session():
    logging.info(f"Creating Shotgun session with script: {SCRIPT_NAME}")
    return Shotgun(SERVER_URL, SCRIPT_NAME, API_KEY)

def get_software_info(sg, software_name):
    logging.info(f"Fetching software info for {software_name}")
    software = sg.find_one(
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

def get_task_info(sg, task_id):
    logging.info(f"Fetching task info for task ID: {task_id}")
    task = sg.find_one(
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

def get_uasset_files(movie_pipeline_config):
    movie_pipeline_directory = movie_pipeline_config.replace("/Game/", "C:/Users/admin/Desktop/Project/pipe_test/Content/")
    config_files = []

    if os.path.exists(movie_pipeline_directory):
        logging.info(f"Searching for .uasset files in {movie_pipeline_directory}")
        for root, dirs, files in os.walk(movie_pipeline_directory):
            for f in files:
                if f.endswith(".uasset"):
                    config_files.append(os.path.join(root, f))
                    logging.info(f"Found .uasset: {os.path.join(root, f)}")
    else:
        logging.error(f"Error: Directory {movie_pipeline_directory} does not exist")
    
    return config_files

def generate_cmd_commands(unreal_editor_path, uproject_path, config_file, args):
    config_path = config_file.replace("C:/Users/admin/Desktop/Project/pipe_test/Content/", "/Game/")
    config_name = os.path.splitext(config_path)[0]
    config_name = config_name.replace("\\", "/")
    
    width, height = map(int, args.resolution.split('x'))
    
    commands = []
    
    # Generate command for each format
    for output_format in args.formats:
        # Create format-specific output path
        format_output_path = os.path.join(args.output_path, output_format.lower())
        os.makedirs(format_output_path, exist_ok=True)
        
        command = [
            f'"{unreal_editor_path}"',
            f'"{uproject_path}"',
            '-game',
            '-NoSplash',
            '-log',
            '-windowed',
            '-ForceRes',
            '-NoTextureStreaming',
            f'-MoviePipelineConfig="{config_name}"',
            f'-override_config="MoviePipeline.OutputPath={format_output_path}"',
            f'-override_config="MoviePipeline.OutputResolution=(X={width},Y={height})"',
            f'-override_config="MoviePipeline.TargetFPS={args.frame_rate}"',
            f'-override_config="MoviePipeline.SamplesPerPixel={args.samples}"',
            f'-override_config="MoviePipeline.OutputFormat={output_format}"',
            '-ExecuteAutomation',
            '-RenderOffscreen'
        ]
        
        commands.append(" ".join(command))
    
    return commands

def execute_cmd_command(cmd_command):
    try:
        logging.info(f"Executing command: {cmd_command}")
        process = subprocess.Popen(
            cmd_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()  # 명령어 실행 결과를 바로 받음
        logging.info(f"STDOUT: {stdout}")
        logging.error(f"STDERR: {stderr}")
    except Exception as e:
        logging.error(f"Command execution failed: {e}")
        
        # Real-time logging of output
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logging.info(output.strip())
        
        return_code = process.poll()
        
        if return_code != 0:
            _, stderr = process.communicate()
            logging.error(f"Command failed with return code {return_code}")
            logging.error(f"Error output: {stderr}")
            return False
            
        return True
        
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        traceback.print_exc()
        return False

def execute():
    # Setup logging
    setup_logging()
    logging.info("Starting script execution")
    
    # Parse command line arguments
    args = parse_arguments()
    
    try:
        # Create ShotGrid session
        sg = create_shotgun_session()
        
        # Get software info
        software_name = "Unreal Engine Editor"
        unreal_editor_path, _ = get_software_info(sg, software_name)
        
        if unreal_editor_path is None:
            return
        
        # Get task info
        uproject_path, movie_pipeline_config = get_task_info(sg, args.task_id)
        
        if uproject_path and movie_pipeline_config:
            config_files = get_uasset_files(movie_pipeline_config)
            
            if config_files:
                for config_file in config_files:
                    commands = generate_cmd_commands(
                        unreal_editor_path,
                        uproject_path,
                        config_file,
                        args
                    )
                    
                    for cmd in commands:
                        logging.info('*' * 50)
                        logging.info(f"Processing: {config_file}")
                        logging.info(f"Generated CMD: {cmd}")
                        logging.info('*' * 50)
                        
                        if not execute_cmd_command(cmd):
                            logging.error(f"Failed to execute command for format")
            else:
                logging.warning(f"No .uasset files found in {movie_pipeline_config}")
        else:
            logging.error("Not found uproject path or movie_pipeline_config in ShotGrid")
    
    except Exception as e:
        logging.error(f"Script execution failed: {str(e)}")
        traceback.print_exc()
    
    logging.info("Script execution finished")

if __name__ == "__main__":
    execute()
