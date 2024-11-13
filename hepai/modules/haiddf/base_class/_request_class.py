
from typing import Union, Optional, Literal, Dict, List
from pydantic import BaseModel, Field

class WorkerInfoRequest(BaseModel):
    worker_id: Optional[str] = Field(default=None, description="worker id")
    alias_model_name: Optional[str] = Field(default=None, alias="model_name", description="worker alias")


class WorkerUnifiedGateRequest(BaseModel):
    # target: dict = Field(..., description='such as {"model": "model_name", "func": "function_name"}')
    args: list = Field([], description="args")
    kwargs: dict = Field({}, description="kwargs")


class CreateUserRequest(BaseModel):
    username: str = Field(..., description="username")
    password: str = Field(default=None, description="password")
    user_level: str = Field(default='free', description="user level")
    user_groups: list = Field(default=None, description="user groups")
    email: str = Field(default=None, description="email")
    phone: str = Field(default=None, description="phone")
    auth_type: str = Field(default='local', description="auth type")
    umt_id: int = Field(default=None, description="umt id")
    cluster_uid: int = Field(default=None, description="cluster uid")
    remarks: Optional[str] = Field("", description="remarks")

class DeleteUserRequest(BaseModel):
    user_id: str = Field(..., description="user id")

class CreateAPIKeyRequest(BaseModel):
    key_name: str = Field(..., description="key name")
    valid_time: int = Field(30, description="valid time")
    allowed_models: Union[str, Dict] = Field(default="all", description="allowed models")
    user_id: Union[str, None] = Field(default=None, description="user id")
    remarks: str = Field("", description="remarks")

class DeleteAPIKeyRequest(BaseModel):
    api_key_id: str = Field(..., description="api key id")

    
    
