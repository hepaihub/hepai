from .app_worker import DrSaiAPP

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent, BaseChatAgent
from autogen_agentchat.teams import BaseGroupChat

from hepai import HRModel, HModelConfig, HWorkerConfig, HWorkerAPP
import hepai

import json
import os, subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Union
from fastapi import FastAPI
import uvicorn
from uvicorn import Server, Config
import asyncio

class DrSaiWorkerModel(HRModel):  # Define a custom worker model inheriting from HRModel.
    def __init__(
            self, 
            config: HModelConfig,
            drsaiapp: DrSaiAPP = None # 传入DrSaiAPP实例
            ):
        super().__init__(config=config)

        # if drsaiapp is not None and isinstance(drsaiapp, type):
        #     self.drsai = drsaiapp()  # Instantiate the DrSaiAPP instance.
        # else:
        #     self.drsai = drsaiapp or DrSaiAPP()  # Instantiate the DrSaiAPP instance.
        # pass
        self.drsai = drsaiapp

    @HRModel.remote_callable  # Decorate the function to enable remote call.
    def custom_method(self, a: int = 1, b: int = 2) -> int:
        """Define your custom method here."""
        return a + b

    @HRModel.remote_callable
    def get_stream(self):
        for x in range(10):
            yield f"data: {json.dumps(x)}\n\n"

    @HRModel.remote_callable
    async def a_chat_completions(self, *args, **kwargs):
        return await self.drsai.a_start_chat_completions(*args, **kwargs)
    
    # @HRModel.remote_callable
    # def models(self, *args, **kwargs):
    #     return self.drsai.a_list_models(*args, **kwargs)

        # request = self.params2request(*args, **kwargs)
        # return self.drsai.a_chat_completions(request=request)


@dataclass
class DrSaiModelConfig(HModelConfig):
    name: str = field(default="hepai/drsai", metadata={"help": "Model's name"})
    permission: Union[str, Dict] = field(default=None, metadata={"help": "Model's permission, separated by ;, e.g., 'groups: all; users: a, b; owner: c', will inherit from worker permissions if not setted"})
    version: str = field(default="2.0", metadata={"help": "Model's version"})

@dataclass
class DrSaiWorkerConfig(HWorkerConfig):
    host: str = field(default="0.0.0.0", metadata={"help": "Worker's address, enable to access from outside if set to `0.0.0.0`, otherwise only localhost can access"})
    port: int = field(default=42801, metadata={"help": "Worker's port, default is None, which means auto start from `auto_start_port`"})
    auto_start_port: int = field(default=42801, metadata={"help": "Worker's start port, only used when port is set to `auto`"})
    route_prefix: str = field(default="/apiv2", metadata={"help": "Route prefix for worker"})
    # controller_address: str = field(default="https://aiapi001.ihep.ac.cn", metadata={"help": "The address of controller"})
    controller_address: str = field(default="http://localhost:42601", metadata={"help": "The address of controller"})
    
    controller_prefix: str = field(default="/apiv2", metadata={"help": "Controller's route prefix"})
    no_register: bool = field(default=True, metadata={"help": "Do not register to controller"})
    

    permissions: str = field(default='groups: default; users: admin, xiongdb@ihep.ac.cn, ddf_free; owner: xiongdb@ihep.ac.cn', metadata={"help": "Model's permissions, separated by ;, e.g., 'groups: default; users: a, b; owner: c'"})
    description: str = field(default='This is Dr.Sai multi agents system', metadata={"help": "Model's description"})
    author: str = field(default=None, metadata={"help": "Model's author"})
    daemon: bool = field(default=False, metadata={"help": "Run as daemon"})
    type: str = field(default="drsai", metadata={"help": "Worker's type"})
    debug: bool = field(default=True, metadata={"help": "Debug mode"})


