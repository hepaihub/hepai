
import os, sys, signal
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Generator, Callable
import threading
import atexit
import time, asyncio
import traceback, inspect
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
import requests
import logging
from logging import Logger


from ._related_class import (
    WorkerNetworkInfo, ModelResourceInfo, WorkerStatusInfo, WorkerInfo,
    HWorkerModel, 
)

from .utils import get_uuid

@dataclass
class HWorkerArgs:  # (2) worker的参数配置和启动代码
    host: str = field(default="0.0.0.0", metadata={"help": "Worker's address, enable to access from outside if set to `0.0.0.0`, otherwise only localhost can access"})
    port: str = field(default="auto", metadata={"help": "Worker's port"})
    auto_start_port: int = field(default=42602, metadata={"help": "Worker's start port, only used when port is set to `auto`"})
    route_prefix: str = field(default="/apiv2", metadata={"help": "Route prefix for worker"})
    controller_address: str = field(default="http://localhost:42601", metadata={"help": "Controller's address"})
    controller_prefix: str = field(default="/apiv2", metadata={"help": "Controller's route prefix"})
    
    speed: int = field(default=1, metadata={"help": "Model's speed"})
    limit_model_concurrency: int = field(default=5, metadata={"help": "Limit the model's concurrency"})
    stream_interval: float = field(default=0., metadata={"help": "Extra interval for stream response"})
    no_register: bool = field(default=False, metadata={"help": "Do not register to controller"})
    permissions: str = field(default='groups: all; users: admin', metadata={"help": "Model's permissions, separated by ;, e.g., 'groups: all; users: a, b; owner: c'"})
    description: str = field(default='This is a demo worker of HaiDDF2 (HepAI Distrobuted Deployment Framework)', metadata={"help": "Model's description"})
    author: str = field(default=None, metadata={"help": "Model's author"})
    test: bool = field(default=False, metadata={"help": "Test mode, will not really start worker, just print the parameters"})



