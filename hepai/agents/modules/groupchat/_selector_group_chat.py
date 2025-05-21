from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.teams._group_chat._selector_group_chat import SelectorFuncType, CandidateFuncType
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage
from autogen_agentchat.base import ChatAgent, TerminationCondition
from autogen_core.models  import ChatCompletionClient
from autogen_core import AgentRuntime
from hepai.agents import HepAIChatCompletionClient
from hepai.agents.modules.managers.base_thread import Thread
from hepai.agents.modules.managers.threads_manager import ThreadsManager

from typing import List, Optional, Any
import os

class DrSaiSelectorGroupChat(SelectorGroupChat):
    def __init__(
        self,
        participants: List[ChatAgent],
        *,
         model_client: ChatCompletionClient = None,
        termination_condition: TerminationCondition | None = None,
        max_turns: int | None = None,
        runtime: AgentRuntime | None = None,
        selector_prompt: str = """You are in a role play game. The following roles are available:
{roles}.
Read the following conversation. Then select the next role from {participants} to play. Only return the role.

{history}

Read the above conversation. Then select the next role from {participants} to play. Only return the role.
""",
        allow_repeated_speaker: bool = False,
        max_selector_attempts: int = 3,
        selector_func: Optional[SelectorFuncType] = None,
        candidate_func: Optional[CandidateFuncType] = None,
        custom_message_types: List[type[BaseAgentEvent | BaseChatMessage]] | None = None,
        emit_team_events: bool = False,
        model_client_streaming: bool = False,
        thread: Thread = None,
        thread_mgr: ThreadsManager = None,
        **kwargs: Any
    ):
        if not model_client:
            model_client = HepAIChatCompletionClient(model="openai/gpt-4o", api_key=os.environ.get("HEPAI_API_KEY"))
        super().__init__(
            participants=participants,
            model_client=model_client,
            termination_condition=termination_condition, 
            max_turns=max_turns,
            runtime=runtime,
            selector_prompt=selector_prompt,
            allow_repeated_speaker=allow_repeated_speaker,
            max_selector_attempts=max_selector_attempts,
            selector_func=selector_func,
            candidate_func=candidate_func,
            custom_message_types=custom_message_types,
            emit_team_events=emit_team_events,
            model_client_streaming=model_client_streaming,
        )

        self._theard: Thread = thread
        self._thread_mgr: ThreadsManager = thread_mgr

