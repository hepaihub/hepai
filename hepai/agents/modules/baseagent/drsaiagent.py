from typing import (
    AsyncGenerator, List, Sequence, 
    Dict, Any, Callable, Awaitable, 
    Union, Optional, Tuple)

import asyncio
import logging
import inspect
import json
import os

from pydantic import BaseModel

from autogen_core import CancellationToken, FunctionCall
from autogen_core.tools import BaseTool, FunctionTool, StaticWorkbench, Workbench, ToolResult, TextResultContent
from autogen_core.memory import Memory
from autogen_core.model_context import ChatCompletionContext
from autogen_core.models import (
    ChatCompletionClient,
    CreateResult,
    FunctionExecutionResultMessage,
    FunctionExecutionResult,
    LLMMessage,
    UserMessage,
    AssistantMessage,
    SystemMessage,
    RequestUsage,
)
from autogen_core import EVENT_LOGGER_NAME
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Handoff as HandoffBase
from autogen_agentchat.base import Response
from autogen_agentchat.messages import (
    AgentEvent,
    ChatMessage,
    HandoffMessage,
    MemoryQueryEvent,
    ModelClientStreamingChunkEvent,
    TextMessage,
    ToolCallExecutionEvent,
    ToolCallRequestEvent,
    ToolCallSummaryMessage,
    UserInputRequestedEvent,
    ThoughtEvent
)

from hepai.agents import HepAIChatCompletionClient
from hepai.agents.modules.managers.base_thread import Thread
from hepai.agents.modules.managers.threads_manager import ThreadsManager
from hepai.agents.modules.managers.base_thread_message import ThreadMessage, Content, Text

event_logger = logging.getLogger(EVENT_LOGGER_NAME)


class TextContent(BaseModel):
    type: str
    text: str

