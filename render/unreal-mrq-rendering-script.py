import os
import sys
import json
import subprocess
from datetime import datetime
import logging

class UnrealMRQManager:
    def __init__(self, unreal_editor_path, project_path):
        self.unreal_editor_path = unreal_editor_path
        self.project_path = project_path
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('unreal_mrq_render.log'),
                logging.StreamHandler()
            ]
        )
        
    def submit_render_job(self, mrq_config_path, overrides=None):
        """
        MRQ Configuration을 사용한 렌더링 작업 실행
        
        Args:
            mrq_config_path (str): MRQ 설정 파일 경로
            overrides (dict): 오버라이드할 설정들
                가능한 키:
                - output_path: 출력 경로
                - resolution: (width, height) 튜플
                - frame_rate: 프레임 레이트 (float)
                - samples_per_pixel: AA 샘플 수
                - output_format: 출력 포맷 (EXR, PNG 등)
                등...
        """
        try:
            # 렌더링 명령어 생성 및 실행
            render_cmd = self._create_mrq_render_command(mrq_config_path, overrides)
            self._execute_render(render_cmd)
            return True
            
        except Exception as e:
            logging.error(f"렌더링 작업 실패: {str(e)}")
            return False
    
    def _create_override_arguments(self, overrides):
        """오버라이드 설정을 커맨드라인 인수로 변환"""
        args = []
        
        if not overrides:
            return args
            
        # 출력 경로 오버라이드
        if 'output_path' in overrides:
            args.extend([
                "-override_config",
                f"MoviePipeline.OutputPath={overrides['output_path']}"
            ])
            
        # 해상도 오버라이드
        if 'resolution' in overrides:
            width, height = overrides['resolution']
            args.extend([
                "-override_config",
                f"MoviePipeline.OutputResolution=(X={width},Y={height})"
            ])
            
        # 프레임레이트 오버라이드
        if 'frame_rate' in overrides:
            args.extend([
                "-override_config",
                f"MoviePipeline.TargetFPS={overrides['frame_rate']}"
            ])
            
        # AA 샘플 수 오버라이드
        if 'samples_per_pixel' in overrides:
            args.extend([
                "-override_config",
                f"MoviePipeline.SamplesPerPixel={overrides['samples_per_pixel']}"
            ])
            
        # 출력 포맷 오버라이드
        if 'output_format' in overrides:
            args.extend([
                "-override_config",
                f"MoviePipeline.OutputFormat={overrides['output_format']}"
            ])
            
        return args
    
    def _create_mrq_render_command(self, mrq_config_path, overrides):
        """언리얼 MRQ 렌더링 명령어 생성"""
        cmd = [
            self.unreal_editor_path,
            self.project_path,
            "-game",
            "-noSplash",
            "-windowed",
            "-log",
            "-MoviePipelineLocalExecutorClass",
            f"-MovieRenderPipelineConfig={mrq_config_path}"
            "-LevelSequence=/Game/Scene_Saloon/Sequences/His_Sal_Seq_01"
            "-ExecutorPythonClass=/Engine/PythonTypes.MoviePipelineExampleRuntimeExecutor"
        ]
        
        # 오버라이드 설정 추가
        cmd.extend(self._create_override_arguments(overrides))
        
        logging.info(f"렌더링 명령어 생성: {' '.join(cmd)}")
        return cmd
    
    def _execute_render(self, cmd):
        """렌더링 명령어 실행"""
        try:
            logging.info("렌더링 시작")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    logging.info(output.strip())
                    
            retval = process.poll()
            
            if retval == 0:
                logging.info("렌더링 완료")
            else:
                logging.error(f"렌더링 실패 (반환 코드: {retval})")
                
        except Exception as e:
            logging.error(f"렌더링 실행 중 오류 발생: {str(e)}")
            raise

def main():
    # 설정 예시
    manager = UnrealMRQManager(
        unreal_editor_path=r"C:\Program Files\Epic Games\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe",
        project_path=r"C:\Users\admin\Desktop\Project\pipe_test\pipe_test.uproject"
    )
    
    # 오버라이드할 설정들
    overrides = {
        'output_path': r"C:\Users\admin\Desktop\Project\pipe_test\Saved\MovieRenders\render_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
        'resolution': (3840, 2160),
        'frame_rate': 24.0,
        'samples_per_pixel': 64,
        'output_format': "EXR"
    }
    
    # MRQ Configuration을 사용한 렌더링 실행 (설정 오버라이드 포함)
    manager.submit_render_job(
        mrq_config_path="/Game/Cinematics/Queue/MyRenderQueue_1",
        overrides=overrides
    )

if __name__ == "__main__":
    main()
