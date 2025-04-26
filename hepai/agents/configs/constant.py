"""
Here are constant values that are used in the project
"""

import os, sys
from pathlib import Path
here = Path(__file__).parent

from ..version import __appname__, __version__, __author__

## Basic Info
APPNAME = __appname__
AUTHOR = __author__
VERSION = __version__


## Paths
try:
    USERNAME = os.getlogin()  # 当前用户名
except:
    USERNAME = os.getenv('USER') or os.getenv('LOGNAME') or os.getenv('USERNAME')  # 适配WSL和windows环境

REPO_ROOT = f'{here.parent.parent}'  # 项目根目录
PROMPTS_DIR = f'{REPO_ROOT}/DrSai/configs/prompts'  # prompts目录
FS_DIR = f'{Path.home()}/.{APPNAME}'  # 文件系统目录

RUNS_DIR = f'{REPO_ROOT}/runs'  # 运行目录
FILE_DIR = f'{FS_DIR}/files'   # 文件目录
# CONFIG_DIR = f'{FS_DIR}/configs'  # 配置目录
CONFIG_DIR = f'{REPO_ROOT}/DrSai/configs'  # 配置目录

##
DEFAULT_USERNAME = "anonymous"  # for 创建assistant和获取assistant

## logger
LOGGER_DIR = f'{Path.home()}/.{APPNAME}/logs'  # 日志目录
LOGGER_LEVEL = "INFO"  # 日志级别
# LOGGER_LEVEL = "DEBUG"
# LOGGER_LEVEL = "WARNING"

## event
EVENT_TIMEOUT = 60  # 事件等待超时时间
EVENT_INTERVAL = 0.05  # 事件返回间隔时间