class DrSaiAgent(AssistantAgent):
    """基于aotogen AssistantAgent的定制Agent"""
    def __init__(
        self,
        name: str,
        *,
        model_client: ChatCompletionClient = None,
        tools: List[BaseTool[Any, Any] | Callable[..., Any] | Callable[..., Awaitable[Any]]] | None = None,
        workbench: Workbench | None = None,
        handoffs: List[HandoffBase | str] | None = None,
        model_context: ChatCompletionContext | None = None,
        description: str = "An agent that provides assistance with ability to use tools.",
        system_message: (
            str | None
        ) = "You are a helpful AI assistant. Solve tasks using your tools. Reply with TERMINATE when the task has been completed.",
        model_client_stream: bool = True,
        reflect_on_tool_use: bool | None = None,
        tool_call_summary_format: str = "{result}",
        output_content_type: type[BaseModel] | None = None,
        output_content_type_format: str | None = None,
        memory: Sequence[Memory] | None = None,
        metadata: Dict[str, str] | None = None,
        memory_function: Callable = None,
        reply_function: Callable = None,
        thread: Thread = None,
        thread_mgr: ThreadsManager = None,
        **kwargs,
            ):
        '''
        memory_function: 自定义的memory_function，用于RAG检索等功能，为大模型回复增加最新的知识
        reply_function: 自定义的reply_function，用于自定义对话回复的定制
        '''
        if not model_client:
            model_client = HepAIChatCompletionClient(model="openai/gpt-4o", api_key=os.environ.get("HEPAI_API_KEY"))
        
        super().__init__(
            name, 
            model_client,
            tools=tools,
            workbench=workbench,
            handoffs=handoffs,
            model_context=model_context,
            description=description,
            system_message=system_message,
            model_client_stream=model_client_stream,
            reflect_on_tool_use=reflect_on_tool_use,
            tool_call_summary_format=tool_call_summary_format,
            output_content_type=output_content_type,
            output_content_type_format=output_content_type_format,
            memory=memory,
            metadata=metadata
            )
        
        self._reply_function: Callable = reply_function
        self._memory_function: Callable = memory_function
        self._thread: Thread = thread
        self._thread_mgr: ThreadsManager = thread_mgr
        self._user_params: Dict[str, Any] = {}
        self._user_params.update(kwargs)

    async def llm_messages2oai_messages(self, llm_messages: List[LLMMessage]) -> List[Dict[str, str]]:
        """Convert a list of LLM messages to a list of OAI chat messages."""
        messages = []
        for llm_message in llm_messages:
            if isinstance(llm_message, SystemMessage):
                messages.append({"role": "system", "content": llm_message.content} )
            if isinstance(llm_message, UserMessage):
                messages.append({"role": "user", "content": llm_message.content, "name": llm_message.source})
            if isinstance(llm_message, AssistantMessage):
                messages.append({"role": "assistant", "content": llm_message.content, "name": llm_message.source})
            if isinstance(llm_message, FunctionExecutionResultMessage):
                messages.append({"role": "function", "content": llm_message.content})
        return messages
    
    async def oai_messages2llm_messages(self, oai_messages: List[Dict[str, str]]) -> List[LLMMessage]:
        """Convert a list of OAI chat messages to a list of LLM messages."""
        messages = []
        for oai_message in oai_messages:
            if oai_message["role"] == "system":
                messages.append(SystemMessage(content=oai_message["content"]))
            if oai_message["role"] == "user":
                messages.append(UserMessage(content=oai_message["content"], source=oai_message.get("name", self.name)))
            if oai_message["role"] == "assistant":
                messages.append(AssistantMessage(content=oai_message["content"], source=oai_message.get("name", self.name)))
            if oai_message["role"] == "function":
                messages.append(FunctionExecutionResultMessage(content=oai_message["content"]))
        return messages
    
    async def _call_memory_function(self, llm_messages: List[LLMMessage]):
        """使用自定义的memory_function，为大模型回复增加最新的知识"""
        # memory_function: 自定义的memory_function，用于RAG检索等功能，为大模型回复增加最新的知识
        memory_messages = await self.llm_messages2oai_messages(llm_messages)
        try:
            memory_messages_with_new_knowledge: List[Dict[str, str]] = await self._memory_function(memory_messages, **self._user_params)
            llm_messages = await self.oai_messages2llm_messages(memory_messages_with_new_knowledge)
            return llm_messages
        except Exception as e:
            raise ValueError(f"Error: memory_function: {self._memory_function.__name__} failed with error {e}.")
    
    async def _call_reply_function(
            self, 
            llm_messages: List[LLMMessage],
            model_client: ChatCompletionClient,
            tools: Workbench,
            agent_name: str,
            cancellation_token: CancellationToken,
            thread: Thread = None,
            thread_mgr: ThreadsManager = None,
            **kwargs,
            ):
        """使用自定义的reply_function，自定义对话回复的定制"""

        oai_messages = await self.llm_messages2oai_messages(llm_messages)

        model_result: Optional[CreateResult] = None
        allowed_events = [
            ToolCallRequestEvent,
            ToolCallExecutionEvent,
            MemoryQueryEvent,
            UserInputRequestedEvent,
            ModelClientStreamingChunkEvent,
            ThoughtEvent]
        
        if self._model_client_stream:
            # 如果reply_function不是返回一个异步生成器而使用了流式模式，则会报错
            if not inspect.isasyncgenfunction(self._reply_function):
                raise ValueError("reply_function must be AsyncGenerator function if model_client_stream is True.")
            # Stream the reply_function.
            response = ""
            async for chunk in self._reply_function(
                oai_messages, 
                agent_name = agent_name,
                llm_messages = llm_messages, 
                model_client=model_client, 
                tools=tools, 
                cancellation_token=cancellation_token, 
                thread=thread, 
                thread_mgr=thread_mgr, 
                **self._user_params
                ):
                if isinstance(chunk, str):
                    response += chunk
                    yield ModelClientStreamingChunkEvent(content=chunk, source=agent_name)
                elif any(isinstance(chunk, event_type) for event_type in allowed_events):
                    response += str(chunk.content)
                    yield chunk
                elif isinstance(chunk, CreateResult):
                    model_result = chunk
                else:
                    raise RuntimeError(f"Invalid chunk type: {type(chunk)}")
            if isinstance(model_result, CreateResult):
                pass
            elif model_result is None:
            #     if isinstance(chunk, str):
            #         yield ModelClientStreamingChunkEvent(content=chunk, source=agent_name)
            #         response += chunk
            #     elif isinstance(chunk, AgentEvent):
            #         yield chunk
            #     elif isinstance(chunk, BaseAgentEvent):
            #     else:
            #         raise RuntimeError(f"Invalid chunk type: {type(chunk)}")
                assert isinstance(response, str)
                model_result = CreateResult(
                    content=response, finish_reason="stop",
                    usage = RequestUsage(prompt_tokens=0, completion_tokens=0),
                    cached=False)
        else:
            # 如果reply_function不是异步函数，或者是一个异步生成器，则会报错
            if not asyncio.iscoroutinefunction(self._reply_function) and not inspect.isasyncgenfunction(self._reply_function):
                raise ValueError("reply_function must be a coroutine function if model_client_stream is False.")
            response = await self._reply_function(
                oai_messages, 
                agent_name = agent_name,
                llm_messages = llm_messages, 
                tools=tools, 
                cancellation_token=cancellation_token, 
                **self._user_params
                )
            if isinstance(response, str):
                model_result = CreateResult(
                    content=response, finish_reason="stop",
                    usage = RequestUsage(prompt_tokens=0, completion_tokens=0),
                    cached=False)
            elif isinstance(response, CreateResult):
                model_result = response
            else:
                raise RuntimeError(f"Invalid response type: {type(response)}")
        yield model_result

    @classmethod
    async def call_llm(
        cls,
        agent_name: str,
        model_client: ChatCompletionClient,
        llm_messages: List[LLMMessage], 
        tools: List[BaseTool[Any, Any]], 
        model_client_stream: bool,
        cancellation_token: CancellationToken,
        output_content_type: type[BaseModel] | None,
        ) -> AsyncGenerator:
    
        model_result: Optional[CreateResult] = None

        if model_client_stream:
                
            async for chunk in model_client.create_stream(
                llm_messages, 
                tools=tools,
                json_output=output_content_type,
                cancellation_token=cancellation_token
            ):
                if isinstance(chunk, CreateResult):
                    model_result = chunk
                elif isinstance(chunk, str):
                    yield ModelClientStreamingChunkEvent(content=chunk, source=agent_name)
                else:
                    raise RuntimeError(f"Invalid chunk type: {type(chunk)}")
            if model_result is None:
                raise RuntimeError("No final model result in streaming mode.")
            yield model_result
        else:
            model_result = await model_client.create(
                llm_messages, tools=tools, cancellation_token=cancellation_token
            )
            yield model_result


