
import asyncio
import logging

from typing import Any, AsyncGenerator, List, Sequence, Callable

from autogen_core import (
    AgentId,
    CancellationToken,
    SingleThreadedAgentRuntime,
    AgentRuntime
)

from autogen_agentchat.base import ChatAgent, TaskResult, TerminationCondition
from autogen_agentchat.messages import (
    BaseAgentEvent, 
    AgentEvent, 
    BaseChatMessage, 
    ChatMessage, 
    MessageFactory,
    ModelClientStreamingChunkEvent, 
    StopMessage,
    TextMessage)
from autogen_agentchat.teams._group_chat._events import (
    GroupChatStart, 
    GroupChatTermination,
    SerializableException,
    )
from autogen_agentchat.teams._group_chat._sequential_routed_agent import SequentialRoutedAgent
from autogen_agentchat.teams._group_chat._base_group_chat_manager import BaseGroupChatManager
from autogen_agentchat.teams import BaseGroupChat

from hepai.agents.modules.managers.base_thread import Thread
from hepai.agents.modules.managers.threads_manager import ThreadsManager
from hepai.agents.modules.managers.base_thread_message import ThreadMessage, Content, Text

event_logger = logging.getLogger(__name__)



class DrSaiGroupChatManager(BaseGroupChatManager):

    def __init__(
        self,
        name: str,
        group_topic_type: str,
        output_topic_type: str,
        participant_topic_types: List[str],
        participant_names: List[str],
        participant_descriptions: List[str],
        output_message_queue: asyncio.Queue[BaseAgentEvent | BaseChatMessage | GroupChatTermination],
        termination_condition: TerminationCondition | None,
        max_turns: int | None,
        message_factory: MessageFactory,
        emit_team_events: bool = False,
        thread: Thread = None,
        thread_mgr: ThreadsManager = None,
        **kwargs: Any
    ):
        
        super().__init__(
            name=name,
            group_topic_type=group_topic_type,
            output_topic_type=output_topic_type,
            participant_topic_types=participant_topic_types,
            participant_names=participant_names,
            participant_descriptions=participant_descriptions,
            output_message_queue=output_message_queue,
            termination_condition=termination_condition,
            max_turns=max_turns,
            message_factory=message_factory,
            emit_team_events=emit_team_events,
        )
        self._theard: Thread = thread
        self._thread_mgr: ThreadsManager = thread_mgr



class DrSaiGroupChat(BaseGroupChat):

    component_type = "team"

    def __init__(
        self,
        participants: List[ChatAgent],
        group_chat_manager_name: str,
        group_chat_manager_class: type[SequentialRoutedAgent],
        termination_condition: TerminationCondition | None = None,
        max_turns: int | None = None,
        runtime: AgentRuntime | None = None,
        custom_message_types: List[type[BaseAgentEvent | BaseChatMessage]] | None = None,
        emit_team_events: bool = False,
        thread: Thread = None,
        thread_mgr: ThreadsManager = None,
        **kwargs: Any
    ):
        super().__init__(
            participants=participants,
            group_chat_manager_name=group_chat_manager_name,
            group_chat_manager_class=group_chat_manager_class,
            termination_condition=termination_condition,
            max_turns=max_turns,
            runtime=runtime,
            custom_message_types=custom_message_types,
            emit_team_events=emit_team_events,
            )
        self._thread: Thread = thread
        self._thread_mgr: ThreadsManager = thread_mgr

    def _create_group_chat_manager_factory(
       self,
        name: str,
        group_topic_type: str,
        output_topic_type: str,
        participant_topic_types: List[str],
        participant_names: List[str],
        participant_descriptions: List[str],
        output_message_queue: asyncio.Queue[BaseAgentEvent | BaseChatMessage | GroupChatTermination],
        termination_condition: TerminationCondition | None,
        max_turns: int | None,
        message_factory: MessageFactory,
        **kwargs: Any
    ) -> Callable[[], DrSaiGroupChatManager]:
        def _factory() -> DrSaiGroupChatManager:
            return DrSaiGroupChatManager(
                name = name,
                group_topic_type = group_topic_type,
                output_topic_type = output_topic_type,
                participant_topic_types = participant_topic_types,
                participant_names = participant_names,
                participant_descriptions = participant_descriptions,
                output_message_queue = output_message_queue,
                termination_condition = termination_condition,
                max_turns = max_turns,
                message_factory = message_factory,
                thread = self._thread,
                thread_mgr = self._thread_mgr,
                **kwargs, 
            )

        return _factory
    