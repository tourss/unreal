import os
import sys
import json
import subprocess
from datetime import datetime
import logging
from typing import List, Dict, Optional

class UnrealMRQManager:
    def __init__(self, unreal_editor_path: str, project_path: str):
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
    
    def batch_render(self, render_jobs: List[Dict]) -> List[Dict]:
        """
        여러 MRQ 설정을 순차적으로 처리
        
        Args:
            render_jobs: 렌더링 작업 목록. 각 작업은 다음 형식의 딕셔너리:
                {
                    'mrq_config': 'config 경로',
                    'overrides': {설정 오버라이드},
                    'job_name': '작업 이름'
                }
                
        Returns:
            처리된 작업 정보 목록
        """
        processed_jobs = []
        
        for job in render_jobs:
            job_info = {
                'job_name': job.get('job_name', f"render_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                'mrq_config': job['mrq_config'],
                'overrides': job.get('overrides', {}),
                'command': None,
                'status': 'pending'
            }
            
            try:
                # 렌더링 명령어 생성
                cmd = self._create_render_command(job['mrq_config'], job['overrides'])
                job_info['command'] = cmd
                
                # Deadline 제출용 정보 생성
                job_info['deadline_info'] = self._create_deadline_info(job_info)
                
                processed_jobs.append(job_info)
                
            except Exception as e:
                logging.error(f"작업 처리 실패 - {job.get('job_name')}: {str(e)}")
                job_info['status'] = 'failed'
                job_info['error'] = str(e)
                processed_jobs.append(job_info)
                
        return processed_jobs
    
    def _create_render_command(self, mrq_config_path: str, overrides: Optional[Dict] = None) -> List[str]:
        """렌더링 명령어 생성"""
        cmd = [
            self.unreal_editor_path,
            self.project_path,
            "-game",
            "-nosplash",
            f"-MovieRenderPipelineConfig={mrq_config_path}"
        ]
        
        if overrides:
            cmd.extend(self._create_override_arguments(overrides))
            
        return cmd
    
    def _create_override_arguments(self, overrides: Dict) -> List[str]:
        """오버라이드 설정을 커맨드라인 인수로 변환"""
        args = []
        
        # 설정 매핑 정의
        override_mappings = {
            'output_path': 'MoviePipeline.OutputPath',
            'resolution': 'MoviePipeline.OutputResolution',
            'frame_rate': 'MoviePipeline.TargetFPS',
            'samples_per_pixel': 'MoviePipeline.SamplesPerPixel',
            'output_format': 'MoviePipeline.OutputFormat'
        }
        
        for key, value in overrides.items():
            if key in override_mappings:
                if key == 'resolution':
                    width, height = value
                    args.extend([
                        "-override_config",
                        f"{override_mappings[key]}=(X={width},Y={height})"
                    ])
                else:
                    args.extend([
                        "-override_config",
                        f"{override_mappings[key]}={value}"
                    ])
        
        return args
    
    def _create_deadline_info(self, job_info: Dict) -> Dict:
        """Deadline 제출용 정보 생성"""
        return {
            'JobInfo': {
                'Plugin': 'UnrealEngine',
                'Name': job_info['job_name'],
                'Comment': f"MRQ Config: {job_info['mrq_config']}",
                'Department': "3D",
                'Priority': 50,
                'ChunkSize': 1,
            },
            'PluginInfo': {
                'CommandLineArguments': ' '.join(job_info['command'][1:]),  # executable 제외
                'UnrealProjectPath': self.project_path,
                'Version': '5.2'  # 언리얼 버전
            }
        }

def main():
    manager = UnrealMRQManager(
        unreal_editor_path="C:/Program Files/Epic Games/UE_5.2/Engine/Binaries/Win64/UnrealEditor.exe",
        project_path="D:/Projects/MyUnrealProject/MyProject.uproject"
    )
    
    # 여러 렌더링 작업 정의
    render_jobs = [
        {
            'job_name': 'Shot_010',
            'mrq_config': '/Game/Movies/Shot_010_RenderQueue.Shot_010_RenderQueue',
            'overrides': {
                'output_path': 'D:/Renders/Shot_010',
                'resolution': (3840, 2160)
            }
        },
        {
            'job_name': 'Shot_020',
            'mrq_config': '/Game/Movies/Shot_020_RenderQueue.Shot_020_RenderQueue',
            'overrides': {
                'output_path': 'D:/Renders/Shot_020',
                'resolution': (3840, 2160)
            }
        }
    ]
    
    # 작업 처리
    processed_jobs = manager.batch_render(render_jobs)
    
    # 결과 출력
    for job in processed_jobs:
        print(f"\nJob: {job['job_name']}")
        print(f"Status: {job['status']}")
        print("Deadline Info:")
        print(json.dumps(job['deadline_info'], indent=2))

if __name__ == "__main__":
    main()
