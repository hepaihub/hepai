"""
基础类的定义
"""

import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Literal, Union, Optional, Any


class BaseWorkerModel:

    @classmethod
    def remote_callable(cls, func):
        """
        用来修饰一个函数，使得其可以被远程调用，未修饰的函数不能被远程调用
        Decorator to mark a method as remotely callable.
        """
        func.is_remote_callable = True
        return func

class HWorkerModel(BaseWorkerModel):
    """
    The HepAI basic worker model class 
    """
    def __init__(self, name: str = "HWorkerModel"):
        self.name = name

    @BaseWorkerModel.remote_callable
    def hello_world(self, *args, **kwargs):
        """An example of a function that returns a string"""
        return f"Hello world! You are using the HepAI worker model with args: `{args}`, kwargs: `{kwargs}`"

    @BaseWorkerModel.remote_callable
    def get_int(self, a: int, b: int) -> int:
        """An example of a function that returns an int type"""
        return a + b
    
    @BaseWorkerModel.remote_callable
    def get_float(self, a: float, b: float) -> float:
        """An example of a function that returns a float type"""
        return a + b
    
    @BaseWorkerModel.remote_callable
    def get_list(self, a: List[int], b: List[int]) -> List[int]:
        """An example of a function that returns a list type"""
        return a + b
    
    @BaseWorkerModel.remote_callable
    def get_dict(self, a: Dict[str, int], b: Dict[str, int]) -> Dict[str, int]:
        """An example of a function that returns a dict type"""
        return {**a, **b}
    
    @BaseWorkerModel.remote_callable
    def get_stream(self, data: Any, interval: float = None):
        """An example of a function that returns a stream type"""

        for i, x in enumerate(data):
            time.sleep(interval)
            yield f"data: {x}\n\n"
            time.sleep(interval)

    @BaseWorkerModel.remote_callable
    def __call__(self, *args, **kwargs):
        return f"Hello world! You are calling function `__call__` of the HepAI remote model with args: `{args}`, kwargs: `{kwargs}`"


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

    def to_dict(self):
        return asdict(self)

@dataclass
class WorkerInfo:
    """
    Worker Info
    """
    id: str
    type: Literal["llm", "actuator", "preceptor", "memory", "common"] = "common"
    network_info: WorkerNetworkInfo = field(default_factory=WorkerNetworkInfo, metadata={"help": "Worker's network info"})
    resource_info: ModelResourceInfo = field(default_factory=ModelResourceInfo, metadata={"help": "Model's resource info"})
    status_info: WorkerStatusInfo = field(default_factory=WorkerStatusInfo, metadata={"help": "Worker's status info"})
    check_heartbeat: bool = True
    last_heartbeat: Union[int, None] = None
    vserion: str = "2.0"
    metadata: Dict = field(default_factory=dict, metadata={"help": "Worker's metadata"})

    def __post_init__(self):
        """在实例化本类时，自动检查network_info等是否Dict, 并转换为相应的对象"""
        if isinstance(self.network_info, dict):
            self.network_info = WorkerNetworkInfo(**self.network_info)
        if isinstance(self.resource_info, dict):
            self.resource_info = ModelResourceInfo(**self.resource_info)
        if isinstance(self.status_info, dict):
            self.status_info = WorkerStatusInfo(**self.status_info)

    def to_dict(self):
        return asdict(self)

from pydantic import BaseModel

class WorkerInfoItem(BaseModel):
    """用于FastAPI的WorkerInfo"""
    id: str = field(default="wk-default_id", metadata={"help": "Worker's id"})     
    type: Literal["llm", "actuator", "preceptor", "memory", "common"] = "common"
    network_info: WorkerNetworkInfo = field(default_factory=WorkerNetworkInfo, metadata={"help": "Worker's network info"})
    resource_info: ModelResourceInfo = field(default_factory=ModelResourceInfo, metadata={"help": "Model's resource info"})
    status_info: WorkerStatusInfo = field(default_factory=WorkerStatusInfo, metadata={"help": "Worker's status info"})
    check_heartbeat: bool = field(default=True, metadata={"help": "Check worker's heartbeat"})
    last_heartbeat: Union[int, None] = field(default=None, metadata={"help": "Worker's last heartbeat"})
    vserion: str = field(default="2.0", metadata={"help": "Worker's version"})
    metadata: Dict = field(default_factory=dict, metadata={"help": "Worker's metadata"})


class WorkerStoppedInfo(BaseModel):
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