class Run_DrSaiAPP:
    def __init__(
            self,
            model_args: HModelConfig = DrSaiModelConfig,
            worker_args: HWorkerConfig = DrSaiWorkerConfig,
            **kwargs
            ):
        self.model_args, self.worker_args = hepai.parse_args((model_args, worker_args))

    async def run_drsai(
        self, 
        model_name: str = None,
        host: str = None,
        port: int = None,
        no_register: bool = True,
        controller_address: str = "http://localhost:42601",
        drsaiapp: DrSaiAPP = DrSaiAPP, # 传入DrSaiAPP实例:
        enable_pipeline: bool = False,
        ):
        
        if isinstance(drsaiapp, type): # 传入DrSaiAPP类而不是实例
            drsaiapp = drsaiapp()  # Instantiate the DrSaiAPP instance.

        if model_name is not None:
            self.model_args.name = model_name
        model = DrSaiWorkerModel(config=self.model_args, drsaiapp=drsaiapp)

        if host is not None:
            self.worker_args.host = host
        if port is not None:
            self.worker_args.port = port
        if no_register is not None:
            self.worker_args.no_register = no_register
        self.worker_args.controller_address = controller_address
        
        print(self.model_args)
        print()
        print(self.worker_args)
        print()
        
        if enable_pipeline:
            # 通过Pipeline适配OpenWebUI
            from .owebui_pipeline.api import app as owebui_pipeline_app
            from .owebui_pipeline.api import lifespan as owebui_lifespan
            # 实例化HWorkerAPP
            self.app: FastAPI = HWorkerAPP(
                model, worker_config=self.worker_args,
                lifespan=owebui_lifespan,
                )  # Instantiate the APP, which is a FastAPI application.
            self.app.mount("/pipelines", app=owebui_pipeline_app)
            
        else:
            self.app: FastAPI = HWorkerAPP(
                model, worker_config=self.worker_args
                )
       
        self.app.include_router(model.drsai.router)
      
        print(self.app.worker.get_worker_info(), flush=True)
        # # 启动服务
        # uvicorn.run(self.app, host=self.app.host, port=self.app.port)
        # 创建uvicorn配置和服务实例
        config = uvicorn.Config(
            self.app, 
            host=self.worker_args.host,  # 确保这里使用的是正确的host参数
            port=self.worker_args.port   # 确保这里使用的是正确的port参数
        )
        server = uvicorn.Server(config)
        # 在现有事件循环中启动服务
        if enable_pipeline:
            print(f"Enable OpenWebUI pipelines: `http://{self.worker_args.host}:{self.worker_args.port}/pipelines` with API-KEY: `{owebui_pipeline_app.api_key}`")
        await server.serve()

async def run_console(agent_factory: callable, task: str, **kwargs):
    drsaiapp = DrSaiAPP(agent_factory = agent_factory)
    result = await drsaiapp.start_console(task=task, **kwargs)
    if result is not None:
        return result


async def run_backend(agent_factory: callable, **kwargs):
    '''
    启动后端服务
    : args:
        enable_openwebui_pipeline: bool = False,  # 是否启动openwebui pipelines
    '''
    model_name: str = kwargs.pop("model_name", None)
    host: str =  kwargs.pop("host", None)
    port: int =  kwargs.pop("port", None)
    no_register: bool =  kwargs.pop("no_register", True)
    controller_address: str =  kwargs.pop("controller_address", "http://localhost:42601")
    enable_pipeline: bool = kwargs.pop("enable_openwebui_pipeline", False)
    
    drsaiapp = DrSaiAPP(
        agent_factory = agent_factory,
        **kwargs
        )
    
    await Run_DrSaiAPP().run_drsai(
        model_name=model_name,
        host=host,
        port=port,
        no_register=no_register,
        controller_address=controller_address,
        drsaiapp=drsaiapp,
        enable_pipeline=enable_pipeline,
    )

