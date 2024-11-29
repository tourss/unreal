import unreal
import MyCustomEditorRenderExecutor
 
"""
This is a bootstrapping script that is executed when the editor starts in a
mode where it should connect read the command line and automatically render a job specified on the command line without artist intervention. It simply
calls render_queue_with_executor with a custom executor which then spawns
normal PIE executors - MyCustomEditorRenderExecutor is effectively a 'wrapper' around a PIE executor.
 
USAGE: UnrealEditor-Cmd.exe C:/Path/To/Project.uproject -execcmds="py CustomRenderBootstrap.py" -MoviePipelineConfig="/Game/Path/To/YourQueueAsset.YourQueueAsset"
 
The editor should launch, then automatically load the map specified by the first job in YourQueueAsset, then render it in PIE, then load the map for the next job, etc. Finally it will quit the editor on finish.
"""
 
tick_handle = None
custom_executor = None
 
def initialize_render_job():
    print('Initialize render job')
    
    # Create an instance of our custom executor
    global custom_executor
    custom_executor = MyCustomEditorRenderExecutor.MoviePipelineMyCustomEditorRenderExecutor()
    
    # Listen for the executor to be finished so we can request editor shutdown
    custom_executor.on_executor_finished_delegate.add_callable_unique(on_custom_executor_finished)
    
    # Now tell our custom executor to render which will load the queue asset and then create PIE executor instances.    
    subsystem = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    subsystem.render_queue_with_executor_instance(custom_executor)
 
def on_custom_executor_finished(executor, success):
    # Unfortunately the success bool isn't very useful at this time (errors report success)
    # so we can't do much with it here, but if you really need it you can get the correct
    # information from the individual job work callbacks on the PIE Executor and then you can
    # bubble that information up with another delegate, etc.
    unreal.log("Custom Executor Finished. Quitting editor now! Success: " + str(success))
    unreal.SystemLibrary.quit_editor()
    
def wait_for_asset_registry(delta_seconds):
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    if asset_registry.is_loading_assets():
        unreal.log_warning("Still loading...")
        pass
    else:
        global tick_handle
        unreal.unregister_slate_pre_tick_callback(tick_handle)
        initialize_render_job()
 
 
# The asset registry may not be fully loaded by the time this is called, so we
# will wait until it has finished parsing all of the assets in the project
# before we move on, otherwise attempts to look assets up may fail
# unexpectedly. This registers a OnTick callback and it will get called once
# per frame. Once the registry reports that we're loaded then we'll start the
# render job and unregister from this callback so that we only try to start
# rendering once!
tick_handle = unreal.register_slate_pre_tick_callback(wait_for_asset_registry)