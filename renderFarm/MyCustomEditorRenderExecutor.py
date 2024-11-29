import unreal

pieExecutor = None

@unreal.uclass()
class MoviePipelineMyCustomEditorRenderExecutor (unreal.MoviePipelinePythonHostExecutor):
    pieExecutor = unreal.uproperty(unreal.MoviePipelinePIEExecutor)
    loadedQueue = unreal.uproperty(unreal.MoviePipelineQueue)
    currentQueue = unreal.uproperty(unreal.MoviePipelineQueue)
    jobIndex = unreal.uproperty(int)
    
    # Constructor that gets called when created either via C++ or Python
    def _post_init(self):
        self.loadedQueue = None
        self.currentQueue = None
        self.pieExecutor = None
        self.jobIndex = -1
        
    @unreal.ufunction(override=True)
    def execute_delayed(self, dummy_queue_ignore):
        # The usual code that loads the queue from the manifest file into the
        # inPipelineQueue doesn't run in the editor, so we have to do it by hand.
        cmd_tokens, cmd_switches, cmd_parameters = unreal.SystemLibrary.parse_command_line(
            unreal.SystemLibrary.get_command_line()
        )
        try:
            queue_asset_path = cmd_parameters['MoviePipelineConfig']
        except Exception:
            unreal.log_error("Missing '-MoviePipelineConfig' argument")
            self.on_executor_errored_impl_impl()
            return

        unreal.log(f"Loading Queue file from path: {queue_asset_path}")
        self.loadedQueue = unreal.EditorAssetLibrary.load_asset(queue_asset_path);
        
        if self.loadedQueue is None:
            unreal.log_error("Failed to load queue from path, is asset missing?")
            self.on_executor_errored_impl()
            return
            
        if len(self.loadedQueue.get_jobs()) == 0:
            unreal.log_error("No jobs in queue to process.")
            self.on_executor_errored_impl()
            return
            
        # Here's a good time to edit the self.loadedQueue if you wanted to, as its
        # now a copy (ie: changes won't affect the asset on disk) such as resolving
        # output directories or checking things out in Shotgrid, etc.
        
        # Start the rendering process
        self.start_job_by_index(0)

    @unreal.ufunction(ret=None, params=[int])
    def start_job_by_index(self, inIndex):
        if(inIndex >= len(self.loadedQueue.get_jobs())):
            unreal.log_error("Out of Bounds Job Index!")
            self.on_executor_errored_impl()
        
        self.jobIndex = inIndex;
        
        # Load the map in the editor
        map_package_path = unreal.MoviePipelineLibrary.get_map_package_name(
                self.loadedQueue.get_jobs()[self.jobIndex])
                
        map_load_start_time = unreal.MathLibrary.utc_now()
        unreal.EditorLoadingAndSavingUtils.load_map(map_package_path)
        curr_time = unreal.MathLibrary.utc_now()
        total_seconds = unreal.MathLibrary.get_total_seconds(
            unreal.MathLibrary.subtract_date_time_date_time(
                curr_time,
                map_load_start_time
            )
        )
        unreal.log(f"Map load took: {total_seconds} seconds.")
        
        # This is a little bit of a change in behavior compared to the in-editor behavior,
        # we first duplicate the job into its own Queue and then use the PIE Executor to
        # render that new queue (which only has one job). This allows us to do two things:
        # 1) Fully load the map in the editor before rendering a job (in case different jobs have different maps)
        # 2) Iterate through the queue ourself which gives us better control over updating extenral systems, etc.
        self.currentQueue = unreal.MoviePipelineQueue()
        job = self.currentQueue.duplicate_job(self.loadedQueue.get_jobs()[self.jobIndex])
        
        # Now create the executor and listen to it finish one job
        self.pieExecutor = unreal.MoviePipelinePIEExecutor()
        self.pieExecutor.on_executor_finished_delegate.add_function_unique(self, "on_individual_job_finished")
        self.pieExecutor.execute(self.currentQueue)
        
    @unreal.ufunction(ret=None, params=[unreal.MoviePipelineExecutorBase, bool])
    def on_individual_job_finished(self, executor, fatal_error):
        unreal.log("Job finished! Job Index: " + str(self.jobIndex))
        self.currentQueue = None

        # Render the next job in the queue (if any)
        if (self.jobIndex < len(self.loadedQueue.get_jobs()) - 1):
            self.start_job_by_index(self.jobIndex + 1)
        else:
            # Notify whoever created us that we're done
            self.on_executor_finished_impl()

        
    @unreal.ufunction(override=True)
    def is_rendering(self):
        # This will block anyone from trying to use the UI to launch other
        # jobs and cause confusion
        return self.pieExecutor is not None