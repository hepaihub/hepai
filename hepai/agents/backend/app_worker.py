from hepai.agents import DrSai
import os, sys
from pathlib import Path
here = Path(__file__).parent
from typing import Generator, Optional, Union, Dict
from fastapi import FastAPI, Request, Header
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse, JSONResponse, PlainTextResponse
from dataclasses import dataclass, field
import json
from fastapi import FastAPI, Form, File, UploadFile, HTTPException, Response
from fastapi import APIRouter, Query
import traceback
import uvicorn
import inspect  
from collections.abc import AsyncGenerator 

try:
    from hepai.agents.version import __version__
except:
    sys.path.append(str(here.parent.parent))
    from hepai.agents.version import __version__

import hepai
from hepai import HepAI, HRModel, HModelConfig, HWorkerConfig, HWorkerAPP

from hepai.agents.utils import Logger

logger = Logger.get_logger("app_worker.py")

class DrSaiAPP(DrSai):
    '''
    chat/completion:路由,直接处理聊天和自动回复请求。
    该路由接收前端页面的请求，并返回相应的回复。
    该路由的请求参数包括:
    - messages: 输入的消息列表

    OpenAI Assistants格式的标准接口的DrSai后端服务:
    该后端服务通过http请求或者hepai的openai assistants格式的标准接口api, 提供Dr.Sai多智能体后端服务。
    包括:
    1. Assistants-相关接口，包括创建、获取、删除、更新助手。用于对接前后端Agents设置和前端页面的交互。
    2. Threads-相关接口，包括创建、获取、删除、更新会话。用于对接前端页面的会话交互。
    3. Runs-相关接口，包括创建、获取、删除、更新运行。用于对接前端页面的运行交互。

    '''
    app = FastAPI()
    router = APIRouter(prefix="/apiv2", tags=["agent"])
    
    def __init__(self, **kwargs):

        super(DrSaiAPP, self).__init__(**kwargs)

        self._init_router()
    
    def _init_router(self):

        # 测试路由
        DrSaiAPP.router.get("/")(self.index)

        # chat/completion路由
        DrSaiAPP.router.post("/chat/completions")(self.a_chat_completions)


    #### --- 关于DrSai的路由 --- ####
    async def index(self, request: Request):
        return f"Hello, world! This is DrSai WebUI {__version__}"
    
    ### --- 关于chat_completions的路由 --- ###
    async def a_chat_completions(self, request: Request):

        headers = request.headers
        if not isinstance(headers, dict):
            headers = dict(headers)
        authorization = headers.get("authorization", None)
        if authorization:
            apikey = authorization.split(" ")[-1]
        else:
            apikey = None

        # apikey = headers.get("authorization").split(" ")[-1]
        params = await request.json()
        params.update({"apikey": apikey})
        if "messages" not in params or "model" not in params:
            raise HTTPException(status_code=400, detail="messages and model must be required, see https://platform.openai.com/docs/api-reference/chat")
        # return self.try_except_raise_http_exception(
        #     self.a_start_chat_completions, **params
        #     )
        return await self.try_except_raise_http_exception(
            self.a_start_chat_completions, **params
            )

    ### --- 其它函数 --- #### 
    async def try_except_raise_http_exception(self, func, *args, **kwargs):  # 改为异步函数
        """智能捕获函数内部raise的异常，转换为HTTPException返回，支持同步/异步函数"""
        try:
            # 判断是否是异步函数
            if inspect.iscoroutinefunction(func):
                res = await func(*args, **kwargs)  # 异步函数需要await
            else:
                res = func(*args, **kwargs)  # 同步函数直接调用

            # 处理同步/异步生成器
            if isinstance(res, (AsyncGenerator, Generator)):  # 同时检查两种生成器
                return StreamingResponse(res)
            return res
    
        except Exception as e:
            tb_str = traceback.format_exception(*sys.exc_info())
            tb_str = "".join(tb_str)
            logger.debug(f"Error: {e}.\nTraceback: {tb_str}")

            e_class = e.__class__.__name__
            error_mapping = {
                "ModuleNotFoundError": 404,
                "NotImplementedError": 501,
                # 添加更多映射...
            }
            status_code = error_mapping.get(e_class, 400)
            raise HTTPException(
                status_code=status_code,
                detail=f'{e_class}("{str(e)}")'
            )
    # def try_except_raise_http_exception(self, func, *args, **kwargs):
    #     """智能捕获函数内部raise的异常，转换为HTTPException返回，便于前端处理"""
    #     try:
    #         res = func(*args, **kwargs)
    #         if isinstance(res, Generator):
    #             return StreamingResponse(res)
    #         return res
    #     except Exception as e:
    #         # 获取报错类型：e.__class__.__name__
    #         # if self.debug:
    #             # logger.error(f"Error: {e}")
    #         # tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
    #         tb_str = traceback.format_exception(*sys.exc_info())
    #         tb_str = "".join(tb_str)
    #         logger.debug(f"Error: {e}.\nTraceback: {tb_str}")

    #         e_class = e.__class__.__name__
    #         if e_class == "ModuleNotFoundError":
    #             raise HTTPException(status_code=404, detail=f'{e_class}("{str(e)}")')
    #         elif e_class == "NotImplementedError":
    #             raise HTTPException(status_code=501, detail=f'{e_class}("{str(e)}")')
    #         ## TODO: 其他报错类型转换为合适的报错状态码
    #         raise HTTPException(status_code=400, detail=f'{e_class}("{str(e)}")')