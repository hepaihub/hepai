"""
把所有client模块以外从外部引用的类定义引用到这里，方便把haiddf拷贝到hepai项目中使用
"""


# from ...controller.worker_manager._worker_class import (
#     HWorkerModel, WorkerInfo, WorkerStatusInfo, WorkerStoppedInfo,
#     )

# from ...controller.user_manager._user_class import (
#     UserInfo, UserDeletedInfo, APIKeyInfo, APIKEYDeletedInfo,
#     )


### --- 为HepAI --- ###
from ..base_class._worker_class import (
    HWorkerModel, WorkerInfo, WorkerStatusInfo, WorkerStoppedInfo,
    )

from ..base_class._user_class import (
    UserInfo, UserDeletedInfo, APIKeyInfo, APIKEYDeletedInfo,
    )
