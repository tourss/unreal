import sys
import os

# Unreal Engine의 Python 환경을 초기화
unreal_root = "C:/Program Files/Epic Games/UE_5.4/Engine"  # Unreal Engine의 루트 경로
engine_python_path = os.path.join(unreal_root, "Binaries", "Python")

if engine_python_path not in sys.path:
    sys.path.append(engine_python_path)

# 필요한 커스텀 Python 모듈 로드
custom_python_module = os.path.join(os.path.dirname(__file__), "Executors", "MyExecutor.py")
if custom_python_module not in sys.path:
    sys.path.append(custom_python_module)

# 필요한 경우 Unreal Editor에서 추가적인 초기화 작업을 할 수 있습니다
import unreal
