"""
基础类的定义
"""
import os
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Literal, Union, Optional, Any
import json
import inspect

@dataclass
class permission:
    groups: List[str] = field(default_factory=list, metadata={"help": "Model's groups"})
    users: List[str] = field(default_factory=list, metadata={"help": "Model's users"})
    owner: Union[str, None] = field(default=None, metadata={"help": "Model's owner"})

    def to_dict(self):
        return asdict(self)

@dataclass
class HModelConfig:
    name: str = field(default=None, metadata={"help": "Model's name"})
    permission: Union[str, Dict] = field(default=None, metadata={"help": "Model's permission, separated by ;, e.g., 'groups: all; users: a, b; owner: c', will inherit from worker permissions if not setted"})
    version: str = field(default="2.0", metadata={"help": "Model's version"})

class BaseWorkerModel:
    @classmethod
    def remote_callable(cls, func):
        """
        用来修饰一个函数，使得其可以被远程调用，未修饰的函数不能被远程调用
        Decorator to mark a method as remotely callable.
        """
        func.is_remote_callable = True
        return func
    
    @property
    def all_remote_callables(self):
        """
        获取所有被修饰的远程调用函数
        """
        methods = {}
        # Traverse the method resolution order (MRO), which includes the class and its bases
        for subclass in inspect.getmro(self.__class__):
            for name, method in inspect.getmembers(subclass, inspect.isfunction):
                methods[name] = method
        callable_funcs = list(methods.keys())
        # 再判断这些函数是不是可以远程调用的
        callable_funcs = [f for f in callable_funcs if hasattr(methods[f], "is_remote_callable")]
        return callable_funcs
    
    @classmethod
    def run(cls, **worker_overrides):
        """
        Run the worker model as a standalone service.

        """

        import uvicorn
        import hepai as hai
        from ..worker.worker_app import HWorkerAPP, HWorkerConfig

        model_config, worker_config = hai.parse_args((HModelConfig, HWorkerConfig))
        app = HWorkerAPP(
            cls(config=model_config),
            worker_config=worker_config,
            **worker_overrides,
            )  # Instantiate the APP, which is a FastAPI application.
        print(app.worker.get_worker_info(), flush=True)
        # 启动服务
        uvicorn.run(app, host=app.host, port=app.port)

    @classmethod
    def connect(
        cls,
        name: str,  # 远程模型的名称
        base_url: str = "https://aiapi.ihep.ac.cn/apiv2",  # 远程模型的地址
        api_key: str = None,  # 远程模型的API Key
        **kwargs,
        ):

        import logging
        import httpx
        # 将 httpx 的日志记录级别调整为 WARNING
        logging.getLogger("httpx").setLevel(logging.WARNING)
        
        api_key = api_key if api_key else os.environ.get("HEPAI_API_KEY")
        
        from hepai import HepAI
        client = HepAI(
            base_url=base_url,
            api_key=api_key,
            **kwargs,
            )

        from ..hclient._remote_model import LRModel

        model: LRModel = client.get_remote_model(model_name=name)
        return model
    
    @classmethod
    def list_models(
        cls,
        base_url: str = None,  # 远程模型的地址
        **kwargs,
        ):
        import logging
        import httpx
        # 将 httpx 的日志记录级别调整为 WARNING
        logging.getLogger("httpx").setLevel(logging.WARNING)

        base_url = base_url if base_url else "http://localhost:4260/apiv2"
        
        from hepai import HepAI
        client = HepAI(base_url=base_url,**kwargs)

        from ..hclient._remote_model import LRModel
        models = client.models.list()
        return models

    @classmethod
    async def async_connect(
            cls,
            name: str,  # 远程模型的名称
            base_url: str,  # 远程模型的地址
            # api_key: str = None,  # 远程模型的API Key
            **kwargs,
    ):

        import logging
        import httpx
        # 将 httpx 的日志记录级别调整为 WARNING
        logging.getLogger("httpx").setLevel(logging.WARNING)

        from hepai import AsyncHepAI
        client = AsyncHepAI(
            base_url=base_url,
            # api_key=api_key,
            **kwargs,
        )

        from ..hclient._remote_model import LRModel

        model: LRModel = await client.get_remote_model(model_name=name)
        return model

DEFAULT_STREAM_DATA = [
    1, 2, 3,
    "x", "y", "z",
    [[1, 2], [3, 4], [5, 6]],
    {"a": "b", "c": "d"},
]
    
