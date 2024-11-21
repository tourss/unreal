import unreal


@unreal.uclass()
class MyExecutor(unreal.MoviePipelinePythonHostExecutor):
 
    pipeline = unreal.uproperty(unreal.MoviePipeline)  # 파이프라인 객체를 저장
    queue = unreal.uproperty(unreal.MoviePipelineQueue)  # 렌더링 큐를 저장
    job_id = unreal.uproperty(unreal.Text)  # 작업 ID를 저장

    def _post_init(self):
        self.pipeline = None
        self.queue = None
        self.job_id = None
