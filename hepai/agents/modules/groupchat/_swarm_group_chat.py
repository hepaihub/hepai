from autogen_agentchat.teams import Swarm
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage
from autogen_agentchat.base import ChatAgent, TerminationCondition
from autogen_core import AgentRuntime
from hepai.agents.modules.managers.base_thread import Thread
from hepai.agents.modules.managers.threads_manager import ThreadsManager
from typing import List, Dict, Any


class DrSaiSwarm(Swarm):

    def __init__(
        self,
        participants: List[ChatAgent],
        termination_condition: TerminationCondition | None = None,
        max_turns: int | None = None,
        runtime: AgentRuntime | None = None,
        custom_message_types: List[type[BaseAgentEvent | BaseChatMessage]] | None = None,
        emit_team_events: bool = False,
        thread: Thread = None,
        thread_mgr: ThreadsManager = None,
        **kwargs: Any
    ) -> None:
        super().__init__(
            participants=participants,
            termination_condition=termination_condition, 
            max_turns=max_turns,
            runtime=runtime,
            custom_message_types=custom_message_types,
            emit_team_events=emit_team_events,
        )

        self._theard: Thread = thread
        self._thread_mgr: ThreadsManager = thread_mgr