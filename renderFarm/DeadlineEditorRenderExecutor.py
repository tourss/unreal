from datetime import datetime
from email import message

import unreal

import DeadlineRemoteCommand

pieExecutor = None


@unreal.uclass()
class MoviePipelineDeadlineEditorRenderExecutor(unreal.MoviePipelinePythonHostExecutor):
    localShotIndex = unreal.uproperty(int)
    globalShotIndex = unreal.uproperty(int)
    hasLoadedMapOnce = unreal.uproperty(bool)
    jobSubmitTime = unreal.uproperty(str)
    pieExecutor = unreal.uproperty(unreal.MoviePipelinePIEExecutor)
    soloQueue = unreal.uproperty(unreal.MoviePipelineQueue)

    def __init__(self, *args, **kwargs):
        super(MoviePipelineDeadlineEditorRenderExecutor, self).__init__(*args, **kwargs)
        self.pipeline_queue = None
        self.lastJobProgressUpdate = None

    # Constructor that gets called when created either via C++ or Python
    def _post_init(self):
        # Register to any socket messages
        self.socket_message_recieved_delegate.add_function_unique(self, "on_message")
        print(f"Deadline Class: {self.get_class()} Name: {self.get_full_name()}")

    @unreal.ufunction(override=True)
    def execute_delayed(self, pipeline_queue):
        # The usual code that loads the queue from the manifest file into the
        # inPipelineQueue doesn't run in the editor, so we have to do it by hand.
        cmd_tokens, cmd_switches, cmd_parameters = unreal.SystemLibrary.parse_command_line(
            unreal.SystemLibrary.get_command_line()
        )
        try:
            manifest_file_path = cmd_parameters['MoviePipelineConfig']
        except Exception:
            unreal.log_error("Missing '-MoviePipelineConfig' argument")
            self.on_executor_errored()
            return

        unreal.log(f"Loading manifest file from path: {manifest_file_path}")
        self.pipeline_queue = unreal.MoviePipelineLibrary.load_manifest_file_from_string(manifest_file_path)

        # This executioner stays alive the entire time there
        # are tasks to be rendered for the Deadline Job.
        unreal.log(f"Execute called with pipeline queue: {pipeline_queue} Connecting to socket...")
        socket_connected = self.connect_socket("127.0.0.1", 6783)
        if socket_connected:
            unreal.log("Successfully connected to socket host!")
        else:
            unreal.log_warning("Failed to connect socket to host!")

        self.deadline_log("Executor initialized and awaiting commands from Deadline Plugin...")

    @unreal.ufunction(override=True)
    def on_begin_frame(self):
        # It is important that we call the super so that async socket messages get processed.
        super(MoviePipelineDeadlineEditorRenderExecutor, self).on_begin_frame()

    @unreal.ufunction(ret=None, params=[str])
    def on_message(self, message):

        pending_message = DeadlineRemoteCommand.RemoteCommand(None, None)
        pending_message.from_json(message)

        if pending_message.commandType == DeadlineRemoteCommand.TYPE_START_TASK:
            # Get the shot index from the message. Our Queue only has one job.
            shot_index = pending_message.data['shotIndex']
            self.jobSubmitTime = pending_message.data['jobSubmitTime']
            self.load_map_for_shot(shot_index)

    @unreal.ufunction(ret=None, params=[int])
    def load_map_for_shot(self, global_shot_index):
        self.deadline_log(f"load_map_for_shot for (local) shotIndex: {global_shot_index}")

        # Determine which job in the queue this shot is for. This is future
        # proofing to allow us to run multiple jobs in one queue.
        job_index = 0
        accumulated_shot_index = 0
        local_shot_index = global_shot_index
        for curr_job_index in range(0, len(self.pipeline_queue.get_jobs())):
            potential_job = self.pipeline_queue.get_jobs()[curr_job_index]
            prev_accumulated_shot_index = accumulated_shot_index
            accumulated_shot_index += len(potential_job.shot_info)
            # Untested, test this if you have more than one job in the Queue
            # ToDo: localShotIndex should be globalShotIndex and turned into a
            #  local shot index before calling render_shot
            # ToDo: if jobIndex != prevJobIndex, reset self.hasLoadedMapOnce
            if prev_accumulated_shot_index <= global_shot_index < accumulated_shot_index:
                job_index = curr_job_index
                local_shot_index = global_shot_index - prev_accumulated_shot_index
                break

        if not self.hasLoadedMapOnce:
            # We need to load the map in the editor that they want to render
            # from. Technically this would be done by the PIE Executor, but
            # historically some systems (texture streaming, etc.) sometimes
            # fail if the map in PIE isn't the one that was loaded in the Editor.
            map_package_path = unreal.MoviePipelineLibrary.get_map_package_name(
                self.pipeline_queue.get_jobs()[job_index])
            self.deadline_log("Loading target map: %s" % map_package_path)
            self.set_status_message("Loading Map")
            self.set_status_progress(0)

            # In the editor this is a blocking load.
            map_load_start_time = unreal.MathLibrary.utc_now()
            unreal.EditorLoadingAndSavingUtils.load_map(map_package_path)
            curr_time = unreal.MathLibrary.utc_now()
            total_seconds = unreal.MathLibrary.get_total_seconds(
                unreal.MathLibrary.subtract_date_time_date_time(
                    curr_time,
                    map_load_start_time
                )
            )
            self.deadline_log(f"Map load took: {total_seconds} seconds.")

            self.hasLoadedMapOnce = True

        # Now that the target map is loaded, render.
        self.render_shot(job_index, local_shot_index, global_shot_index)

    @unreal.ufunction(ret=None, params=[int, int, int])
    def render_shot(self, job_index, local_shot_index, global_shot_index):
        # We need to modify the job mask for this job to only do the current shot.
        self.set_status_progress(0)
        self.localShotIndex = local_shot_index

        # Duplicate the queue we loaded into a local one with only job
        self.soloQueue = unreal.MoviePipelineQueue()
        job = self.soloQueue.duplicate_job(self.pipeline_queue.get_jobs()[job_index])

        # Iterate through the shot mask and turn off all shots except the target one.
        print(f"Found: {len(job.shot_info)} ShotInfos.")
        for shot_info_index in range(0, len(job.shot_info)):
            shot_info = job.shot_info[shot_info_index]
            shot_info.enabled = (shot_info_index == local_shot_index)
            print(f"Shot info index: {shot_info_index} Shot Index: {local_shot_index} Enabled: {shot_info.enabled}")

        default_settings = unreal.get_default_object(unreal.MovieRenderPipelineProjectSettings)
        is_soft_class_object = True

        try:
            # Get the local executor class
            class_ref = (
                unreal.SystemLibrary.conv_soft_class_path_to_soft_class_ref(
                    default_settings.default_local_executor
                )
            )
        except (TypeError, Exception):
            class_ref = default_settings.default_local_executor
            is_soft_class_object = False

        if is_soft_class_object:
            # Get the executor class as this is required to get an instance of
            # the executor
            executor_class = unreal.SystemLibrary.load_class_asset_blocking(
                class_ref
            )
        else:
            executor_class = class_ref

        local_default_executor = unreal.new_object(executor_class)
        
        # self.pieExecutor = unreal.MoviePipelinePIEExecutor()
        self.pieExecutor = local_default_executor
        self.pieExecutor.on_executor_finished_delegate.add_function_unique(self, "on_queue_finished")

        self.set_status_message("Rendering")
        self.lastJobProgressUpdate = 0

        # Convert our Deadline-time format ("12/08/2020 13:10:55") into a Python DateTime
        datetime_object = datetime.strptime(self.jobSubmitTime, "%m/%d/%Y %H:%M:%S")
        # Then convert it to a unreal DateTime object via an iso compliant string
        unreal_datetime = unreal.MathLibrary.date_time_from_iso_string(datetime_object.isoformat())
        # Finally, override the job initialization time in the movie pipeline so all
        # shots share the same global initialization time.
        self.pieExecutor.set_initialization_time(unreal_datetime)
        self.pieExecutor.execute(self.soloQueue)

    @unreal.ufunction(override=True)
    def is_rendering(self):
        # This will block anyone from trying to use the UI to launch other
        # jobs and cause confusion
        return self.pieExecutor is not None

    def deadline_log(self, message):
        unreal.log(message)
        log_message = DeadlineRemoteCommand.RemoteCommand(
            DeadlineRemoteCommand.TYPE_LOG_MESSAGE,
            {
                'severity': 'log',
                'message': message
            }
        )
        serialized_message = log_message.to_json()
        self.send_socket_message(serialized_message)

    @unreal.ufunction(override=True)
    def set_status_message(self, status):
        super(MoviePipelineDeadlineEditorRenderExecutor, self).set_status_message(status)

        log_message = DeadlineRemoteCommand.RemoteCommand(
            DeadlineRemoteCommand.TYPE_SET_STATUS,
            {'status': status}
        )
        serialized_message = log_message.to_json()
        self.send_socket_message(serialized_message)

    @unreal.ufunction(override=True)
    def set_status_progress(self, progress):
        super(MoviePipelineDeadlineEditorRenderExecutor, self).set_status_progress(progress)

        log_message = DeadlineRemoteCommand.RemoteCommand(
            DeadlineRemoteCommand.TYPE_SET_PROGRESS,
            {'progress': progress * 100}
        )
        serialized_message = log_message.to_json()
        self.send_socket_message(serialized_message)

    @unreal.ufunction(ret=None, params=[unreal.MoviePipelineExecutorBase, bool])
    def on_queue_finished(self, executor, fatal_error):
        self.deadline_log(f"Shot finished! Shot: {self.localShotIndex} (Local) {self.globalShotIndex} (Global)", )
        self.set_status_message("Idle")
        self.set_status_progress(0)

        self.soloQueue = None

        # When we finish a job, we will notify the external plugin that we
        # have finished. Then we return to an idling state until we get
        # another message indicating we should start on a new job.
        finished_message = DeadlineRemoteCommand.RemoteCommand(
            DeadlineRemoteCommand.TYPE_END_TASK,
            {
                'shotIndex': self.globalShotIndex,
                'success': fatal_error
            }
        )
        serialized_message = finished_message.to_json()

        self.send_socket_message(serialized_message)
