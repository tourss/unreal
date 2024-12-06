import logging
from logging import handlers
from shotgun_api3 import Shotgun
import os
import subprocess
import sys
import copy
import time
import unreal

class MrqRender:
    def __init__(self, server_url, script_name, api_key):
        self.server_url = server_url
        self.script_name = script_name
        self.api_key = api_key

        self.log_filename = "render_script.log"
        logging.basicConfig(
            level=logging.DEBUG, 
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        
        self.handler = handlers.TimedRotatingFileHandler(
            self.log_filename, when="D", interval=15, backupCount=150
        )
        logging.getLogger().addHandler(self.handler)

        self.sg = None
        self.unreal_editor_path = None  
        self.render_args = None
        self.uproject_path = None
        self.movie_pipeline_config = None

    def log_execution_time(func):
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            result = func(self, *args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            logging.info(f"Execution time for {func.__name__}: {elapsed_time:.2f} seconds.")
            return result
        return wrapper

    def create_shotgun_session(self):
        logging.info(f"Creating Shotgun session with script: {self.script_name}")
        self.sg = Shotgun(self.server_url, self.script_name, self.api_key)

    def get_software_info(self, software_name):
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
        logging.info(f"Fetching task info for task ID: {task_id}")
        task = self.sg.find_one(
            "Task",
            [["id", "is", task_id]],
            ["project", "entity.Shot.sg_ue_scene_path", "entity.Shot.sg_movie_pipeline_config"]
        )
        if task is not None:
            self.uproject_path = task.get("entity.Shot.sg_ue_scene_path")
            self.movie_pipeline_config = task.get("entity.Shot.sg_movie_pipeline_config")
            logging.info(f"Found uproject path: {self.uproject_path} and movie pipeline config: {self.movie_pipeline_config}")
        else:
            logging.error("Error: 'task' is None. Unable to access task information.")

    def _unreal_render_sequence_with_sequencer(self, output_path, unreal_map_path, sequence_path):
        """
        Renders a given sequence in a given level to a movie file with the Level Sequencer.

        :param str output_path: Full path to the movie to render.
        :param str unreal_map_path: Path of the Unreal map in which to run the sequence.
        :param str sequence_path: Content Browser path of sequence to render.
        :returns: True if a movie file was generated, False otherwise
                  string representing the path of the generated movie file
        """
        output_folder, output_file = os.path.split(output_path)
        movie_name = os.path.splitext(output_file)[0]

        if os.path.isfile(output_path):
            try:
                os.remove(output_path)
            except OSError:
                logging.error(
                    "Couldn't delete {}. The Sequencer won't be able to output the movie to that file.".format(output_path)
                )
                return False, None

        cmdline_args = [
            sys.executable,  # Unreal executable path
            "%s" % os.path.join(
                unreal.SystemLibrary.get_project_directory(),
                "%s.uproject" % unreal.SystemLibrary.get_game_name(),
            ),
            unreal_map_path,  # Level to load for rendering the sequence
            "-LevelSequence=%s" % sequence_path,
            "-MovieFolder=%s" % output_folder,
            "-MovieName=%s" % movie_name,
            "-game",
            "-MovieSceneCaptureType=/Script/MovieSceneCapture.AutomatedLevelSequenceCapture",
            "-ResX=1280",
            "-ResY=720",
            "-ForceRes",
            "-Windowed",
            "-MovieCinematicMode=yes",
            "-MovieFormat=Video",
            "-MovieFrameRate=24",
            "-MovieQuality=75",
            "-NoTextureStreaming",
            "-NoLoadingScreen",
            "-NoScreenMessages",
        ]

        logging.info("Sequencer command-line arguments: {}".format(" ".join(cmdline_args)))

        run_env = copy.copy(os.environ)
        if "UE_SHOTGUN_BOOTSTRAP" in run_env:
            del run_env["UE_SHOTGUN_BOOTSTRAP"]
        if "UE_SHOTGRID_BOOTSTRAP" in run_env:
            del run_env["UE_SHOTGRID_BOOTSTRAP"]

        subprocess.call(cmdline_args, env=run_env)

        return os.path.isfile(output_path), output_path

if __name__ == "__main__":
    render_job = MrqRender(
        server_url="https://hg.shotgrid.autodesk.com", 
        script_name="hyo", 
        api_key="4yhreigsfqmwlsz%yfnfuqqYo"
    )
    render_job.create_shotgun_session()
    render_job.get_task_info(task_id=5827)

    output_path = r"C:\Users\admin\Desktop\Project\render_output\movie.mov"
    unreal_map_path = "/Game/Scene_Saloon/Maps/Historic_Saloon"
    sequence_path = "/Game/Scene_Saloon/Sequences/His_Sal_Seq_01"

    success, output = render_job._unreal_render_sequence_with_sequencer(output_path, unreal_map_path, sequence_path)

    if success:
        logging.info(f"Movie rendered successfully: {output}")
    else:
        logging.error("Failed to render the movie.")
