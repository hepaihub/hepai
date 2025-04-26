from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.openai._openai_client import (
    convert_tools, 
    _add_usage,
    to_oai_type,
    create_kwargs
    )
from autogen_ext.models.openai.config import OpenAIClientConfiguration
from autogen_core.models import ModelFamily

from typing_extensions import Unpack
import os

import warnings
from typing import (
    Any,
    AsyncGenerator,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)

from autogen_core import (
    CancellationToken,
    FunctionCall,
    Image
)
from autogen_core.models import (
    ChatCompletionTokenLogprob,
    CreateResult,
    LLMMessage,
    ModelFamily,
    RequestUsage,
    TopLogprob,
    UserMessage
)
from autogen_core.tools import Tool, ToolSchema
from openai.types.chat import (
    ParsedChoice

)
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from pydantic import BaseModel

from autogen_ext.models._utils.normalize_stop_reason import normalize_stop_reason
from autogen_ext.models._utils.parse_r1_content import parse_r1_content

class HepAIChatCompletionClient(OpenAIChatCompletionClient):

    def __init__(self, **kwargs: Unpack[OpenAIClientConfiguration]):

        if "api_key" not in kwargs:
            kwargs["api_key"] = os.environ.get("HEPAI_API_KEY")
        if "base_url" not in kwargs:
            kwargs["base_url"] = "https://aiapi.ihep.ac.cn/apiv2"

        if "model_info" not in kwargs:
            model_info={
                "vision": False,
                "function_calling": False,  # You must sure that the model can handle function calling
                "json_output": False,
                "structured_output": False,
                "family": ModelFamily.UNKNOWN,
            }
            kwargs["model_info"] = model_info
        allowed_models = [
        "gpt-4o",
        "o1",
        "o3",
        "gpt-4",
        "gpt-35",
        "r1",
        "v3",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash",
        "claude-3-haiku",
        "claude-3-sonnet",
        "claude-3-opus",
        "claude-3.5-haiku",
        "claude-3.5-sonnet"]
        for allowed_model in allowed_models:
            model = kwargs.get("model", "")
            if allowed_model in model.lower():
                if allowed_model == "v3":
                    allowed_model = "gpt-4o"
                kwargs["model_info"]["family"] = allowed_model
                kwargs["model_info"]["function_calling"] = True
                kwargs["model_info"]["json_output"] = True,
                kwargs["model_info"]["structured_output"] = True
                break

        super().__init__(**kwargs)
    