

from dataclasses import dataclass, field
from typing import Dict, Any, List, Callable
import threading
import time

from .base_assistant import BaseObject
from .base_thread_message import ThreadMessage
from .base_run import ThreadRun

@dataclass
class ToolResources:
    type: str
    url: str
    description: str

@dataclass
class ThreadDeleted:
    id: str
    object: str = "thread.deleted"
    deleted: bool = True


@dataclass
class Thread(BaseObject):
    id: Any  # ID的类型可能取决于具体情况，这里使用Any以保持通用性
    object: str
    created_at: int
    metadata: Dict[str, Any]
    tool_resources: Dict[str, Any]
    
    username: str
    order_id: str
    messages: List[ThreadMessage] = field(default_factory=list)
    runs: List[ThreadRun] = field(default_factory=list)

    deleted: bool = False

    def __post_init__(self):
        self._locked = False  # 标识线程锁定，锁定时无法向Thread添加新的消息，无法在Thread上执行新的Run
        self._running_run = None  # 当前正在运行的Run

        self.thread = None

    @property
    def allowed_update_keys(self):
        return ["metadata", "tool_resources", "messages", "deleted"]
    
    @property
    def output_keys(self):
        # 没username字段
        return ["id", "object", "created_at", "metadata", "tool_resources", 
                "username", "order_id", "messages", "runs", "deleted"]
    
    @property
    def locked(self):
        return self._locked
    

    def start(self, run_func: Callable, run: ThreadRun, **kwargs):
        """
        在Thread上开始一个Run
        """
        assert not self.locked, f"Thread `{self.id}` is locked, cannot start a new run at this time"
        daemon = kwargs.get("daemon", True)

        run.status = "in_progress"
        # 创建一个自线程
        self._running_run = run
        self.thread = threading.Thread(
            # target=self._run, 
            target=run_func,
            args=(run,), 
            daemon=daemon)
        self.thread.start()

        pass

    def _run(self, run: ThreadRun):
        """
        真正执行Run的函数
        """
        count = 0
        while True:
            print(f"Run `{run.id}` is running on thread `{self.id}`... {count}")
            count += 1
            time.sleep(1)
            if count >= 10:
                break
        run.status = "completed"
        run.completed_at = int(time.time())
        # self.stop(run=run)
        pass

    def stop(self, run: ThreadRun = None):
        """
        停止Thread上的所有Run
        """
        run = run or self._running_run
        assert run is not None, "No running run on this thread"
        if run.status == "requires_action":
            run.status = "expired"
            run.expires_at = int(time.time())
        elif run.status == "cancelling":
            run.status = "cancelled"
            run.cancelled_at = int(time.time())
        elif run.status == "completed":
            run.status = "completed"
            run.completed_at = int(time.time())
        elif run.status == "in_progress":
            raise Exception(
                "Cannot stop a running run when in progress, \
                specify a reason to stop it to determine the `failed` or `incomplete` status")
        self.thread.join()

        self._running_run = None
        pass

    



  