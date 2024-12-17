"""
基于OAI的SyncAPI的Client
"""

import os
import json
from typing import Mapping, Generator, Dict
from typing_extensions import override
import httpx
import warnings


from .openai_api import *

from .resources._resource import SyncAPIResource

# from . import resources
from dataclasses import dataclass, field, asdict

class DemoResoure(SyncAPIResource):
    """
    This is a demo resource for demostrating how to use SyncAPIResource
    
    Usage:
        ```python
        class MyClient(HClient):
            
            def __init__(self):
                super().__init__()
                self.demo_resource: SyncAPIResource = DemoResoure()
        ```

        ```python
        client = MyClient()
        client.demo_resource.get_index()
        ```
    """
    def get_index(self):
        return self._get(
            "/",
            cast_to=Any,
        )
    
    def post_index(self, data):
        return self._post(
            "/",
            cast_to=Any,
            body=data,
        )
    

def get_defualt_timeout(timeout: float = 600.0, connect: float = 5.0) -> httpx.Timeout:
    return httpx.Timeout(timeout=timeout, connect=connect)


# DEFAULT_BASE_URL = os.environ.get("HEPAI_BASE_URL", None)
# DEFAULT_API_KEY = os.environ.get("HEPAI_API_KEY", None)

@dataclass
class HClientConfig:
    base_url: str = field(default=NOT_GIVEN, metadata={"description": "The default base URL for all requests"})
    api_key: str = field(default=NOT_GIVEN, metadata={"description": "The default API key for all requests"})
    max_retries: int = field(default=0, metadata={"description": "The default maximum number of retries for all requests"})
    timeout: None | httpx.Timeout = field(default_factory=get_defualt_timeout, metadata={"description": "The default timeout for all requests"})
    http_client: None | httpx.Client  = field(default=None, metadata={"description": "The default HTTP client for all requests"})
    default_headers: Mapping[str, str] = field(default=None, metadata={"description": "The default headers for all requests"})
    default_query: Mapping[str, object] = field(default=None, metadata={"description": "The default query parameters for all requests"})
    version: str = field(default="2.0.0", metadata={"description": "The version of the client"})
    enable_openai: bool = field(default=True, metadata={"description": "Whether to enable openai resources"})
    _strict_response_validation: bool = field(default=False, metadata={"description": "Whether to strictly validate responses"})
    
    def to_dict(self):
        return asdict(self)
    
    def update_by_dict(self, d: dict):
        unkown_keys = []
        for k, v in d.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                unkown_keys.append(k)
        if unkown_keys:
            warnings.warn(f"[HClientConfig] encountered {len(unkown_keys) }unknown keys when updating config, this keys will be ignored: {unkown_keys}")
        return self
    
    
class HClient(SyncAPIClient):
    """
    高能AI框架基础客户端
    """
    NotGiven = NOT_GIVEN

    def __init__(
            self,
            config: HClientConfig = None,
            **overrides, # 用于覆盖默认配置
    ):
        self.config = config or HClientConfig()
        if overrides:
            self.config.update_by_dict(overrides)
        
        api_key = self.config.api_key
        if api_key == NOT_GIVEN:  # 人为设置为NOT_GIVEN时，不报错
            pass
        elif api_key is None:
            raise ValueError(
                "The api_key client option must be set either by passing api_key to the client or by setting the environment variable"
            )
        self.api_key = api_key


        if self.config.base_url == NOT_GIVEN:
            self.config.base_url = httpx.URL("")
            pass
        elif self.config.base_url is None:
            raise ValueError(
                "The base_url client option must be set, you can set it by passing base_url to the client or by setting the environment variable"
            )

        super().__init__(
            version=self.config.version,
            base_url=self.config.base_url,
            max_retries=self.config.max_retries,
            timeout=self.config.timeout,
            http_client=self.config.http_client,
            custom_headers=self.config.default_headers,
            custom_query=self.config.default_query,
            _strict_response_validation=self.config._strict_response_validation,
        )

        if self.config.enable_openai:
            """集成openai的resources"""
            # from openai import OpenAI
            # from openai import resources
            # from openai._client import OpenAIWithRawResponse, OpenAIWithStreamedResponse
            from .openai_api import resources
            # self._default_stream_cls = HClient.Stream
            self.completions = resources.Completions(self)
            self.chat = resources.Chat(self)
            self.embeddings = resources.Embeddings(self)
            self.files = resources.Files(self)
            self.images = resources.Images(self)
            self.audio = resources.Audio(self)
            self.moderations = resources.Moderations(self)
            self.models = resources.Models(self)
            self.fine_tuning = resources.FineTuning(self)
            self.beta = resources.Beta(self)
            self.batches = resources.Batches(self)
            self.uploads = resources.Uploads(self)
            # self.with_raw_response = OpenAIWithRawResponse(self)
            # self.with_streaming_response = OpenAIWithStreamedResponse(self)

    
    
    @property
    def Stream(self):
        return Stream
    
    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="brackets")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        if api_key is None:
            return {}
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }
    
    def stream_to_generator(self, stream_obj: Stream) -> Generator:
        """make a stream object to a generator that fit to client stream decoder"""
        for x in stream_obj:
            # print(x)
            yield f"data: {json.dumps(x)}\n\n"

    def _make_status_error(self, err_msg: str, *, body: object, response: httpx.Response) -> APIStatusError:
        """
        Make an APIStatusError from an error message, response body, and response object.
        For example: 
            err_msg: str, "Error code: 401 - {'detail': 'API-KEY not provied, please provide API Key in the header by set `Authorization` header'}"
            body: dict, {'detail': 'API-KEY not provied, please provide API Key in the header by set `Authorization` header'}
            response: httpx.Response, <Response [401]>
        """
        return APIStatusError(err_msg, body=body, response=response)
        
        
        # return super()._make_status_error(err_msg, body=body, response=response)


class AsyncHClient(AsyncAPIClient):
    pass



if __name__ == "__main__":
    client = HClient(base_url="http://localhost:42600/apiv2")    
    
    from openai_api import Stream
    from typing import Any
    data_need_stream = [
            1, 2, 3,
            "x", "y", "z",
            [[1, 2], [3, 4], [5, 6]],
            {"a": "b", "c": "d"},
        ]
    
    rst = client.post(
            path="/worker_unified_gate/?function=get_stream", 
            cast_to=Any,
            body={"kwargs": {"data": data_need_stream, "interval": 0.1}},
            stream=True,
            stream_cls=Stream[Any],
            )
    for i, x in enumerate(rst):
        print(f"i: {i}, x: {x}, type: {type(x)}")