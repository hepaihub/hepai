
from typing import List, Dict, Union, AsyncGenerator, Type, Generator
import copy, json, asyncio
import time
from hepai.agents.modules.managers.threads_manager import ThreadsManager
THREADS_MGR = ThreadsManager()
from hepai.agents.modules.managers.base_thread import Thread

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent, BaseChatAgent
from autogen_agentchat.base import Response, TaskResult
from autogen_core import FunctionCall, CancellationToken
from autogen_agentchat.messages import (
    AgentEvent,
    ChatMessage,
    TextMessage,
    ToolCallSummaryMessage,
    ToolCallRequestEvent,
    ToolCallExecutionEvent,
    ModelClientStreamingChunkEvent,
    MultiModalMessage,
    UserInputRequestedEvent,
)
from autogen_agentchat.teams import BaseGroupChat
from autogen_agentchat.ui import Console
import time

from hepai.agents.modules.managers.threads_manager import ThreadsManager
from hepai.agents.modules.managers.base_thread_message import ThreadMessage, Content, Text

from hepai.agents.utils import Logger
logger = Logger.get_logger("dr_sai.py")

import logging
# 单个模型日志
third_party_logger1 = logging.getLogger("autogen_core")
third_party_logger1.propagate = False
third_party_logger2 = logging.getLogger("autogen_agentchat.events")
third_party_logger2.propagate = False
third_party_logger3 = logging.getLogger("httpx")
third_party_logger3.propagate = False


from hepai.agents.utils.async_process import sync_wrapper
from hepai.agents.utils.oai_stream_event import (
    chatcompletionchunk, 
    chatcompletionchunkend,
    chatcompletions,
    split_string)

