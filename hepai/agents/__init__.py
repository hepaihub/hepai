from hepai.agents.dr_sai import DrSai

# Agent components
from hepai.agents.modules.components.LLMClient import HepAIChatCompletionClient

# Agents
from hepai.agents.modules.baseagent.drsaiagent import DrSaiAgent as AssistantAgent

# Groupchat
from hepai.agents.modules.groupchat._round_robin_group_chat import DrSaiRoundRobinGroupChat, DrSaiRoundRobinGroupChatManager
from hepai.agents.modules.groupchat._selector_group_chat import DrSaiSelectorGroupChat
from hepai.agents.modules.groupchat._swarm_group_chat import DrSaiSwarm
from hepai.agents.modules.groupchat._base_group_chat import DrSaiGroupChatManager, DrSaiGroupChat

# manager
from hepai.agents.modules.managers.base_thread import Thread
from hepai.agents.modules.managers.threads_manager import ThreadsManager
from hepai.agents.modules.managers.base_thread_message import ThreadMessage, Content, Text

# reply functions
from hepai.agents.modules.baseagent.toolagent import tools_reply_function, tools_recycle_reply_function

# # tools
# from hepai.agents.modules.components.tools.mcps_std import web_fetch

# utils
from hepai.agents.utils.message_convert import (
    llm_messages2oai_messages, 
    llm_messages2basechatmessages)

from hepai.agents.utils.oai_stream_event import (
    chatcompletionchunk, 
    chatcompletionchunkend, 
    chatcompletions)

# backend
from hepai.agents.backend.run import (
    Run_DrSaiAPP, 
    run_backend, 
    run_console, 
    run_hepai_worker,
    run_openwebui,
    run_pipelines,
    run_drsai_app)
from hepai.agents.backend.app_worker import DrSaiAPP

###########
# Autogen #
###########

# autogen_ext Models
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models  import (
    ChatCompletionClient,
    ModelCapabilities,  # type: ignore
    ModelFamily,
    ModelInfo,
    validate_model_info,
)

# autogen_agentchat Agents
from autogen_agentchat.agents import (
    UserProxyAgent, 
    BaseChatAgent,
    CodeExecutorAgent, 
    SocietyOfMindAgent)

# autogen_agentchat Groupchat
from autogen_agentchat.teams import (
    BaseGroupChat, 
    RoundRobinGroupChat, 
    Swarm,
    SelectorGroupChat, 
    MagenticOneGroupChat)

# autogen_agentchat Groupchat Termination Conditions
from autogen_agentchat.conditions import (
    ExternalTermination,
    HandoffTermination,
    MaxMessageTermination,
    SourceMatchTermination,
    StopMessageTermination,
    TextMentionTermination,
    TimeoutTermination,
    TokenUsageTermination,)

# autogen_agentchat UI
from autogen_agentchat.ui import Console, UserInputManager

# autogen_agentchat Messages
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionTokenLogprob,
    CreateResult,
    FinishReasons,
    FunctionExecutionResult,
    FunctionExecutionResultMessage,
    LLMMessage,
    RequestUsage,
    SystemMessage,
    TopLogprob,
    UserMessage,
)
from autogen_agentchat.base import Response
from autogen_agentchat.messages import (
    BaseAgentEvent,
    BaseChatMessage,
    ToolCallSummaryMessage,
    ModelClientStreamingChunkEvent,
    TextMessage,
    HandoffMessage,
)

# autogen_core Tools
from autogen_core.tools import (
    Tool, 
    ToolSchema, 
    ParametersSchema,
    BaseTool,
    BaseToolWithState,
    FunctionTool,
    StaticWorkbench,
    ImageResultContent, 
    TextResultContent, 
    ToolResult, 
    Workbench
    )

# autogen_ext mcp
from autogen_ext.tools.mcp import (
    McpServerParams, 
    SseServerParams, 
    StdioServerParams,
    StdioMcpToolAdapter,
    SseMcpToolAdapter,
    McpWorkbench,
    create_mcp_server_session,
    mcp_server_tools)

from autogen_core import Image as AGImage
from autogen_core import CancellationToken