
from typing import Dict, Any
from ..._types import Stream
from .._resource import SyncAPIResource

from ..._return_class import (
    HWorkerListPage,
)
from ..._related_class import (
    WorkerInfo, HRemoteModel, WorkerStoppedInfo, WorkerStatusInfo,
)


class Worker(SyncAPIResource):

    @property
    def prefix(self) -> str:
        return "/worker"
    
    def list_workers(self):
        return self._get(
            f"{self.prefix}/list_workers",
            cast_to=HWorkerListPage,
        )

    def get_info(
            self,
            worker_id: str = None,
            model_name: str = None,
            ) -> WorkerInfo:
        assert worker_id or model_name, "Either worker_id or model_name should be provided."
        payload = {
            "worker_id": worker_id,
            "model_name": model_name,
        }
        return self._post(
            f"{self.prefix}/get_worker_info",
            cast_to=WorkerInfo,
            body=payload,
        )

    def get_status(
            self,
            worker_id: str,
            refresh: bool = False,
            ) -> WorkerStatusInfo:
        payload = {
            "worker_id": worker_id,
            "refresh": refresh,
        }
        return self._post(
            f"{self.prefix}/get_worker_status",
            cast_to=WorkerStatusInfo,
            body=payload,
        )
    
    def stop(
            self,
            worker_id: str,
            permanent: bool = False,
            ) -> WorkerStoppedInfo:
        payload = {
            "worker_id": worker_id,
            "permanent": permanent,
        }
        return self._post(
            f"{self.prefix}/stop_worker",
            cast_to=WorkerStoppedInfo,
            body=payload,
        )
    
    def refresh_all(self):
        return self._get(
            f"{self.prefix}/refresh_all_workers",
            cast_to=Dict[str, Any],
        )
    
    def get_remote_model(
            self,
            worker_id: str = None,
            model_name: str = None,
            ) -> HRemoteModel:
        worker_info: WorkerInfo = self.get_info(worker_id=worker_id, model_name=model_name)
        if not isinstance(worker_info, WorkerInfo):
            raise ValueError(f"Failed to get remote model: {worker_info}")
        from ..._remote_model import LRemoteModel
        return LRemoteModel(name=model_name, worker_info=worker_info, worker_resource=self)

    def request(
            self,
            target: dict,  # 请求目标模型和函数, such as {"model": model_name, "function": "__call__"}
            args: list = None, 
            kwargs: dict = None,
        ):
        # get model and function
        model = target.get("model")
        function = target.get("function")  
        # check if need stream
        stream = kwargs.get("stream", False) if kwargs is not None else False
        # set payload
        payload = dict()
        if args:
            payload["args"] = args
        if kwargs:
            payload["kwargs"] = kwargs

        if stream:
            return self._post(
                f"{self.prefix}/unified_gate/?model={model}&function={function}",
                body=payload,
                stream=True,
                stream_cls=Stream[Any],
                cast_to=Any,
            )
        return self._post(
            f"{self.prefix}/unified_gate/?model={model}&function={function}",
            cast_to=Any,
            body=payload,
        )
    
    def register(
            self,
            model: HRemoteModel = None,
            daemon: bool = False,
            standalone: bool = False,
            )  -> WorkerInfo:
        
        from ..._related_class import HWorkerAPP
        return HWorkerAPP.register_worker(model=model, daemon=daemon, standalone=standalone)