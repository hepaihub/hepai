"""
把所有client模块以外从外部引用的类定义引用到这里，方便把haiddf拷贝到hepai项目中使用
"""


# from ...controller.worker_manager._worker_class import (
#     ModelResourceInfo, WorkerStatusInfo, WorkerNetworkInfo, WorkerInfo,
#     HWorkerModel, WorkerStoppedInfo,
# )

# from ...controller.api_gateway._request_class import WorkerInfoRequest, WorkerUnifiedGateRequest

from ..base_class._worker_class import (
    ModelResourceInfo, WorkerStatusInfo, WorkerNetworkInfo, WorkerInfo,
    HRemoteModel, WorkerStoppedInfo, HRModel
)

from ..base_class._request_class import WorkerInfoRequest, WorkerUnifiedGateRequest