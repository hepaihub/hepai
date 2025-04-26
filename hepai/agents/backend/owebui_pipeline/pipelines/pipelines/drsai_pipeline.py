from typing import List, Union, Generator, Iterator, Callable, Awaitable, Optional
from pydantic import BaseModel, Field
import os
import requests
from openai import OpenAI



class Pipeline:
    class Valves(BaseModel):

        HEPAI_API_KEY: str = Field(
            default=os.getenv("HEPAI_API_KEY", "your-hepai-api-key-here"),
            description="大模型的服务商的apikey, 默认HepAI平台的api_key",
        )
        HEPAI_BASE_URL: str = Field(
            default="https://aiapi.ihep.ac.cn/apiv2",
            description="大模型的服务商的base_url, 默认HepAI平台的base_url",
        )
        DRSAI_NAME: str = Field(
            default="DrSai",
            description="你的Dr.Sai智能体后端的名称, 默认为DrSai",
        )
        DRSAI_URL: str = Field(
            default="http://localhost:42801/apiv2",
            description="你的Dr.Sai智能体后端的地址, 默认为http://localhost:42801/apiv2",
        )
        BASE_MODELS: str = Field(
            default="openai/gpt-4o",
            description="drsai后端使用的基座模型名称，默认openai/gpt-4o",
        )

    def __init__(self):
        # Optionally, you can set the id and name of the pipeline.
        # Best practice is to not specify the id so that it can be automatically inferred from the filename, so that users can install multiple versions of the same pipeline.
        # The identifier must be unique across all pipelines.
        # The identifier must be an alphanumeric string that can include underscores or hyphens. It cannot contain spaces, special characters, slashes, or backslashes.
        # self.id = "openai_pipeline"

        self.valves = self.Valves()
        self.user_id = None
        self.user_name = None
        self.user_email = None
        self.message_id = None
        self.chat_id = None
        self.name = self.valves.DRSAI_NAME 
        pass

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")
        pass
    
    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        print(f"inlet:{__name__}")
        # print(f"body: {body}")
        # print(f"user: {user}")
        self.user_id = user.get("id")
        self.user_name = user.get("name")
        self.user_email = user.get("email")
        self.chat_id = body.get("metadata").get("chat_id")
        self.message_id = body.get("metadata").get("message_id")
        body["user"] = user
        return body

    def pipe(
        self, user_message: str, 
        model_id: str, messages: List[dict], 
        body: dict, 
        headers: dict = None,
        **kwargs
    ) -> Union[str, Generator, Iterator]:
        
        self.backend_base_url = self.valves.DRSAI_URL # 连接drsai后端的地址
        # 配置hepai平台的api_key和base_url
        self.base_models = self.valves.BASE_MODELS # drsai后端使用的基座模型
        self.hepai_client = OpenAI(
            api_key=self.valves.HEPAI_API_KEY, base_url=self.valves.HEPAI_BASE_URL
        )

        # This is where you can add your custom pipelines like RAG.
        print(f"pipe:{__name__}") 

        # 构建访问openai的请求头和参数
        new_hearers = {}
        new_hearers["Authorization"] = f"Bearer {self.valves.HEPAI_API_KEY}"
        new_hearers["Content-Type"] = "application/json"

        # title_generation任务
        if body["stream"] is False:
            payload = {**body, "model": self.base_models}
            if "user" in payload:
                del payload["user"]
            if "chat_id" in payload:
                del payload["chat_id"]
            if "title" in payload:
                del payload["title"]
            # print(f"payload: {payload}")
        
            try:
                r = requests.post(
                    url=f"{self.valves.HEPAI_BASE_URL}/chat/completions",
                    json=payload,
                    headers=new_hearers,
                    # stream=True,
                )
                r.raise_for_status()
                response = r.iter_lines()
                return response
            except Exception as e:
                return f"Error: {e}"


        # 访问drsai多智能体框架后端接口
        # if user_message == "自动继续": # 适配特殊前端
        #     body["messages"][-1]["content"] = "exit"
        try:
            body["base_models"] = self.base_models
            body["chat_id"] = self.chat_id
            body["message_id"] = self.message_id
            r = requests.post(
                f"{self.backend_base_url}/chat/completions", 
                headers=new_hearers,
                json=body,
                stream=True,
                )
            r.raise_for_status()
            return r.iter_lines()
        except Exception as e:
            return f"Error: {e}"