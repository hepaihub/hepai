
"""
Dr.Sai与OpenWebUI的Pipeline的API接口
"""
import os, sys
from pathlib import Path
here = Path(__file__).parent


pipe_dir = f'{here}/pipelines'


sys.path.insert(0, pipe_dir)
from .pipelines.main import app
from .pipelines.main import lifespan
sys.path.pop(0)