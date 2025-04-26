
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal, Generator
import time
import json
import uuid
from hepai.agents.configs import CONST

@dataclass
class BaseObject:

    def __post_init__(self):
        self._queue = None  # 用于收集事件的队列

    @property
    def queue(self):
        if self._queue is None:
            import queue
            self._queue = queue.Queue()
        return self._queue

    @property
    def output_keys(self) -> List[str]:
        raise NotImplementedError("Please implement the property `output_keys` in the subclass of `BaseObject`")
    
    @property
    def allowed_update_keys(self) -> List[str]:
        raise NotImplementedError("Please implement the property `allowed_update_keys` in the subclass of `BaseObject`")

    def to_dict(self, only_output_keys=True):
        if only_output_keys:
            return {k: v for k, v in self.__dict__.items() if k in self.output_keys}
        return self.__dict__
    
    def update(self, auto_metadata=False, **new_info):
        """
        更新对象的信息
        :param auto_metadata: 是否自动更新metadata，自动更新"modified"和"modified_at"字段
        """
        for k, v in new_info.items():
            assert k in self.allowed_update_keys, f"Key `{k}` is not allowed to update"
            setattr(self, k, v)
        if auto_metadata:
            self.metadata["modified"] = True
            self.metadata["modified_at"] = int(time.time())
        return self
    
    def get(self, key, default=None):
        return getattr(self, key, default)
    
    def event_generator(self) -> Generator:
        """
        事件生成器，用于流式输出的事件
        """
        end_status = ["completed", "failed", "incomplete", "cancelled", "expired"]
        interval = CONST.EVENT_INTERVAL
        timeout = CONST.EVENT_TIMEOUT
        ctime = time.time()
        while True:
            ### 有事件时，直接返回
            if not self.queue.empty():
                data = self._queue.get()
                # 如果队列中本来就是一个生成器，则返回生成器内容
                if isinstance(data, Generator):
                    for x in data:
                        yield x
                else:  # 否则，直接返回数据
                    yield data
                time.sleep(0.05)
                continue
            # 没有事件，看是否已经结束
            if self.status in end_status:
                break
            # 等待事件
            waited_time = time.time() - ctime
            if waited_time > timeout:
                break
            time.sleep(interval)  

    @property
    def valid_status(self):
        return ["queued", "created", "requires_action", "in_progress", 
                "completed", "failed", "cancelling", "cancelled", "expired"]
    
    def set_status(self, value: str, **kwargs):
        """
        带有事件收集器的状态设置方法
        :param emit: 是否发送事件，事件会被放入队列中并通过事件生成器通过流式输出反馈给前端
        """
        value = value.lower()
        assert value in self.valid_status, f"Invalid status of `ThreadRun`: {value}"
        self.status = value

        if value == "completed":
            self.completed_at = int(time.time())

        emit = kwargs.get("emit", False)
        if emit:
            data = self.construct_status_event()
            sse_data = f"data: {json.dumps(data)}\n\n"
            self.queue.put(sse_data)
            # return self.status_event()
        # return self.status
            
    def auto_id(self, prefix: str = '', length: int = 30, deduplicate: bool | List = True):
        """
        自动生成一个20位的id。
        """
        new_id = uuid.uuid4().hex
        short_id = str(new_id).replace('-', '')
        short_id = prefix + short_id[:length-len(prefix)]
        return short_id
    
    def construct_status_event(self):
        raise NotImplementedError("Please implement the method `construct_status_event` in the subclass of `BaseObject`")
    
    def status_event(self, status=None, set_status=False):
        status = status or self.status
        if set_status:
            if status is None:
                raise ValueError("Status is required when `set_status` is True")
            self.set_status(status, emit=False)
        yield f'data: {json.dumps(self.construct_status_event(status=status))}\n\n'

        # raise NotImplementedError("Please implement the method `status_event` in the subclass of `BaseObject`")
    

@dataclass
class Tool:
    type: str

@dataclass
class Assistant(BaseObject):
    id: str
    object: str
    model: str
    created_at: int
    name: str
    description: Optional[str]
    instructions: str
    tools: List[Tool]
    tool_resources: Dict[str, Any]
    metadata: Dict[str, Any]
    top_p: float
    temperature: float
    response_format: str

    username: str
    order_id: str

    agent_type: Literal["AssistantAgent", "HostAgent", "Human", "Planner", "Coder", "Tester"] = "AssistantAgent"
    deleted: Optional[bool] = False

    @property
    def output_keys(self):
        """定义了网络请求时需要返回的字段"""
        return ["id", "object", "model", "created_at", "name", "description", 
                "instructions", "tools", "tool_resources", "metadata", "top_p",
                "temperature", "response_format", "username", "order_id", "agent_type", "deleted"]
    
    @property
    def allowed_update_keys(self):
        return ["model", "name", "description", "instructions", "tools", "tool_resources", "metadata", "temperature", "top_p", "response_format", "deleted"]
    

@dataclass
class AssistantDeleted:
    id: str
    object: str = "assistant.deleted"
    deleted: bool = True