async def run_hepai_worker(agent_factory: callable, **kwargs):
    '''
    启动Hepai Worker
    '''
    model_name: str = kwargs.pop("model_name", None)
    host: str =  kwargs.pop("host", None)
    port: int =  kwargs.pop("port", None)
    no_register: bool =  kwargs.pop("no_register", False)
    controller_address: str =  kwargs.pop("controller_address", "https://aiapi.ihep.ac.cn")

    drsaiapp = DrSaiAPP(
        agent_factory = agent_factory,
        **kwargs
        )
    
    await Run_DrSaiAPP().run_drsai(
        model_name=model_name,
        host=host,
        port=port,
        no_register=no_register,
        controller_address=controller_address,
        drsaiapp=drsaiapp
    )

async def run_pipelines(pipelines_path: str, pipelines_port: int = 9097):

    NOTES=f"""++++++++++++++++++++++++++++++++\n\n
Open-webui pipelines is starting... \n
If any error, maybe you need to install open-webui first:
```
pip install open-webui
```
Any requriments refrence to https://github.com/open-webui/pipelines"

"""
    print(NOTES)

    # # 获取当前文件夹路径
    # current_path = os.path.dirname(os.path.abspath(__file__))
    # # 获取pipelines文件夹路径./pipelines/main.py
    # pipelines_path = os.path.join(current_path, "pipelines")
    command = f"pm2 start -n pipelines --cwd {pipelines_path} 'python main.py --port {pipelines_port}'"

    print(f"command: {command}")

    # 使用subprocess的asyncio接口来异步执行命令
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 获取命令输出
    stdout, stderr = await process.communicate()
    
    # 打印输出信息
    print(f'[Standard output]\n{stdout.decode()}')
    print(f'[Standard error]\n{stderr.decode()}')
    
    # 检查命令是否执行成功
    if process.returncode == 0:
        print(f'Command executed successfully, please visit http://localhost:{pipelines_port}\n"pm2 logs pipelines" to check logs. ')
    else:
        print('Command execution failed')
    
    await asyncio.create_subprocess_shell(
        "pm2 save",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    print("++++++++++++++++++++++++++++++++ \n\n")


async def run_openwebui(openwebui_port: int = 8088):

    NOTES= f'''++++++++++++++++++++++++++++++++\n\n
Open-webui frontend is starting... \n
If any error, maybe you need to install open-webui first:
```
pip install open-webui
```
Any requriments refrence to https://github.com/open-webui/open-webui \n
'''
    print(NOTES)

    # 将huggface镜像站点添加到环境变量：
    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

    # 构建命令
    command = f"pm2 start -n open-webui 'open-webui serve --port {openwebui_port}'"
    
    # 使用subprocess的asyncio接口来异步执行命令
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 获取命令输出
    stdout, stderr = await process.communicate()
    
    # 打印输出信息
    print(f'[Standard output]\n{stdout.decode()}')
    print(f'[Standard error]\n{stderr.decode()}')
    
    # 检查命令是否执行成功
    if process.returncode == 0:
        print(f'Command executed successfully, please visit http://localhost:{openwebui_port}\n"pm2 logs open-webui" to check logs. ')
    else:
        print('Command execution failed')
    
    await asyncio.create_subprocess_shell(
        "pm2 save",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    print("++++++++++++++++++++++++++++++++ \n\n")

async def run_drsai_app(agent_factory: callable, pipelines_path: str, **kwargs):
    ''''
    pm2 启动drsai后端/openwebui pipelines/openwebui前端
    '''
    # 检查是否安装了pm2
    try:
        subprocess.check_output("pm2 -v", shell=True)
    except:
        print("Please install pm2 first: `https://pm2.io/`")
        return

    # 并行启动所有服务
    pipelines_port = kwargs.pop("pipelines_port", 9097)
    openwebui_port = kwargs.pop("openwebui_port", 8088)
    await asyncio.gather(
        run_backend(agent_factory=agent_factory, **kwargs),
        run_pipelines(pipelines_path=pipelines_path, pipelines_port=pipelines_port),
        run_openwebui(openwebui_port=openwebui_port)
    )
