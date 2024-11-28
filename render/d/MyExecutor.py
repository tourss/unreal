import unreal

# 커스텀 Executor 클래스 정의
@unreal.uclass()
class MyExecutor(unreal.MoviePipelinePythonHostExecutor):
    # 파이프라인과 큐를 저장할 변수 선언
    pipeline = unreal.uproperty(unreal.MoviePipeline)
    queue = unreal.uproperty(unreal.MoviePipelineQueue)
    job_id = unreal.uproperty(unreal.Text)
    map_path = unreal.uproperty(unreal.Text)
    seq_path = unreal.uproperty(unreal.Text)
    preset_path = unreal.uproperty(unreal.Text)
    output_path = unreal.uproperty(unreal.Text)

    def __init__(self):
        # 초기화 함수에서 빈 문자열로 설정
        self.pipeline = None
        self.queue = None
        self.job_id = ""
        self.map_path = ""
        self.seq_path = ""
        self.preset_path = ""
        self.output_path = ""
        super().__init__()

    def _post_init(self):
        # 초기화 함수에서 빈 문자열로 설정
        self.pipeline = None
        self.queue = None
        self.job_id = ""
        self.map_path = ""
        self.seq_path = ""
        self.preset_path = ""
        self.output_path = ""

    @unreal.ufunction(override=True)
    def execute_delayed(self, queue):
        # 명령줄에서 파라미터 읽기
        cmd_parameters = unreal.SystemLibrary.parse_command_line(unreal.SystemLibrary.get_command_line())
        
        # 필수 파라미터 읽기
        self.map_path = cmd_parameters.get('Level')
        self.job_id = cmd_parameters.get('JobId')
        self.seq_path = cmd_parameters.get('LevelSequence')
        self.preset_path = cmd_parameters.get('MoviePipelineConfig')
        self.output_path = cmd_parameters.get('OutputDirectory')

        # MoviePipelineConfig 파일 로드
        preset = unreal.SystemLibrary.conv_soft_obj_path_to_soft_obj_ref(unreal.SoftObjectPath(self.preset_path))
        movie_pipeline_config = unreal.MoviePipelineMasterConfig(preset)

        # 해상도 변경 (기존 해상도 읽고, 새로 설정)
        output_setting = movie_pipeline_config.find_setting_by_class(unreal.MoviePipelineOutputSetting)
        if output_setting:
            current_resolution = output_setting.output_resolution
            unreal.log(f"Current resolution: {current_resolution}")
            new_resolution = unreal.IntPoint(1920, 1080)  # 원하는 해상도로 설정
            output_setting.set_editor_property("output_resolution", new_resolution)
            unreal.log(f"Overridden resolution: {new_resolution}")
        
        # 파이프라인 초기화 및 큐에 작업 추가
        self.pipeline = unreal.new_object(
            self.target_pipeline_class,
            outer=self.get_last_loaded_world(),
            base_type=unreal.MoviePipeline
        )
        self.queue = unreal.new_object(unreal.MoviePipelineQueue, outer=self)
        job = self.queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
        job.map = unreal.SoftObjectPath(self.map_path)
        job.sequence = unreal.SoftObjectPath(self.seq_path)

        # 설정된 프리셋 적용
        preset_path = unreal.SoftObjectPath(self.preset_path)
        u_preset = unreal.SystemLibrary.conv_soft_obj_path_to_soft_obj_ref(preset_path)
        job.set_configuration(u_preset)
        
        # 파이프라인 초기화
        self.pipeline.initialize(self.queue)

        # 렌더링 시작
        self.pipeline.execute()

    # 작업 완료 후 호출되는 콜백
    @unreal.ufunction(ret=None, params=[unreal.MoviePipeline, bool])
    def on_job_finished(self, pipeline, error):
        if error:
            unreal.log_error("Rendering job failed!")
        else:
            unreal.log("Rendering job finished successfully!")
        self.on_executor_finished_impl()

    # 파이프라인이 완료된 후 호출되는 콜백
    @unreal.ufunction(ret=None, params=[unreal.MoviePipelineOutputData])
    def on_pipeline_finished(self, results):
        if results.success:
            for shot_data in results.shot_data:
                render_pass_data = shot_data.render_pass_data
                for k, v in render_pass_data.items():
                    if k.name == 'FinalImage':
                        outputs = v.file_paths
                        unreal.log(f"Final output images: {outputs}")
        else:
            unreal.log_error("Pipeline failed!")
