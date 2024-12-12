import unreal

# Movie Pipeline Queue 어셋 로드
asset_path = "/Game/Cinematics/Queue/His_Sal_Seq_01_1"
queue_asset = unreal.EditorAssetLibrary.load_asset(asset_path)

if queue_asset:
    # Queue에 있는 Job 확인
    jobs = queue_asset.get_jobs()
    for job in jobs:
        # Job의 렌더링 설정 가져오기
        config = job.get_configuration()
        if config:
            # 해상도 설정 가져오기
            resolution_setting = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
            if resolution_setting:
                # 현재 해상도 확인
                print(f"Current Resolution: {resolution_setting.output_resolution.x}x{resolution_setting.output_resolution.y}")

                # 해상도 변경
                new_width = 3840
                new_height = 2160
                resolution_setting.output_resolution.x = new_width
                resolution_setting.output_resolution.y = new_height

                print(f"Updated Resolution: {resolution_setting.output_resolution.x}x{resolution_setting.output_resolution.y}")
            else:
                print("No resolution setting found.")

    # 변경 사항 저장
    unreal.EditorAssetLibrary.save_asset(asset_path)
    print("Changes saved successfully.")
else:
    print("Failed to load asset.")
