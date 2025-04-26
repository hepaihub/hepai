
from typing import (
    List,
    Dict, 
    )

from autogen_core.models import (
    FunctionExecutionResultMessage,
    LLMMessage,
    UserMessage,
    AssistantMessage,
    SystemMessage,
)

from autogen_agentchat.messages import (
    # BaseAgentEvent,
    BaseChatMessage,
    ToolCallSummaryMessage,
    # ModelClientStreamingChunkEvent,
    TextMessage,
)

async def llm_messages2oai_messages(llm_messages: List[LLMMessage]) -> List[Dict[str, str]]:
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

async def llm_messages2basechatmessages(
    llm_messages: List[LLMMessage]
    ) -> List[BaseChatMessage]:
    basechatmessages = []
    for llm_message in llm_messages:
        if isinstance(llm_message, SystemMessage):
            continue
        if isinstance(llm_message, FunctionExecutionResultMessage):
            basechatmessages.append(ToolCallSummaryMessage(content=llm_message.content, source="assistant"))
        basechatmessages.append(TextMessage(content=llm_message.content, source=llm_message.source))
    
    return basechatmessages
