from shotgun_api3 import Shotgun
import os
import subprocess
import traceback

# ShotGrid server URL and certification info
SERVER_URL = "https://jhworld.shotgrid.autodesk.com"
SCRIPT_NAME = "hyo"
API_KEY = "qhxiu7rznptjzbonbv*bhxJvu"

def create_shotgun_session(server_url, script_name, api_key):
    # Create ShotGrid API session
    return Shotgun(server_url, script_name, api_key)

def get_software_info(sg, software_name):
    # Get ShotGrid software entity and field info
    software = sg.find_one(
        "Software",
        [["code", "is", software_name]],
        ["windows_path", "windows_args"]
    )
    if software is not None:
        return software.get("windows_path"), software.get("windows_args")
    else:
        print(f"Error: '{software_name}' not found in ShotGrid Software")
        return None, None

def get_task_info(sg, task_id):
    # Get task info
    task = sg.find_one(
        "Task",
        [["id", "is", task_id]],
        ["project", "entity.Shot.sg_ue_scene_path", "entity.Shot.sg_movie_pipeline_config"]
    )
    if task is not None:
        uproject_path = task.get("entity.Shot.sg_ue_scene_path")
        movie_pipeline_config = task.get("entity.Shot.sg_movie_pipeline_config")
        return uproject_path, movie_pipeline_config
    else:
        print("Error: 'task' is None. Unable to access task information.")
        return None, None

def get_uasset_files(movie_pipeline_config):
    # Get queue files for rendering
    movie_pipeline_directory = movie_pipeline_config.replace("/Game/", "C:/Users/admin/Desktop/Project/pipe_test/Content/") 
    config_files = []

    if os.path.exists(movie_pipeline_directory):
        for f in os.listdir(movie_pipeline_directory):
            if f.endswith(".uasset"):
                config_files.append(f)
                print ("movie_pipe:", movie_pipeline_directory)
    else:
        print(f"Error: Directory {movie_pipeline_directory} does not exist.")
    
    return config_files

def generate_cmd_command(unreal_editor_path, uproject_path, movie_pipeline_config, config_file, render_args):
    # Generate cmd command for unreal editor
    config_file_name = os.path.splitext(config_file)[0] # remove extension of file
    
    return (
        f'"{unreal_editor_path}" "{uproject_path}" -game '
        f'-MoviePipelineConfig="{movie_pipeline_config}/{config_file_name}" '
        f'{render_args}'
    )

def execute_cmd_command(cmd_command):
    # Execute CMD command
    try:
        subprocess.run(cmd_command, shell=True, check=True)  # check=True will raise an exception if the command fails
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while executing the command: {cmd_command}")
        print(f"Return code: {e.returncode}")
        print("Output:")
        print(e.output)
        traceback.print_exc()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        traceback.print_exc()


def main():
    sg = create_shotgun_session(SERVER_URL, SCRIPT_NAME, API_KEY)

    software_name = "Unreal Engine Editor"
    unreal_editor_path, render_args = get_software_info(sg, software_name)
    
    if unreal_editor_path is None:
        return

    # Task ID
    task_id = 5849  # 실제 태스크 ID로 변경

    uproject_path, movie_pipeline_config = get_task_info(sg, task_id)

    if uproject_path and movie_pipeline_config:
        config_files = get_uasset_files(movie_pipeline_config)

        if config_files:
            for config_file in config_files:
                cmd_command = generate_cmd_command(unreal_editor_path, uproject_path, movie_pipeline_config, config_file, render_args)
                print('*' * 50)
                print(f"Processing: {config_file}")
                print(f"Generated CMD: {cmd_command}")
            
                # execute_cmd_command(cmd_command)
        else:
            print(f"No .uasset files found in {movie_pipeline_config}")
    else:
        print("Not found uproject path or movie_pipeline_config in ShotGrid")

if __name__ == "__main__":
    main()