class DrSai:
    """
    This is the main class of OpenDrSai, in
    """
    def __init__(self, **kwargs):
        self.username = "anonymous"
        self.threads_mgr = THREADS_MGR
        self.agent_factory: callable = kwargs.pop('agent_factory', None)
        self.history_mode = kwargs.pop('history_mode', 'backend') # backend or frontend

    #### --- 关于AutoGen --- ####
    async def start_console(
            self,
            task: str,
            agent: AssistantAgent|BaseGroupChat = None, 
            **kwargs) -> Union[None, TaskResult]:
        """
        启动aotugen原生多智能体运行方式和多智能体逻辑
        """

        # agent: AssistantAgent|BaseGroupChat = self.agent_factory() if agent is None else agent
        agent: AssistantAgent | BaseGroupChat = (
            await self.agent_factory() 
            if agent is None and asyncio.iscoroutinefunction(self.agent_factory)
            else (
                self.agent_factory() 
                if agent is None 
                else agent
            )
        )

        stream = agent._model_client_stream if not isinstance(agent, BaseGroupChat) else agent._participants[0]._model_client_stream
        if stream:
            await Console(agent.run_stream(task=task))
            return 
        else:
            result:TaskResult = await agent.run(task=task)
            print(result)
            # return result
    
    #### --- 关于OpenAI Chat/Completions --- ####
    async def a_start_chat_completions(
            self, 
            **kwargs) -> AsyncGenerator:
        """
        启动聊天任务，使用completions后端模式
        加载默认的Agents, 并启动聊天任务, 这里默认使用GroupChat
        params:
        stream: bool, 是否使用流式模式
        messages: List[Dict[str, str]], 传入的消息列表
        HEPAI_API_KEY: str, 访问hepai的api_key
        usr_info: Dict, 用户信息
        base_models: Union[str, List[str]], 智能体基座模型
        chat_mode: str, 聊天模式，默认once
        **kwargs: 其他参数
        """
        
        # 从函数工厂中获取定义的Agents
        # agent: AssistantAgent|BaseGroupChat = self.agent_factory()
        agent: AssistantAgent | BaseGroupChat = (
            await self.agent_factory() 
            if asyncio.iscoroutinefunction(self.agent_factory)
            else (self.agent_factory())
        )

        # 是否使用流式模式
        agent_stream = agent._model_client_stream if not isinstance(agent, BaseGroupChat) else agent._participants[0]._model_client_stream
        stream = kwargs.pop('stream', agent_stream)
        if isinstance(agent, BaseGroupChat) and stream:
            for participant in agent._participants:
                if not participant._model_client_stream:
                    raise ValueError("Streaming mode is not supported when participant._model_client_stream is False")
        
        # 传入的消息列表
        messages: List[Dict[str, str]] = kwargs.pop('messages', [])
        usermessage = messages[-1]["content"]

        # 保存用户的extra_requests
        extra_requests: Dict = copy.deepcopy(kwargs)

        # 大模型配置
        api_key = kwargs.pop('api_key', None)
        temperature = kwargs.pop('temperature', 0.6)
        top_p = kwargs.pop('top_p', 1)
        cache_seed = kwargs.pop('cache_seed', None)
        # 额外的请求参数
        extra_body: Union[Dict, None] = kwargs.pop('extra_body', None)
        if extra_body is not None:
            ## 用户信息 从DDF2传入的
            user_info: Dict = kwargs.pop('extra_body', {}).get("user", {})
            self.username = user_info.get('email', None) or user_info.get('name', "anonymous")
            chat_id = extra_body.get("chat_id", None) # 获取前端聊天界面的session_id
        else:
            #  {'model': 'drsai_pipeline', 'user': {'name': '888', 'id': '888', 'email': 888', 'role': 'admin'}, 'metadata': {}, 'base_models': 'openai/gpt-4o', 'apikey': 'sk-88'}
             user_info = kwargs.pop('user', {})
             self.username = user_info.get('email', None) or user_info.get('name', "anonymous")
             chat_id = kwargs.pop('chat_id', None) # 获取前端聊天端口的session_id
             history_mode = kwargs.pop('history_mode', None) or self.history_mode # backend or frontend
                
        # 使用thread加载后端的聊天记录
        # TODO: 这里需要改成异步加载
        thread: Thread = self.threads_mgr.create_threads(username=self.username, dialog_id=chat_id)
        thread.metadata["extra_requests"] = extra_requests
        agent._thread = thread
        agent._thread_mgr = self.threads_mgr
        # 如果前端没有给定dialog_id，则将当前历史消息记录加入到新的thread中/或者使用前端历史消息
        if not chat_id or history_mode == "frontend":
            thread.messages = [] # 清空历史消息
            for message in messages[:-1]:
                thread_content = [Content(type="text", text=Text(value=message["content"],annotations=[]))]
                self.threads_mgr.create_message(
                    thread=thread,
                    role = message["role"],
                    content=thread_content,
                    sender=message["role"],
                    metadata={},
                    )
                
        # 将历史消息单独保存到metadata中
        history_aoi_messages = [ {"role": x.role, "content": x.content_str(), "name": x.sender} for x in thread.messages] # 不将usermessage加入到历史消息中，在智能体会重复发送
        thread.metadata["history_aoi_messages"] = history_aoi_messages

        # 由于groupchat中不能将历史消息传入队列中，因为必须由每个Agent来处理历史消息
        if isinstance(agent, BaseGroupChat):
            for participant in agent._participants:
                participant._thread = thread
                participant._thread_mgr = self.threads_mgr

        # 启动聊天任务
        res = agent.run_stream(task=usermessage)
        tool_flag = 0
        role = ""
        async for message in res:
            
            # print(message)
            oai_chunk = copy.deepcopy(chatcompletionchunk)
            # The Unix timestamp (in seconds) of when the chat completion was created
            oai_chunk["created"] = int(time.time())
            if isinstance(message, ModelClientStreamingChunkEvent):
                if stream and isinstance(agent, BaseChatAgent):
                    content = message.content
                    oai_chunk["choices"][0]["delta"]['content'] = content
                    oai_chunk["choices"][0]["delta"]['role'] = 'assistant'
                    yield f'data: {json.dumps(oai_chunk)}\n\n'
                elif stream and isinstance(agent, BaseGroupChat):
                    role_tmp = message.source
                    if role != role_tmp:
                        role = role_tmp
                        # oai_chunk["choices"][0]["delta"]['content'] = f"\n\n**Speaker: {role}**\n\n"
                        if role:
                            oai_chunk["choices"][0]["delta"]['content'] = f"\n\n**{role}发言：**\n\n"
                        oai_chunk["choices"][0]["delta"]['role'] = 'assistant'
                        yield f'data: {json.dumps(oai_chunk)}\n\n'
                    
                    content = message.content
                    oai_chunk["choices"][0]["delta"]['content'] = content
                    oai_chunk["choices"][0]["delta"]['role'] = 'assistant'
                    yield f'data: {json.dumps(oai_chunk)}\n\n'
                    
                else:
                    if stream:
                        raise ValueError("No valid agent type for chat completions")
                    else:
                        pass
            elif isinstance(message, TaskResult):
                if stream:
                    # 最后一个chunk
                    chatcompletionchunkend["created"] = int(time.time())
                    yield f'data: {json.dumps(chatcompletionchunkend)}\n\n'
            elif isinstance(message, TextMessage):
                # 将智能体回复加入thread.messages中
                self.threads_mgr.create_message(
                    thread=thread,
                    role = "assistant",
                    content=[Content(type="text", text=Text(value=message.content,annotations=[]))],
                    sender=message.source,
                    metadata={},
                    )
                chatcompletions["choices"][0]["message"]["created"] = int(time.time())
                if (not stream) and isinstance(agent, BaseChatAgent):
                    if message.source!="user":
                        content = message.content
                        chatcompletions["choices"][0]["message"]["content"] = content
                        yield f'data: {json.dumps(chatcompletions)}\n\n'
                elif (not stream) and isinstance(agent, BaseGroupChat):
                    if message.source!="user":
                        content = message.content
                        source = message.source
                        content = f"\n\nSpeaker: {source}\n\n{content}\n\n"
                        chatcompletions["choices"][0]["message"]["content"] = content
                        yield f'data: {json.dumps(chatcompletions)}\n\n'
                else:
                    if (not stream):
                        raise ValueError("No valid agent type for chat completions")
                    else:
                        pass
            elif isinstance(message, ToolCallRequestEvent):
                tool_flag = 1
                tool_content: List[FunctionCall]=message.content
                tool_calls = []
                for tool in tool_content:
                    tool_calls.append(
                        {"id": tool.id, "type": "function","function": {"name": tool.name,"arguments": tool.arguments}}
                         )
                if stream:
                    oai_chunk["choices"][0]["delta"]['tool_calls'] = tool_calls
                    oai_chunk["choices"][0]["delta"]['role'] = 'assistant'
                    yield f'data: {json.dumps(oai_chunk)}\n\n'
                else:
                    chatcompletions["choices"][0]["message"]["tool_calls"] = tool_calls
            elif isinstance(message, ToolCallExecutionEvent):
                tool_flag = 2
            elif isinstance(message, ToolCallSummaryMessage):
                # 将智能体的ToolCallSummaryMessage回复加入thread.messages中
                self.threads_mgr.create_message(
                    thread=thread,
                    role = "assistant",
                    content=[Content(type="text", text=Text(value=message.content,annotations=[]))],
                    sender=message.source,
                    metadata={},
                    )
                if tool_flag == 2:
                    if not stream:
                        content = message.content
                        chatcompletions["choices"][0]["message"]["content"] = content
                        yield f'data: {json.dumps(chatcompletions)}\n\n'
                    else:
                        oai_chunk["choices"][0]["delta"]['content'] = message.content
                        oai_chunk["choices"][0]["delta"]['role'] = 'assistant'
                        yield f'data: {json.dumps(oai_chunk)}\n\n'
                    tool_flag = 0
            # elif isinstance(message, Response):
            #     # print("Response: " + str(message))
            # elif isinstance(message, UserInputRequestedEvent):
            #     print("UserInputRequestedEvent:" + str(message))
            # elif isinstance(message, MultiModalMessage):
            #     print("MultiModalMessage:" + str(message))
            # elif isinstance(message, ThoughtEvent):
            #     print("ThoughtEvent:" + str(message))
            else:
                # print("Unknown message:" + str(message))
                # print(f"Unknown message, type: {type(message)}")
                pass


        