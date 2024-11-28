import unreal

@unreal.uclass()
class MyPreset(unreal.MoviePipelineMasterConfig):
    
    def __init__(self, preset):
        super(MyPreset, self).__init__(preset)
        self.copy_from(preset)

    @unreal.ufunction(ret=None, params=[])
    def set_flush_disk(self):
        # 설정을 disk flush로 변경
        u_setting = self.find_setting_by_class(unreal.MoviePipelineOutputSetting)
        u_setting.flush_disk_writes_per_shot = True
    
    @classmethod
    def get_base_preset(cls):
        u_preset = unreal.MoviePipelineMasterConfig()
        u_setting = u_preset.find_setting_by_class(unreal.MoviePipelineOutputSetting)
        u_setting.output_resolution = unreal.IntPoint(1920, 1080)  # 기본 해상도 설정

        # 다른 설정 추가
        render_pass = u_preset.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
        render_pass.disable_multisample_effects = True

        u_preset.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
        u_preset.initialize_transient_settings()
        return cls(u_preset)

    @property
    def output_path(self):
        u_setting = self.find_setting_by_class(unreal.MoviePipelineOutputSetting)
        return u_setting.get_editor_property('output_directory')

    @unreal.ufunction(ret=None, params=[str])
    def set_output_path(self, path):
        u_setting = self.find_setting_by_class(unreal.MoviePipelineOutputSetting)
        u_setting.set_editor_property('output_directory', unreal.DirectoryPath(path))
