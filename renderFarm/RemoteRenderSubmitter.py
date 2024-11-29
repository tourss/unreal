import unreal
 
@unreal.uclass()
class MyCustomRemoteRenderSubmitter(unreal.MoviePipelineExecutorBase):
 
    # A MoviePipelineExecutor implementation must override this.
    @unreal.ufunction(override=True)
    def execute(self, pipeline_queue):
      unreal.log("Execute!")