import os
import sys
import unreal

class MyCustomExecutor(unreal.MoviePipelinePythonHostExecutor):
    def execute_job(self, in_job):
        print(f"Customizing render parameters for job: {in_job}")

        # Output path
        output_path = self._get_command_line_argument("output")
        if not output_path:
            print("No output path provided. Using default path.")
            output_path = "/Game/RenderedMovies"

        # Convert to local file system path
        local_output_path = unreal.Paths.convert_relative_path_to_full(output_path)

        # Ensure output directory exists
        if not os.path.exists(local_output_path):
            print(f"Output path does not exist. Creating folder: {local_output_path}")
            os.makedirs(local_output_path, exist_ok=True)

        # Output format
        output_format = self._get_command_line_argument("format")
        if not output_format or output_format.lower() not in ["mov", "mp4"]:
            print("Invalid or no output format provided. Defaulting to 'mov'.")
            output_format = "mov"

        # MOV Codec Settings
        mov_codec_argument = self._get_command_line_argument("mov_codec")
        mov_codec = unreal.ProResCodecType.APPLE_PRORES_422  # Default MOV codec
        if mov_codec_argument:
            codec_mapping = {
                "proxy": unreal.ProResCodecType.APPLE_PRORES_PROXY,
                "lt": unreal.ProResCodecType.APPLE_PRORES_LT,
                "422": unreal.ProResCodecType.APPLE_PRORES_422,
                "hq": unreal.ProResCodecType.APPLE_PRORES_422_HQ,
                "4444": unreal.ProResCodecType.APPLE_PRORES_4444,
                "xq": unreal.ProResCodecType.APPLE_PRORES_4444_XQ,
            }
            mov_codec = codec_mapping.get(mov_codec_argument.lower(), mov_codec)
            print(f"Using MOV codec: {mov_codec_argument.upper()}")

        # MP4 Codec Settings
        mp4_codec_argument = self._get_command_line_argument("mp4_codec")
        mp4_codec = unreal.SimpleVideoCodec.H264  # Default MP4 codec (H264)
        if mp4_codec_argument:
            codec_mapping = {
                "h264": unreal.SimpleVideoCodec.H264,
                "h265": unreal.SimpleVideoCodec.H265,
            }
            mp4_codec = codec_mapping.get(mp4_codec_argument.lower(), mp4_codec)
            print(f"Using MP4 codec: {mp4_codec_argument.upper()}")

        # Render Settings
        job_config = in_job.get_configuration()
        if not job_config:
            print("Failed to retrieve job configuration!")
            return

        # Output Settings setup
        job_settings = job_config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
        if job_settings:
            job_settings.output_directory = unreal.DirectoryPath(output_path)
            job_settings.file_name_format = "{sequence_name}_{frame_number}"

            # Resolution Settings
            resolution_x = self._get_command_line_argument("resX", default=1920)
            resolution_y = self._get_command_line_argument("resY", default=1080)
            job_settings.output_resolution = unreal.IntPoint(int(resolution_x), int(resolution_y))

            # Set file extension based on format
            if output_format.lower() == "mov":
                job_settings.file_extension = ".mov"
                prores_settings = job_config.find_or_add_setting_by_class(unreal.MoviePipelineAppleProResOutputSetting)
                if prores_settings:
                    prores_settings.codec = mov_codec
            elif output_format.lower() == "mp4":
                job_settings.file_extension = ".mp4"
                video_settings = job_config.find_or_add_setting_by_class(unreal.MoviePipelineVideoOutputSetting)
                if video_settings:
                    video_settings.video_codec = mp4_codec
        
        # Frame Rate settings (within Output Settings)
        frame_rate_argument = self._get_command_line_argument("frame_rate", default=24)  # Default to 24 FPS
        frame_rate = unreal.FrameRate(int(frame_rate_argument), 1)  # Frame rate as fraction (e.g., 24/1)
        
        if job_settings:
            job_settings.output_frame_rate = frame_rate
            print(f"Using frame rate: {frame_rate_argument} FPS")

        # Anti-Aliasing settings
        aa_settings = job_config.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
        if aa_settings:
            aa_settings.spatial_sample_count = 8  # 8x SSAA
            aa_settings.temporal_sample_count = 4  # 4x TSAA

        print("Render parameters customized!")
        super().execute_job(in_job)

    def _get_command_line_argument(self, arg_name, default=None):
        """Command line argument parser with default support"""
        for arg in sys.argv:
            if arg.startswith(f"-{arg_name}="):
                return arg.split("=", 1)[1]
        return default

    def on_complete(self):
        print("Rendering completed!")
        super().on_complete()
