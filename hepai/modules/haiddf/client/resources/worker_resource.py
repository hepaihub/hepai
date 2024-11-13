



from typing import Literal, List, Dict, Any
import types
import functools


from .._related_class import (
    WorkerInfo, HWorkerModel, WorkerStoppedInfo, WorkerStatusInfo,
)
from ._base_resource import SyncAPIResource, HErrorResponse
from .._client_class import HWorkerListPage


class WorkerResource(SyncAPIResource):

    @property
    def path(self) -> str:
        """path of the worker resource, i.e. the prefix of the endpoint"""
        return "/worker"

    def info(self, worker_id: str=None, model_name: str=None, **kwargs) -> WorkerInfo:
        url = f'{self.base_url}{self.path}/get_worker_info'
        assert worker_id or model_name, "Either worker_id or model_name should be provided."
        payload = {
            "worker_id": worker_id,
            "model_name": model_name,
        }
        return self._post(
            url,
            json=payload,  # 写成params而非json是因为后端接收的是query string
            cast_to=WorkerInfo,
            **kwargs,
        )
    
    def status(self, worker_id: str, refresh: bool = False) -> WorkerStatusInfo:
        url = f'{self.base_url}{self.path}/get_worker_status'
        payload = {
            "worker_id": worker_id,
            "refresh": refresh,
        }
        return self._post(
            url,
            json=payload,
            cast_to=WorkerStatusInfo,
        )
    
    def request(
            self,
            # target: dict,
            params: dict,
            args: list,
            kwargs: dict,
            ):
        url = f'{self.base_url}{self.path}/unified_gate'
        payload = {
            # "target": target,
            "args": args,
            "kwargs": kwargs,
        }
        return self._post(
            url,
            params=params,
            json=payload,
        )
    
    def list(self, url: str=None) -> HWorkerListPage:
        url = f'{self.base_url}{self.path}/list_workers' if url is None else f'{self.base_url}{url}'
        return self._get(
            url,
            cast_to=HWorkerListPage,
            )
    
    def refresh_all(self) -> Dict:
        url = f'{self.base_url}{self.path}/refresh_all_workers'
        return self._get(
            url,
            cast_to=dict,
            )
    
    def register(
            self, 
            model: Dict, 
            daemon: bool=False,
            standalone: bool=False,
        ) -> WorkerInfo:
        
        from ...worker.worker_app import HWorkerAPP
        return HWorkerAPP.register_worker(model=model, daemon=daemon, standalone=standalone)
    
    
    def stop(self, worker_id: str, permanent: bool=False) -> WorkerStoppedInfo:
        url = f'{self.base_url}{self.path}/stop_worker'
        payload = {
            "worker_id": worker_id,
            "permanent": permanent,
        }
        return self._post(
            url,
            json=payload,
            cast_to=WorkerStoppedInfo,
            )

    def get_remote_model(self, model_name: str) -> "HRemoteModel":
        """
        Get remote model by model name
        """
        return HRemoteModel(model_name=model_name, worker_resource=self)
        

class HRemoteModel:

    def __init__(
            self,
            model_name: str,
            worker_resource: WorkerResource,
            ) -> None:
        self.model_name = model_name
        self.wr: WorkerResource = worker_resource
        worker_info: WorkerInfo = self.wr.info(model_name=model_name, worker_id=None, ignore_error=True)
        if isinstance(worker_info, HErrorResponse):
            raise ValueError(f"Failed to get remote model: {worker_info}")

        model_functions = worker_info.resource_info.model_functions
        # model_functions = ["train", "__call__"]
        if len(model_functions) == 0:
            raise ValueError(f"Remote model `{model_name}` has no functions can be called remotely, please check the worker model.")

        # 自动注册远程模型的函数
        for func in model_functions:
            original_func = self.function_warpper(model_name, func)
            # Use functools.wraps to preserve original function metadata when creating new methods
            # @functools.wraps(original_func)
            # def wrapper(*args, **kwargs):
            #     return original_func(*args, **kwargs)
            # setattr(self, func, types.MethodType(wrapper, self))
            setattr(self, func, types.MethodType(original_func, self))
   

    def function_warpper(self, model_name: str, function_name: str):
        def call_remote_function(*args, **kwargs):
            if isinstance(args[0], HRemoteModel):
                # 为了处理通过types.MethodType注册时，第一个参数是self的情况
                args = args[1:]
            return self.wr.request(
                params={
                    "model": model_name, 
                    "function": function_name
                    },
                args=args,
                kwargs=kwargs,
            )
        return call_remote_function
    
    def __call__(self, *args, **kwargs):
        return self.function_warpper(self.model_name, '__call__')(*args, **kwargs)

  