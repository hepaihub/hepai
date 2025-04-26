from dataclasses import dataclass, field
from typing import Optional, Any, Literal
from .base_assistant import BaseObject

@dataclass
class MessageCreation:
    message_id: str

    def to_dict(self):
        return self.__dict__

@dataclass
class StepDetails:
    type: str
    message_creation: MessageCreation 

    def to_dict(self):
        return {
            "type": self.type,
            "message_creation": self.message_creation.to_dict()
        }

@dataclass
class Usage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    def to_dict(self):
        return self.__dict__

@dataclass
class ThreadRunStep(BaseObject):
    id: str
    object: str
    created_at: int
    run_id: str
    assistant_id: str
    thread_id: str
    type: Literal["message_creation", "tool_calls"]
    status: str

    cancelled_at: Optional[int] = None
    completed_at: Optional[int] = None
    expired_at: Optional[int] = None
    failed_at: Optional[int] = None
    last_error: Optional[str] = None
    step_details: StepDetails = None
    usage: Usage = None

    @property
    def output_keys(self):
        return [
            "id", "object", "created_at", "run_id", "assistant_id", "thread_id", "type", "status",
            "cancelled_at", "completed_at", "expired_at", "failed_at", "last_error", "step_details", "usage"
            ]
    
    @property
    def allowed_update_keys(self):
        return [
            "status", "cancelled_at", "completed_at", "expired_at", "failed_at", "last_error", "step_details", "usage"
            ]

    def to_dict(self, only_output_keys=True):
        new_dict = dict()
        for k, v in self.__dict__.items():
            if only_output_keys and k not in self.output_keys:
                continue
            if k == "step_details" and v:
                v = v.to_dict()
            elif k == "usage" and v:
                v = v.to_dict()
            new_dict[k] = v
        return new_dict

    def construct_status_event(self, status: str=None):
        """根据状态构建事件对象"""
        status = status or self.status
        return {
            "data": self.to_dict(),
            "event": f"thread.run.step.{status}"
            }

    
