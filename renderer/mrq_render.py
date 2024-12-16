import logging
from logging import handlers
import os
import subprocess
import traceback
import time
import datetime
import sys
import unreal

# Function to parse resolution arguments from the command line
def parse_resolution_args():
    width = 1920  # Default resolution
    height = 1080  # Default resolution

    command_line = unreal.SystemLibrary.get_command_line()

    # Check for width and height arguments in the command line and update values
    for arg in command_line.split():
        if "width=" in arg:
            width = int(arg.split("=")[1])
        elif "height=" in arg:
            height = int(arg.split("=")[1])

    return width, height

# Decorator for logging execution time of functions
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
    def __init__(self, width, height):
        self.width = width
        self.height = height

        # Get the project's directory
        project_dir = unreal.SystemLibrary.get_project_directory()

        # Build the saved directory path within the project directory
        saved_dir = os.path.join(project_dir, "Saved")

        # Define the full path for the 'render_logs' folder
        log_dir = os.path.join(saved_dir, "Logs", "render_logs")

        # Convert to system-specific path (Windows format)
        sys_log_dir = log_dir.replace("/", "\\")

        # Create 'render_logs' folder if it doesn't exist
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
        logging.info("*" * 100)
        logging.info("RenderScript initialized")

    # Function to load assets from the content directory
    def load_assets(self):
        # Get the content directory of the project
        content_dir = unreal.SystemLibrary.get_project_content_directory()
        sys_config_dir = os.path.join(content_dir, 'Cinematics/', 'Queue')

        # Replace the content directory with '/Game/' to get the appropriate UE5 path
        ue_config_dir = sys_config_dir.replace(content_dir, "/Game/")

        # List all assets in the directory (recursively)
        asset_paths = unreal.EditorAssetLibrary.list_assets(ue_config_dir, recursive=True, include_folder=True)

        # Filter out the paths to get valid queues
        filtered_paths = self.filter_asset_paths(asset_paths)

        # the list to process assets
        queues = list(reversed(filtered_paths))

        # Load each queue asset and apply resolution settings
        self.apply_resolution_to_assets(queues)

        return queues

    # Function to filter asset paths, excluding folders
    def filter_asset_paths(self, asset_paths):
        filtered_paths = []
        for path in asset_paths:
            if not path.endswith('/'): 
                filtered_path = path.split('.')[0]  # Remove extensions
                filtered_paths.append(filtered_path)
        return filtered_paths

    # Function to apply resolution settings to assets
    def apply_resolution_to_assets(self, queues):
        for queue in queues:
            queue_asset = unreal.EditorAssetLibrary.load_asset(queue)

            if not queue_asset:
                logging.error(f"Failed to load asset: {queue}")
                continue

            jobs = queue_asset.get_jobs()
            for job in jobs:
                config = job.get_configuration()
                if config:
                    resolution_setting = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
                    if resolution_setting:
                        logging.info("*" * 150)
                        logging.info(f"Current Resolution: {resolution_setting.output_resolution.x}x{resolution_setting.output_resolution.y}")
                        
                        # Update resolution
                        resolution_setting.output_resolution.x = self.width
                        resolution_setting.output_resolution.y = self.height
                        
                        logging.info(f"Updated Resolution: {resolution_setting.output_resolution.x}x{resolution_setting.output_resolution.y}")
                        logging.info("*" * 150)

            # Save the asset and package
            if unreal.EditorAssetLibrary.save_loaded_asset(queue_asset):
                logging.info(f"Changes saved successfully for asset: {queue}")
                package = unreal.load_package(queue)
                if package:
                    unreal.EditorLoadingAndSavingUtils.save_packages(packages_to_save=[package], only_dirty=False)
                else:
                    logging.error(f"Failed to load package for asset: {queue}")
            else:
                logging.error(f"Failed to save asset: {queue}")

    # Function to generate the command for Unreal Engine render
    def generate_cmd_command(self, queue):
        command = [
            sys.executable,
            "%s" % os.path.join(
                unreal.SystemLibrary.get_project_directory(),
                "%s.uproject" % unreal.SystemLibrary.get_game_name(),
            ),  # Unreal project
            "-game",
            "-NoSplash",  # Skip the Unreal splash screen
            "-log",  # Enable logging to the console
            "-RenderOffscreen",  # Render the scene offscreen, without showing the window
            "-NoTextureStreaming",  # Disable texture streaming (for full memory load)
            f'-MoviePipelineConfig={queue}',  # Path to the Movie Render Queue config
            "-FixedSeed",  # Ensure reproducibility by fixing the random seed
            "-Multiprocess",  # Enable multi-process rendering
            "-Unattended",  # Run without requiring user interaction
            "-nohmd",  # Disable head-mounted display (for VR rendering)
            "-dpcvars=%s" % ",".join([
                "sg.ViewDistanceQuality=4",  # Highest view distance quality
                "sg.AntiAliasingQuality=4",  # Highest anti-aliasing quality
                "sg.ShadowQuality=4",  # Highest shadow quality
                "sg.PostProcessQuality=4",  # Highest post-processing quality
                "sg.TextureQuality=4",  # Highest texture quality
                "sg.EffectsQuality=4",  # Highest effects quality
                "sg.FoliageQuality=4",  # Highest foliage quality
                "sg.ShadingQuality=4",  # Highest shading quality
                "r.TextureStreaming=0",  # Disable texture streaming
                "r.ForceLOD=0",  # Disable forced Level of Detail (LOD)
                "r.SkeletalMeshLODBias=-10",  # Use high-quality skeletal meshes
                "r.ParticleLODBias=-10",  # Use high-quality particles
                "foliage.DitheredLOD=0",  # Disable dithered LOD for foliage
                "foliage.ForceLOD=0",  # Disable forced LOD for foliage
                "r.Shadow.DistanceScale=10",  # Increase shadow distance scale
                "r.ShadowQuality=5",  # Highest shadow quality
                "r.Shadow.RadiusThreshold=0.001000",  # Fine-grain shadow precision
                "r.ViewDistanceScale=50",  # Increase view distance scale
                "r.D3D12.GPUTimeout=0",  # Disable GPU timeout for long renders
                "a.URO.Enable=0",  # Disable Unreal Rendering Optimization (if necessary)
            ])
        ]

        logging.info(f"Generated command: {' '.join(command)}")
        return command

    # Main execution method for the render task
    @log_execution_time
    def execute_mrq_render(self):
        try:
            # Load and filter assets
            queues = self.load_assets()
            if not queues:
                logging.info("No valid asset paths found for rendering.")
                return

            # Generate and execute commands for each filtered asset
            for queue in queues:
                logging.info(f"Processing asset: {queue}")

                # Generate Unreal Engine command
                cmd_command = self.generate_cmd_command(queue)
                if cmd_command:
                    logging.info(f"Executing command for asset: {queue}")

                    # Execute command (currently logging, subprocess can be used if necessary)
                    logging.info(cmd_command)

                    # Actual command execution (uncomment to enable)
                    subprocess.run(cmd_command, shell=True)

            logging.info("All render jobs executed successfully.")
        except Exception as e:
            logging.error(f"Error executing MRQ render: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    width, height = parse_resolution_args()  # Parse resolution arguments
    render_job = MrqRender(width, height)  # Create MrqRender object
    render_job.execute_mrq_render()  # Execute the render
