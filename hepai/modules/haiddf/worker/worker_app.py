



from typing import Dict, List, Literal, Optional, Union, Generator, Callable
from dataclasses import dataclass, field

from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.background import BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse, HTMLResponse
from fastapi.params import Query

import asyncio
from asyncio import Semaphore
import threading
from pydantic import BaseModel
from logging import Logger

from ._worker_class import HWorkerArgs, HWorkerModel, CommonWorker
from ._related_class import WorkerStoppedInfo, WorkerInfoRequest, WorkerUnifiedGateRequest


class FunctionParamsItem(BaseModel):
    args: List = []
    kwargs: Dict = {}


class HWorkerAPP(FastAPI):
    """
    FastAPI app for worker
    """

    def __init__(
            self,
            model: HWorkerModel,
            worker_config: HWorkerArgs = None,
            logger: Logger = None,
            **kwargs):
        super().__init__()
        worker_config = worker_config if worker_config is not None else HWorkerArgs()
        # 用于控制模型访问的信号量
        self.limit_model_concurrency = worker_config.limit_model_concurrency
        self.model_semaphore: Semaphore = None
        self.global_counter = 0

        self.logger = self.get_logger(logger)
        self.worker = CommonWorker(
            app=self, model=model, worker_config=worker_config, 
            logger=self.logger,
            **kwargs)
        self._init_routers()

    def _init_routers(self):
        
        router_prefix = self.worker.config_dict.get("route_prefix", "")
        index_router = APIRouter(prefix="", tags=["base"])
        index_router.get("/")(self.index)
        self.include_router(index_router)

        router = APIRouter(prefix=router_prefix, tags=["worker"])
        router.post("/worker_unified_gate/")(self.worker_unified_gate)
        router.post("/worker_unified_gate/{function}")(self.worker_unified_gate)
        router.get("/worker_get_status")(self.worker_get_status)
        router.post("/shutdown_worker")(self.shutdown_worker)
        router.post("/worker/get_worker_info")(self.get_worker_info)  # 这个路由是为了与controller相同的格式，使得client也能调用
        router.post("/worker/unified_gate")(self.worker_unified_gate)  # 这个路由是为了与controller相同的格式，使得client也能调用

        self.include_router(router)

    @classmethod
    def get_logger(cls, logger: Logger = None):
        if logger is None:
            try:
                from ...utils._logger import Logger
                logger = Logger.get_logger("worker_app.py")
            except:
                import logging
                logger = logging.getLogger("worker_app.py")
        return logger

    @property
    def host(self):
        return self.worker.network_info.host
    
    @property
    def port(self):
        return self.worker.network_info.port

    def get_queue_length(self):
        model_semaphore: asyncio.Semaphore = self.model_semaphore
        if model_semaphore is None:
            return 0
        else:
            _value = model_semaphore._value
            _num_waiters = len(model_semaphore._waiters) if model_semaphore._waiters is not None else 0
            return self.limit_model_concurrency - _value + _num_waiters
    
    def release_model_semaphore(self):
        if self.model_semaphore is not None:
            self.model_semaphore.release()

    async def index(self):
        worker_name = self.worker.worker_name
        content = f"""
        <html>
            <head>
                <title>HepAI Worker Info</title>
            </head>
            <body>
                <h1>This is a worker of HepAI Distributed Deployment Framework</h1>
                <p>Worker Name: <strong>{worker_name}</strong></p>
                <p>Visit the <a href="/docs">API Documentation</a>.</p>
            </body>
        </html>
        """
        return HTMLResponse(content=content)
    
    # async def local_worker_unified_gate(
    #         self,
    #         worker_unified_gate_request: WorkerUnifiedGateRequest,
    #         model: str,
    #         function: str = "__call__",
    #         # user_auth: HAPIKeyAuth = api_key_auth,
    #         ) -> JSONResponse:
    #     wk_ugr = worker_unified_gate_request
    #     return self.worker.worker_unified_gate()


    async def worker_unified_gate(
            self,
            function_params: FunctionParamsItem,
            function: str = "__call__",
            ):
        # global model_semaphore, global_counter
        model_semaphore = self.model_semaphore  # 这个是用于获取队列长度的
        global_counter = self.global_counter
        global_counter += 1
        if model_semaphore is None:
            model_semaphore = asyncio.Semaphore(
                self.limit_model_concurrency)
        await model_semaphore.acquire()
        try:
            rst = self.worker.unified_gate(
                function=function, 
                args=function_params.args,
                kwargs=function_params.kwargs,)
        except Exception as e:  # 如果出错，也要释放锁
            self.release_model_semaphore()
            raise e
        # 如果成功，添加背景任务并返回
        background_tasks = BackgroundTasks()  # 背景任务
        background_tasks.add_task(self.release_model_semaphore)  # 释放锁
        return rst
    
    async def worker_get_status(self):
        return self.worker.get_status_info().to_dict()
    
    async def get_worker_info(
            self, 
            worker_info_request: WorkerInfoRequest,
            # user_auth: HAPIKeyAuth = api_key_auth,
            ) -> JSONResponse:
        """
        与controller的worker_info接口一致，以便client调用
        """
        return self.worker.get_worker_info()
    
    
    async def shutdown_worker(self, background_tasks: BackgroundTasks):
        """接收来自Ctrl的关闭worker的信息"""
        background_tasks.add_task(self.worker.shutdown_worker)
        self.worker._is_deleted_in_controller = True
        wid = self.worker.worker_id
        return WorkerStoppedInfo(
            id=wid, stopped=True, 
            message=f"Worker `{wid}` shutdown",
            shutdown=True,
            )

    @classmethod
    def register_worker(
            cls,
            model: HWorkerModel,
            worker_config: HWorkerArgs = None,
            daemon: bool = False,
            standalone: bool = False,
            **kwargs,
            ):
        """注册HModelWorker到HaiDDF"""
        from .utils import run_standlone_worker_demo
        if standalone:  # 独立程序模式，用户测试程序
            # cls().logger.info("Running `worker` in standalone mode.")
            print("Running `worker` in standalone mode.")
            return run_standlone_worker_demo()
        
        import uvicorn
        app: FastAPI = HWorkerAPP(model, worker_config=worker_config, **kwargs)
        def run_uvicron():
            uvicorn.run(app, host=app.host, port=app.port)

        if daemon:  # 守护进程模式，app workre在后台运行
            t = threading.Thread(target=run_uvicron, daemon=True)
            t.start()
            return app.worker.get_worker_info()
        else:  # 正常模式，app worker在前台运行
            run_uvicron()







