# -*- coding: utf-8 -*-
import json
from typing import List, Dict, Union, AsyncGenerator, Tuple, Any

# Model client
from hepai.agents import HepAIChatCompletionClient 

# backend thread 
from hepai.agents import Thread, ThreadsManager

# AutoGen imports
from autogen_core import CancellationToken, FunctionCall
from autogen_core.tools import BaseTool, FunctionTool, StaticWorkbench, Workbench, ToolResult, TextResultContent
from autogen_core.models import (
    LLMMessage,
    SystemMessage,
    AssistantMessage,
    UserMessage,
    ChatCompletionClient,
    CreateResult,
    FunctionExecutionResultMessage
)
from autogen_agentchat.base import Response
from autogen_agentchat.messages import (
    BaseAgentEvent,
    BaseChatMessage,
    ToolCallSummaryMessage,
    ModelClientStreamingChunkEvent,
    TextMessage,
    UserInputRequestedEvent,
    ThoughtEvent,
    HandoffMessage,
    AgentEvent,
    ChatMessage,
    MemoryQueryEvent,
    ToolCallExecutionEvent,
    ToolCallRequestEvent,
)

async def tools_reply_function( 
    oai_messages: List[str],  # OAI messages
    agent_name: str,  # Agent name
    llm_messages: List[LLMMessage],  # AutoGen LLM messages
    model_client: HepAIChatCompletionClient,  # AutoGen LLM Model client
    tools: Union[StaticWorkbench, Workbench],  # AutoGen Workbench
    cancellation_token: CancellationToken,  # AutoGen cancellation token,
    thread: Thread,  # DrSai thread
    thread_mgr: ThreadsManager,  # DrSai thread manager
    **kwargs) -> Union[str, AsyncGenerator[str, None]]:
    """
    自定义回复函数：能够智能地调用工具，然后通过工具的执行结果进行回复。
    """

    # 使用AutoGen Workbench获取工具信息
    tools_schema = []
    if isinstance(tools, StaticWorkbench):
        # tools: List[BaseTool[Any, Any]] = tools._tools
        tools_schema: List[Dict[str, Any]] = await tools.list_tools()
    
    # 进行工具执行
    model_result = None
    async for chunk in model_client.create_stream(
            messages=llm_messages,
            cancellation_token=cancellation_token,
            tools = tools_schema,
        ):
        if isinstance(chunk, CreateResult):
            model_result = chunk
        else:
            yield chunk
        
    # 进一步解析模型返回的结果
    if isinstance(model_result.content, list):
        function_calls: List[FunctionCall] = model_result.content
        function_call_contents: str = ""
        for function_call in function_calls:
            tool_result: ToolResult = await tools.call_tool(name=function_call.name, arguments=json.loads(function_call.arguments), cancellation_token=cancellation_token)
            name = tool_result.name
            content: str = "\n".join([str(i.content) for i  in tool_result.result])

            function_call_contents += f"{name}:\n{content}\n\n"

    
        prompt = f"""以下是对应工具的执行结果：
```
{function_call_contents}
```
请根据执行结果进一步回复上面用户的问题。
"""
        llm_messages.append(UserMessage(content=prompt, source="user"))
        async for chunk in model_client.create_stream(
            messages=llm_messages,
            cancellation_token=cancellation_token,
        ):
            yield chunk
    else:
        yield model_result


async def tools_recycle_reply_function( 
    oai_messages: List[str],  # OAI messages
    agent_name: str,  # Agent name
    llm_messages: List[LLMMessage],  # AutoGen LLM messages
    model_client: HepAIChatCompletionClient,  # AutoGen LLM Model client
    tools: Union[StaticWorkbench, Workbench],  # AutoGen Workbench
    cancellation_token: CancellationToken,  # AutoGen cancellation token,
    thread: Thread,  # DrSai thread
    thread_mgr: ThreadsManager,  # DrSai thread manager
    **kwargs) -> Union[str, AsyncGenerator[str, None]]:
    """
    自定义回复函数：能够智能地循环调用工具自有的工具集进行规划完成任务。
    """

    # 使用AutoGen Workbench获取工具信息
    tools_schema = []
    if isinstance(tools, StaticWorkbench):
        # tools: List[BaseTool[Any, Any]] = tools._tools
        tools_schema: List[Dict[str, Any]] = await tools.list_tools()
        tools_names = [i["name"] for i in tools_schema]

        # 将循环调用的提示词以UserMessage的形式放入
        llm_messages.append(UserMessage(content=f"""你需要回复我上面的任务，回复要求如下：
1. 如果不需要使用工具集：{tools_names}，或者工具集中的工具无法完成任务，则直接使用你的知识回复；
2. 如果我上面的任务适合使用工具集：{tools_names}，你需要根据每个工具的功能，进行任务和对应的使用工具规划，然后按照规划依次调用对应工具执行，在任务执行结束后进行总结，最后必须回复: 'TERMINATED'
""", 
source="user"))

        # 获取最大循环次数
        max_turns = kwargs.get("max_turns", 3)
        for i in range(max_turns):
            # 进行工具执行
            model_result = None
            async for chunk in model_client.create_stream(
                    messages=llm_messages,
                    cancellation_token=cancellation_token,
                    tools = tools_schema,
                ):
                if isinstance(chunk, CreateResult):
                    model_result = chunk
                else:
                    yield chunk
                
            # 进一步解析模型返回的结果
            if isinstance(model_result.content, list):
                function_calls: List[FunctionCall] = model_result.content
                function_call_contents: str = ""
                for function_call in function_calls:
                    tool_result: ToolResult = await tools.call_tool(name=function_call.name, arguments=json.loads(function_call.arguments), cancellation_token=cancellation_token)
                    name = tool_result.name
                    content: str = "\n".join([str(i.content) for i  in tool_result.result])
                    yield f"工具{name}的执行结果如下:\n"
                    yield "<think>\n"
                    yield f"{content}\n\n"
                    yield "</think>\n"
                    function_call_contents += f"工具{name}的执行结果如下:\n{content}\n\n"

                # 将执行结果以AssistMessage的形式放入
                llm_messages.append(AssistantMessage(content=function_call_contents+"如果需要继续使用工具集，请继续回复；如果不需要使用工具集，请进行总结，并回复'TERMINATE'。\n", source=agent_name))
                                                  
            # 循环调用结束，则结束对话
            elif 'TERMINATE' in model_result.content:
                yield model_result
                return
            else:
                yield model_result
                continue
    else:
        # 无工具集，则直接使用大模型进行回复
        async for chunk in model_client.create_stream(
                messages=llm_messages,
                cancellation_token=cancellation_token,
            ):
            yield chunk