### autogen 更改源码区

    async def _call_llm(
        self,
        model_client: ChatCompletionClient,
        model_client_stream: bool,
        system_messages: List[SystemMessage],
        model_context: ChatCompletionContext,
        workbench: Workbench,
        handoff_tools: List[BaseTool[Any, Any]],
        agent_name: str,
        cancellation_token: CancellationToken,
        output_content_type: type[BaseModel] | None,
    ) -> AsyncGenerator[Union[CreateResult, ModelClientStreamingChunkEvent], None]:
        """
        Perform a model inference and yield either streaming chunk events or the final CreateResult.
        """
        all_messages = await model_context.get_messages()
        if self._thread is None:
            pass
        else:
            # 从thread中获取历史消息，并于autogen中的消息记录合并
            history_aoi_messages: List[Dict[str, str]] = self._thread.metadata["history_aoi_messages"]
            history = []
            for  history_aoi_message in history_aoi_messages:
                if  history_aoi_message["role"] == "user":
                    history.append(UserMessage(content=history_aoi_message["content"], source=history_aoi_message["name"]))
                elif history_aoi_message["role"] == "assistant":
                    history.append(UserMessage(content=history_aoi_message["content"], source=history_aoi_message["name"]))
                elif history_aoi_message["role"] == "system":
                    history.append(SystemMessage(content=history_aoi_message["content"]))
                elif history_aoi_message["role"] == "function":
                    history.append(FunctionExecutionResultMessage(content=history_aoi_message["content"]))
            all_messages = history + all_messages
        
        llm_messages: List[LLMMessage] = self._get_compatible_context(model_client=model_client, messages=system_messages + all_messages)

        # 自定义的memory_function，用于RAG检索等功能，为大模型回复增加最新的知识
        if self._memory_function is not None:
            llm_messages = await self._call_memory_function(llm_messages)

        tools = (await workbench.list_tools()) + handoff_tools
        all_tools = tools + handoff_tools
        # model_result: Optional[CreateResult] = None
        if self._reply_function is not None:
            # 自定义的reply_function，用于自定义对话回复的定制
            async for chunk in self._call_reply_function(
                llm_messages, 
                model_client = model_client, 
                tools=workbench, 
                agent_name=agent_name, 
                cancellation_token=cancellation_token,
                thread = self._thread,
                thread_mgr = self._thread_mgr,
            ):
                # if isinstance(chunk, CreateResult):
                #     model_result = chunk
                yield chunk
        else:
           async for chunk in self.call_llm(
                agent_name = agent_name,
                model_client = model_client,
                llm_messages = llm_messages, 
                tools = all_tools, 
                model_client_stream = model_client_stream,
                cancellation_token = cancellation_token,
                output_content_type = output_content_type,
           ):
            #    if isinstance(chunk, CreateResult):
            #         model_result = chunk
               yield chunk