class CommonWorker:
    """
    Common Worker，用来实际处理各种函数
    """
    def __init__(self,
                 app: FastAPI,  # FastAPI app
                 model: HWorkerModel,  # 模型
                 worker_config: "HWorkerArgs",  # worker的配置
                 logger: Optional[Logger] = None,  # logger
                 **kwargs
                 ):
        # 配置
        self.config: HWorkerArgs = worker_config
        self.config_dict: Dict = self._init_config_dict(worker_config, **kwargs)
        
        # 网络信息相关项目
        self.network_info: WorkerNetworkInfo = self.get_network_info()
        
        # 模型资源信息相关
        self.model_permissions: Dict = self._init_permissions(self.config.permissions)  # 将str转换为dict

        # 状态信息相关
        self.app = app  # "HWorkerAPP" 
        self.speed = self.config_dict.get("speed", 1)
        self.status = "idle"

        # 初始化信息
        worker_id = self.config_dict.get("worker_id", None)
        self.worker_id = worker_id if worker_id else get_uuid(lenth=15, prefix="wk-")
        self.stream_interval = self.config_dict.get("stream_interval", 0)
        self.api_key = kwargs.get("api_key", "")
        self.model = model or HWorkerModel()

        self._is_deleted_in_controller = False  
        # 日志
        self.logger = logger or logging.getLogger(__name__)

        # 注册模型
        if not self.config.no_register:
            success: bool = self.register_to_controller()
            if success:
                self.heartbeat_thread = threading.Thread(
                    target=self.worker_heartbeat, 
                    daemon=True,
                    )
                self.heartbeat_thread.start()
            else:
                self._is_deleted_in_controller = True

        # 标识是否已经在controller中删除，如果已经删除，则exit_handler不再向controller发送删除信息
        # 用于适配controllre端主动向worker发送删除worker时
        atexit.register(self.exit_handler)

        self.status = "ready"

    @property
    def base_url(self):
        controller_addr = self.config.controller_address
        controller_prefix = self.config.controller_prefix
        if controller_prefix:
            return f'{controller_addr}{controller_prefix}'
        return controller_addr
    
    @property
    def worker_name(self):
        return self.model.name or self.model.__class__.__name__
    
    def _init_permissions(self, permissions: Optional[Union[str, Dict]]) -> Dict:
        """worker授予用户或者组的权限"""
        if permissions is None:
            return {}
        elif isinstance(permissions, dict):
            return permissions
        elif isinstance(permissions, str):
            """user: <user1>; user: <user2>; group: <group1>, ..."""
            prems = dict()
            for a in permissions.split(';'):
                user_or_group, name = a.split(':')
                user_or_group = user_or_group.strip()
                name = name.strip()
                assert user_or_group in ['owner', 'users', 'groups']
                names = name.split(',')  if ',' in name else [name]
                prems[user_or_group] = names
        else:
            raise ValueError(f"permissions should be str or dict, but got {type(permissions)}")
        return prems
    
    def _init_config_dict(self, config: HWorkerArgs, **kwargs):
        config_dict = config.__dict__
        for k, v in kwargs.items():
            if k in config_dict:
                raise ValueError(f"Duplicate key: {k}, Please check the config class and the kwargs.")
            config_dict[k] = v
        return config_dict
    
    def worker_heartbeat(self):
        """间隔发送心跳的函数"""
        heartbeat_interval = self.config_dict.get("heartbeat_interval", 60)
        while True:
            time.sleep(heartbeat_interval)
            self.register_to_controller(heartbeat_flag=True)
    
    def get_network_info(self) -> WorkerNetworkInfo:
        host = self.config.host
        from .utils import auto_port, auto_worker_address, get_hostname
        port = auto_port(port=self.config.port, start=self.config.auto_start_port)
        worker_address = auto_worker_address(worker_address="auto", host=host, port=port)
        route_prefix = self.config.route_prefix
        if route_prefix:
            worker_address = f"{worker_address}{route_prefix}"
        return WorkerNetworkInfo(
            host=self.config.host,
            port=port,
            host_name=get_hostname(),
            route_prefix=route_prefix,
            worker_address=worker_address,
        )
    
    def get_model_resource_info(self) -> ModelResourceInfo:
        model_name = self.model.name or self.model.__class__.__name__
        permmisions = self.model_permissions
        # callable_functions = self.get_callable_functions(self.model)
        callable_functions = self.get_all_callable_functions(self.model)
        return ModelResourceInfo(
            model_name=model_name,
            model_type=self.config_dict.get("model_type", "common"),
            model_version=self.config_dict.get("model_version", "1.0"),
            model_description=self.config.description,
            model_author=self.config.author,
            model_onwer=permmisions.get("owner", None),
            model_users=permmisions.get("users", []),
            model_groups=permmisions.get("groups", []),
            model_functions=callable_functions,
        )
    
    def get_callable_functions(self, cls):
        """获取一个类的所有可调用函数"""
        callable_funcs = []
        for name, method in inspect.getmembers(cls, inspect.isfunction):
            # Check if method belongs to the class and is not inherited
            if method.__qualname__.startswith(cls.__name__ + '.'):
                callable_funcs.append(name)
        return callable_funcs
    
    def get_all_callable_functions(self, cls: HWorkerModel):
        """获取一个类的所有可调用函数，包括父类的"""
        # Recursive function to collect callable methods from the class and its parent classes
        methods = {}
   
        # Traverse the method resolution order (MRO), which includes the class and its bases
        for subclass in inspect.getmro(cls.__class__):
            for name, method in inspect.getmembers(subclass, inspect.isfunction):
                methods[name] = method
        callable_funcs = list(methods.keys())

        # 再判断这些函数是不是可以远程调用的
        callable_funcs = [f for f in callable_funcs if hasattr(methods[f], "is_remote_callable")]

        return callable_funcs


    def get_status_info(self) -> WorkerStatusInfo:
        return WorkerStatusInfo(
            speed=self.speed,
            queue_length=self.app.get_queue_length(),
            status=self.status,
        )
    
    async def shutdown_worker(self) -> None:
        await asyncio.sleep(1)
        os.kill(os.getpid(), signal.SIGINT)
    
    def get_worker_info(self) -> WorkerInfo:
        worker_info = WorkerInfo(
            id=self.worker_id,
            network_info=self.network_info,
            resource_info=self.get_model_resource_info(),
            status_info=self.get_status_info(),
            check_heartbeat=True,
            vserion=self.config_dict.get("version", "2.0"),
            metadata={},
        )
        return worker_info
    
    def set_model_pressions(self, permissions: Dict):
        """设置模型的权限, 用于动态更新，仅限于owner和admin"""
        self.model_permissions = permissions

    def set_model_speed(self, speed: int):
        """设置模型的速度, 用于动态更新，仅限于owner和admin"""
        self.speed = speed
    
    ### --- 此处开始是向controller发送请求的相关函数 --- ###
    @property
    def headers(self) -> dict:
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        return headers
    
    def register_to_controller(self, heartbeat_flag: bool = False):
        """注册和心跳"""
        # logger.info(f'Register model "{self.model_name}" to controller.')
        
        # url = self.base_url + '/register_worker'
        url = self.base_url + '/worker/register_worker'
        worker_info: WorkerInfo = self.get_worker_info()
        data = worker_info.to_dict()

        try:
            r = requests.post(url, json=data, headers=self.headers)
            if r.status_code != 200:
                raise Exception(f"Register worker failed. Error: {r.text}\n  Request url: {url}\n  Worker_info: {worker_info}")
            
        except Exception as e:
            if heartbeat_flag:
                print(f"Sent heartbeat failed, ignore... url: {url}, worker_id: {self.worker_id}")
                pass
            else:
                self.logger.warning(f"Register worker to controller failed, pass...")
                return False
        self.logger.info(f"Register worker successful")
        return True
  
    def exit_handler(self):
        """
        退出时向Contoller发送退出信息
        """
        if self.config.no_register:  # 初始化时没有注册到controller，不需要发送退出信息
            return
        if self._is_deleted_in_controller:
            return
        # logger.info(f'Remove model "{self.model_name}" from controller {self.controller_addr}, ')
        # url = self.base_url + "/stop_worker"
        url = self.base_url + "/worker/stop_worker"
        
        worker_info: WorkerInfo = self.get_worker_info()
        wid = worker_info.id
        payload = {"worker_id": wid, "permanent": False}
        # data = worker_info.to_dict()
        r = requests.post(
            url, 
            json=payload, 
            headers=self.headers)
        assert r.status_code == 200, f"Stop worker failed. {r.text}\n worker_info: {worker_info}"
        # logger.info(f'Done. {r.text}') 
        print(f"Stop worker successful. res: {r.text}")

    ### --- 此处是处理Controller的请求的相关函数 --- ###
    def unified_gate(
            self, 
            function: str,
            args,
            kwargs,
            ):
        """
        统一入口, v2.0更新为符合FastAPI规范，易于检测错误
        """
        # assert "function" in kwargs, "function is required"
        # function = kwargs.pop("function")
        
        has_function = hasattr(self.model, function)
        if not has_function:
            raise HTTPException(status_code=404, detail=f"Function `{function}` does not exist in the worker `{self.worker_name}`")
        is_callable = callable(getattr(self.model, function))
        is_remote_callable = hasattr(getattr(self.model, function), "is_remote_callable")
        if not is_callable:
            raise HTTPException(status_code=405, detail=f"Function `{function}` is not callable in the worker `{self.worker_name}`")
        if not is_remote_callable:
            raise HTTPException(status_code=405, detail=f"Function `{function}` is not remote callable in the worker `{self.worker_name}`, please add `@remote_callable` decorator to the function in worker model.")
        if has_function and is_callable and is_remote_callable:
            func: Callable = getattr(self.model, function)
            try:
                # res =  func(**kwargs)
                res = func(*args, **kwargs)
                if isinstance(res, Generator):
                    return StreamingResponse(res, media_type="application/octet-stream")
                return res
            except Exception as e:
                # 获取报错类型：e.__class__.__name__
                tb_str = traceback.format_exception(*sys.exc_info())
                tb_str = "".join(tb_str)
                # logger.debug(f"Error: {e}.\nTraceback: {tb_str}")
                e_class = e.__class__.__name__
                error_msg = e.__dict__.get("body", None)
                error_msg = error_msg if error_msg else f"{e_class}: {str(e)}"
                if e_class == "ModuleNotFoundError":
                    raise HTTPException(status_code=404, detail=error_msg)
                elif e_class == "NotImplementedError":
                    raise HTTPException(status_code=501, detail=error_msg)
                elif e_class == "BadRequestError":
                    raise HTTPException(status_code=400, detail=error_msg)
                elif e_class == "TypeError":
                    raise HTTPException(status_code=500, detail=error_msg)
                elif e_class == "APITimeoutError":
                    raise HTTPException(status_code=504, detail=error_msg)
                ## TODO: 其他报错类型转换为合适的报错状态码
                error_msg2 = f"{e_class}: {str(e)}"
                print(f"一种新的错误类型：{e_class}, 错误信息：{error_msg}\n{error_msg2}")
                raise HTTPException(status_code=400, detail=f'{error_msg2}\n{error_msg2}')
        else:
            raise HTTPException(status_code=404, detail=f"Function `{function}` does not exist or is not callable in the worker `{self.worker_name}`")
    
