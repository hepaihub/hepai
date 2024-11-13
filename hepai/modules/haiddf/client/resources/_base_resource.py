import os
import time
import httpx
from typing import Union, Optional, Dict
from functools import wraps
from dataclasses import dataclass, field

@dataclass
class HErrorResponse(Exception):
    """Class to encapsulate HTTP request errors."""
    status_code: int
    message: str
    content: Optional[str] = None

    def __str__(self):
        details = f"HTTP Status: {self.status_code} - {self.message}"
        if self.content:
            details += f"\nContent: {self.content}"
        return details

from ..utils import post_process_decorator

@dataclass
class HClient:
    """基础的客户端类"""
    api_key: str = field(default=None, metadata={'description': 'API Key'})
    base_url: str = field(default=None, metadata={'description': 'Base URL'})
    proxy: str = field(default=None, metadata={'description': 'Proxy URL'})
    timeout: float = field(default=600.0, metadata={'description': 'Timeout in seconds'})

    def __post_init__(self):
        self.sync_api_resource = SyncAPIResource(client=self)
        
        self._post = self.sync_api_resource._post
        self._get = self.sync_api_resource._get
        self._put = self.sync_api_resource._put
        self._delete = self.sync_api_resource._delete
        self._patch = self.sync_api_resource._patch
        self._head = self.sync_api_resource._head
        self._options = self.sync_api_resource._options


class SyncAPIResource:

    def __init__(
            self, 
            client = None,   # HaiDDFClient
            ):
        if isinstance(client, dict):
            client = HClient(**client)
        if isinstance(client, HClient):
            self._client = client
        else:
            # HaiDDFClient
            from ..haiddf_client import HaiDDFClient
            self._client: HaiDDFClient = client
        self.api_key = self._client.api_key
        self.base_url = self._client.base_url
        self.proxy = self._client.proxy
        self.timeout = self._client.timeout
        self._http_client: httpx.Client = None


    @property
    def http_client(self) -> httpx.Client:
        if self._http_client is None:
            _client = self.get_http_client(
                proxy=self.proxy,
                timeout=self.timeout,
                base_url=self.base_url,
                )
            self._http_client = _client
        return self._http_client

    @post_process_decorator
    def _get(
        self, 
        url: str,
        *,
        headers = None,
        params = None,
        **kwargs):
        if params is not None:
            kwargs.update({
                # "headers": headers, 
                "params": params})
        return self.http_client.get(url, headers=headers, **kwargs)
        # return self.http_client.get(*args, **kwargs)
    
    @post_process_decorator
    def _post(
            self, 
            url: str,
            *,
            headers = None,
            json = None,
            params = None,
            **kwargs):
        headers = headers if headers else self.headers
        # kwargs.update({"headers": headers, "json": json})
        return self.http_client.post(
            url, 
            json=json,
            headers=headers,
            params=params,
            **kwargs)
        # return self.http_client.post(*args, **kwargs)
    
    def _put(self, *args, **kwargs):
        return self.http_client.put(*args, **kwargs)
    
    def _delete(self, *args, **kwargs):
        return self.http_client.delete(*args, **kwargs)
    
    def _patch(self, *args, **kwargs):
        return self.http_client.patch(*args, **kwargs)
    
    def _head(self, *args, **kwargs):
        return self.http_client.head(*args, **kwargs)
    
    def _options(self, *args, **kwargs):
        return self.http_client.options(*args, **kwargs)

    @classmethod
    def get_http_client(cls, **kwargs) -> httpx.Client:
        DEFAULT_TIMEOUT = httpx.Timeout(timeout=600.0, connect=5.0)
        DEFAULT_LIMITS = httpx.Limits(max_connections=100, max_keepalive_connections=20)
        proxy = kwargs.get("proxy", None)
        if proxy is None:
            proxies = None
        else:
            proxies = {
                "http://": proxy,
                "https://": proxy,
            }
        base_url = kwargs.get("base_url", None)
        base_url = base_url or os.getenv("DDF_BASE_URL")
        timeout = kwargs.get("timeout", DEFAULT_TIMEOUT)
        timeout = DEFAULT_TIMEOUT if (timeout is None) else timeout
        transport = kwargs.get("transport", None)
        limits = kwargs.get("limits", DEFAULT_LIMITS)
        limits = DEFAULT_LIMITS if (limits is None) else limits
        http_client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            proxies=proxies,
            transport=transport,
            limits=limits,
        )
        return http_client

    
    @property
    def headers(self) -> dict:
        # if self.api_key is None:
        #     raise ValueError("API Key is required.")
        headers = dict()
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        headers["Content-Type"] = "application/json"
        return headers
    
    def _sleep(self, seconds: float) -> None:
        time.sleep(seconds)
