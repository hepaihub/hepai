"""
这里是haiddf client类定义
"""
import os
import time
import httpx

from . import resources
from .resources._base_resource import SyncAPIResource
from .resources.worker_resource import HRemoteModel
from ._related_class import (
    HWorkerModel, WorkerInfo, WorkerStatusInfo, WorkerStoppedInfo,

)   


DEFAULT_API_KEY = os.getenv("DDF_API_KEY", None)

class HaiDDFClient(SyncAPIResource):
    key: resources.KeyManager
    http_client: httpx.Client

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        # max_retries: int = 0,
        proxy: str | None = None,
        print_result: bool = False,
        ):
        self.base_url = base_url if base_url is not None else f"http://localhost:42601/apiv2"
        self.api_key = api_key if api_key is not None else DEFAULT_API_KEY
        self.proxy = proxy
        self.timeout = timeout
        self.print_result = print_result
        super().__init__(client=self)

        self.key = resources.KeyManager(self)
        self.user = resources.UserResource(self)
        self.worker = resources.WorkerResource(self)

    ## --- 关于Worker的函数 --- ## 

    def list_workers(self):
        return self.worker.list()
    
    def request_worker(
            self,
            # target: dict,
            params: dict,
            args: list,
            kwargs: dict,
            ):
        """
        Request worker via http request

        Args:
            target (dict): Target worker and function, for example: {"model": "HWorkerModel", "function": "hello_world"}
            args (list): Arguments, can by any thing you defined in your `HWorkerModel`
            kwargs (dict): Keyword arguments, can by any thing you defined in your `HWorkerModel`
        """
        return self.worker.request(params=params, args=args, kwargs=kwargs)

    def register_worker(
            self,
            model: HWorkerModel,
            daemon: bool = False,
            standalone: bool = False,
            ):
        """
        注册Worker到服务端

        Args:
            model (HWorkerModel): Worker模型
            daemon (bool): 是否以守护进程方式启动
            standalone (bool): 是否以独立进程方式启动
        """
        return self.worker.register(model, daemon=daemon, standalone=standalone)

    def get_worker_info(
            self, 
            worker_id: str = None, 
            model_name: str = None,
            ) -> WorkerInfo:
        """
        Get worker info by worker_id via http request
    
        Args:
            worker_id (str): Worker ID
        """
        return self.worker.info(worker_id=worker_id, model_name=model_name)
    
    def get_worker_status(self, worker_id: str, refresh: bool = False) -> WorkerStatusInfo:
        """
        Get worker status by worker_id via http request
        
        Args:
            worker_id (str): Worker ID
            refresh (bool): Whether to refresh the worker status
        """
        return self.worker.status(worker_id=worker_id, refresh=refresh)

    def stop_worker(self, worker_id: str, permanent: bool = False) -> WorkerStoppedInfo:
        """
        Stop worker by worker_id via http request
        
        Args:
            worker_id (str): Worker ID
            permanent (bool): Whether to stop the worker permanently
        """
        return self.worker.stop(worker_id=worker_id, permanent=permanent)

    def refresh_all_workers(self) -> dict:
        """
        Refresh all workers
        """
        return self.worker.refresh_all()
    
    def get_remote_model(self, model_name: str) -> HRemoteModel:
        """
        Get a remote model
        """
        return self.worker.get_remote_model(model_name=model_name)
    
    ## # --- 关于User的函数 --- ##
    def list_users(self):
        """
        List all users
        Note: Only admin can use this function
        """
        return self.user.list_users()
    
    def create_user(self, **kwargs):
        """
        Create a new user
        Note: Only admin can use this function
        """
        return self.user.create_user(**kwargs)
    
    def delete_user(self, user_id: str):
        """
        Delete a user
        Note: Only admin can use this function
        """
        return self.user.delete_user(user_id=user_id)
    
    ### --- 关于Key的函数 --- ###
    def list_api_keys(self):
        """
        List all keys
        Note: Only admin can use this function
        """
        return self.key.list_api_keys()
    
    def create_api_key(self, **kwargs):
        """
        Create a new key
        Note: Only admin can use this function
        """
        return self.key.create_api_key(**kwargs)
    
    def delete_api_key(self, api_key_id: str):
        """
        Delete a key
        Note: Only admin can use this function
        """
        return self.key.delete_api_key(api_key_id=api_key_id)

if __name__ == "__main__":
    pass

    