class HRemoteModel(BaseWorkerModel):
    """
    The Remote Model of HAI Framework
    """
    def __init__(
            self,
            name: str = None,
            config: HModelConfig = None,
            ):
        self.config = config if config is not None else HModelConfig()
        assert isinstance(self.config, HModelConfig), "config must be an instance of HModelConfig"
        self.config.name = name if name is not None else self.config.name
        self.config.name = self.config.name if self.config.name else self.__class__.__name__
        self.name = self.config.name
        self.permission = self.config.permission

    @BaseWorkerModel.remote_callable
    def hello_world(self, *args, **kwargs):
        """An example of a function that returns a string"""
        return f"Hello world! You are using the HepAI worker model with args: `{args}`, kwargs: `{kwargs}`"

    @BaseWorkerModel.remote_callable
    def get_int(self, a: int = 1, b: int = 2) -> int:
        """An example of a function that returns an int type"""
        return a + b
    
    @BaseWorkerModel.remote_callable
    def get_float(self, a: float = 1.1, b: float = 2.2) -> float:
        """An example of a function that returns a float type"""
        return a + b
    
    @BaseWorkerModel.remote_callable
    def get_list(self, a: List[int] = [1, 2], b: List[int] = [3, 4]) -> List[int]:
        """An example of a function that returns a list type"""
        return a + b
    
    @BaseWorkerModel.remote_callable
    def get_dict(self, a: Dict[str, int] = {"a1": 1}, b: Dict[str, int] = {"a2": 2}) -> Dict[str, int]:
        """An example of a function that returns a dict type"""
        return {**a, **b}
    
    @BaseWorkerModel.remote_callable
    def get_stream(self, data: Any = None, interval: float = 0.2):
        """An example of a function that returns a stream type"""

        data = data if data is not None else DEFAULT_STREAM_DATA
        for i, x in enumerate(data):
            time.sleep(interval)  # 注：此处为了演示，故意加了延迟，实际使用时应该去掉
            yield f"data: {json.dumps(x)}\n\n"

    @BaseWorkerModel.remote_callable
    def __call__(self, *args, **kwargs):
        return f"Hello world! You are calling function `__call__` of the HepAI remote model with args: `{args}`, kwargs: `{kwargs}`"

class HRModel(HRemoteModel):
    """
    Alias of HepAI Remote Model
    """
    ...
    

@dataclass
class ModelResourceInfo:
    """
    Model Resource Info for Worker, such as llm, nn, preceptor, actuator, etc.
    """
    model_name: str = field(default="<default_modelname>", metadata={"help": "Model's name"})
    model_type: str = field(default="common", metadata={"help": "Model's type"})
    model_version: str = field(default="1.0", metadata={"help": "Model's version"})
    model_description: str =field(default="<This is model description.>", metadata={"help": "Model's description"})
    model_author: Union[str, List[str], None] = field(default="", metadata={"help": "Model's author"})
    model_onwer: Union[str, None] = field(default="", metadata={"help": "Model's onwer"})
    model_groups: List[str] = field(default_factory=list, metadata={"help": "Model's groups"})
    model_users: List[str] = field(default_factory=list, metadata={"help": "Model's users"})
    model_functions: List[str] = field(default_factory=list, metadata={"help": "Model's functions that can be called by remote"})

    def to_dict(self):
        return asdict(self)

@dataclass
class WorkerStatusInfo:
    """
    Worker Status Info, will be dynamic updated
    """
    speed: int = field(default=1, metadata={"help": "Worker's speed, the number of requests that can be processed per second"})
    queue_length: int = field(default=0, metadata={"help": "Worker's queue length"})
    status: Literal["idle", "ready", "busy", "error"] = "idle"

    def is_valid(self):
        """是信息是否可用，即相关信息是否已被填入，而不是None"""
        return self.speed > 0 and self.queue_length >= 0
    
    def to_dict(self):
        return asdict(self)


@dataclass
class WorkerNetworkInfo:
    """
    Network Info for Worker
    """
    host: str = field(default="127.0.0.1", metadata={"help": "Worker's host"})
    port: int = field(default=42602, metadata={"help": "Worker's port"})
    route_prefix: Union[str, None] = field(default="", metadata={"help": "Worker's route prefix, default is '/', the worker's address will be `http://host:port/route_prefix/other_router` if setted"})
    host_name: str = field(default="localhost", metadata={"help": "Worker's host name"})
    worker_address: Union[None, str] = field(default="", metadata={"help": "Worker's address, will be auto generated if not setted"})

    def check_and_autoset_worker_address(self):
        """自动检查并设置worker_address"""
        if self.worker_address in ["", None]:
            if self.route_prefix in ["", None]:
                self.worker_address = f"http://{self.host}:{self.port}"
            else:
                self.worker_address = f"http://{self.host}:{self.port}/{self.route_prefix}"
        return self.worker_address

    def to_dict(self):
        return asdict(self)


