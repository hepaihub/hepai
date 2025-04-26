

import os
from pathlib import Path
import logging
from dataclasses import dataclass

import sys
try:
    from hepai.agents.version import __version__
except:
    here = Path(__file__).parent
    sys.path.insert(1, f'{here.parent.parent}')
    from hepai.agents.version import __version__

from hepai.agents.configs import CONST

@dataclass
class LoggingLevel:
    NOTSET: int = logging.NOTSET  # 0
    DEBUG: int = logging.DEBUG  # 10
    INFO: int = logging.INFO  # 20
    WARNING: int = logging.WARNING  # 30
    WARN: int = logging.WARN  # 30
    ERROR: int = logging.ERROR  # 40
    CRITICAL: int = logging.CRITICAL  # 50
    FATAL: int = logging.FATAL  # 50
    

class DrSaiLogger:

    @classmethod
    def get_logger(
        cls, 
        name: str, 
        dir: str = CONST.LOGGER_DIR,
        level: int = CONST.LOGGER_LEVEL,
        name_length: int = 12,
        **kwargs):

        if isinstance(level, str):
            level = getattr(LoggingLevel, level.upper())

        name = f'{name:^{name_length}}'
        format_str = f"\033[1;35m[%(asctime)s]\033[0m \033[1;32m[%(name)s]\033[0m " \
                    f"\033[1;36m[%(levelname)s]:\033[0m %(message)s"
        # datafmt = '%Y-%m%d %H:%M:%S'
        logger_file = f'{dir}/{Path(os.getcwd()).name}.log'


        # logging.basicConfig(level=level,
        #                     format=format_str,
        #                     datefmt='%Y%m%d %H:%M:%S',
        #                     )
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        if not os.path.exists(dir):
            os.makedirs(dir)

        fh = logging.FileHandler(logger_file)
        fh.setLevel(level=level)
        fh.setFormatter(logging.Formatter(
            format_str, 
            # datefmt=datafmt
            ))
        
        logger.addHandler(fh)
        return logger


if __name__ == "__main__":
    logger = DrSaiLogger.get_logger(
        "DrSai",
        level="DEBUG",
        # level="INFO",
        )
    logger.info("Hello, DrSai!")
    logger.debug("Hello, DrSai!")