@dataclass
class WorkerInfo:
    """
    Worker Info
    v2.1.2 support multi model
    """
    id: str
    type: Literal["llm", "actuator", "preceptor", "memory", "common"] = "common"
    network_info: WorkerNetworkInfo = field(default_factory=WorkerNetworkInfo, metadata={"help": "Worker's network info"})
    resource_info: List[ModelResourceInfo] = field(default_factory=list, metadata={"help": "Model's resource info"})
    status_info: WorkerStatusInfo = field(default_factory=WorkerStatusInfo, metadata={"help": "Worker's status info"})
    check_heartbeat: bool = True
    last_heartbeat: Union[int, None] = None
    vserion: str = "2.0"
    metadata: Dict = field(default_factory=dict, metadata={"help": "Worker's metadata"})

    def __post_init__(self):
        """在实例化本类时，自动检查network_info等是否Dict, 并转换为相应的对象"""
        if isinstance(self.network_info, dict):
            self.network_info = WorkerNetworkInfo(**self.network_info)
        if isinstance(self.resource_info, list):
            # 后处理自动把json处理成对象
            for i, mr in enumerate(self.resource_info):
                if isinstance(mr, dict):
                    self.resource_info[i] = ModelResourceInfo(**mr)
        if isinstance(self.status_info, dict):
            self.status_info = WorkerStatusInfo(**self.status_info)

    def to_dict(self):
        return asdict(self)
    
    @property
    def model_names(self):
        return [x.model_name for x in self.resource_info]
    
    def get_model_resource(self, model_name: str) -> ModelResourceInfo:
        """v2.1.2多模型模式下，获取模型信息"""
        mr = [x for x in self.resource_info if x.model_name == model_name]
        if len(mr) != 1:
            raise ValueError(f'[WorkerInfo] Failed to get_model_info by name `{model_name}`, got {len(mr)} models')
        return mr[0]
    
    def get_model_index(self, model_name: str) -> int:
        """根据模型名，获取其在resource_info中的索引"""
        return self.model_names.index(model_name)
    
    
    def to_openai_list_models(self) -> Dict:
        """转换为OpenAI格式的list_models的返回列表"""
        data = []
        for i, rec in enumerate(self.resource_info):
            tmp = {}
            tmp["id"] = rec.model_name
            tmp["created"] = None
            tmp["object"] = "model"
            tmp['owned_by'] = rec.model_onwer
            data.append(tmp)
        return data


from pydantic import BaseModel

class WorkerInfoItem(BaseModel):
    """用于FastAPI的WorkerInfo"""
    id: str = field(default="wk-default_id", metadata={"help": "Worker's id"})     
    type: Union[Literal["llm", "actuator", "preceptor", "memory", "common"], str] = "common"
    network_info: WorkerNetworkInfo = field(default_factory=WorkerNetworkInfo, metadata={"help": "Worker's network info"})
    resource_info: List[ModelResourceInfo] = field(default_factory=list, metadata={"help": "Model's resource info"})
    status_info: WorkerStatusInfo = field(default_factory=WorkerStatusInfo, metadata={"help": "Worker's status info"})
    check_heartbeat: bool = field(default=True, metadata={"help": "Check worker's heartbeat"})
    last_heartbeat: Union[int, None] = field(default=None, metadata={"help": "Worker's last heartbeat"})
    vserion: str = field(default="2.0", metadata={"help": "Worker's version"})
    metadata: Dict = field(default_factory=dict, metadata={"help": "Worker's metadata"})


@dataclass
class WorkerStoppedInfo:
    id: str = field(metadata={"help": "Worker's id"}) 
    stopped: bool = field(metadata={"help": "Worker's stopped flag"})
    message: str = field(default=None, metadata={"help": "Worker's stopped message"})
    shutdown: bool = field(default=False, metadata={"help": "Worker's shutdown"})

    def to_dict(self):
        return {
            "id": self.id,
            "stopped": self.stopped,
            "message": self.message,
            "shutdown": self.shutdown,
        }