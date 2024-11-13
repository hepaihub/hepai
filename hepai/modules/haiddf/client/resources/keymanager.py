


from typing import Literal, List, Dict, Union
from ._base_resource import SyncAPIResource
from .._client_class import HAPIKeyListPage
from .._related_class import APIKeyInfo, APIKEYDeletedInfo

class KeyManager(SyncAPIResource):

    @property
    def path(self):
        return '/key'

    def info(self, api_key: str):
        """
        curl 'http://0.0.0.0:4000/key/info?key=<user-key>' \
        -X GET \
        -H 'Authorization: Bearer <your-master-key>
        """
        url = f'{self.base_url}{self.path}/info?key={api_key}'
        headers = self.headers
        return self._get(url, headers=headers)

    def list_api_keys(self):
        """
        列出用户所有的api-key
        """
        url = f'{self.base_url}{self.path}/list_api_keys'
        return self._get(url, headers=self.headers, cast_to=HAPIKeyListPage)
    
    def create_api_key(
            self,
            *,
            key_name: str = "Default",
            valid_time: int = 30,
            user_id: str = None,
            allowed_models: Union[str, Dict] = "all",
            remarks: str = "",
            ):
        """
        创建API Key
        """
        url = f'{self.base_url}{self.path}/create_api_key'
        payload = {
            "key_name": key_name,
            "valid_time": valid_time,
            "user_id": user_id,
            "allowed_models": allowed_models,
            "remarks": remarks,
        }
        return self._post(
            url,
            headers=self.headers,
            json=payload,
            cast_to=APIKeyInfo,
            )
    
    def delete_api_key(self, api_key_id: str):
        """
        删除API Key
        """
        url = f'{self.base_url}{self.path}/delete_api_key'
        payload = {
            "api_key_id": api_key_id,
        }
        return self._post(
            url,
            headers=self.headers,
            json=payload,
            cast_to=APIKEYDeletedInfo,
            )

    ### --- 以下的LiteLLM的，准备弃用 --- ###
    def generate(
            self,
            *,
            duration: Literal["30s", "30m", "30h", "30d"] = None,
            key_alias: str = None,
            key: str = None,
            team_id: str = None,
            user_id: str = None,
            models: List[str] = [],
            aliases: Dict = {},
            config: Dict = {},
            spend: int = 0,
            send_invite_email: bool = False,
            max_budget: float = None,
            budget_duration: Literal["30s", "30m", "30h", "30d"] = None,
            max_parallel_requests: int = None,
            metadata: Dict = {},
            guardrails: List[str] = None,
            permissions: Dict = {},
            model_max_budget: Dict = {},
            model_rpm_limit: Dict = {},
            model_tpm_limit: Dict = {},
            ):
        """
        Generate an API key based on the provided data.
        Args:
            duration: Optional[str] - Specify the length of time the token is valid for. You can set duration as seconds ("30s"), minutes ("30m"), hours ("30h"), days ("30d").
            key_alias: Optional[str] - User defined key alias
            key: Optional[str] - User defined key value. If not set, a 16-digit unique sk-key is created for you.
            team_id: Optional[str] - The team id of the key
            user_id: Optional[str] - The user id of the key
            models: Optional[list] - Model_name's a user is allowed to call. (if empty, key is allowed to call all models)
            aliases: Optional[dict] - Any alias mappings, on top of anything in the config.yaml model list. - https://docs.litellm.ai/docs/proxy/virtual_keys#managing-auth---upgradedowngrade-models
            config: Optional[dict] - any key-specific configs, overrides config in config.yaml
            spend: Optional[int] - Amount spent by key. Default is 0. Will be updated by proxy whenever key is used. https://docs.litellm.ai/docs/proxy/virtual_keys#managing-auth---tracking-spend
            send_invite_email: Optional[bool] - Whether to send an invite email to the user_id, with the generate key
            max_budget: Optional[float] - Specify max budget for a given key.
            budget_duration: Optional[str] - Budget is reset at the end of specified duration. If not set, budget is never reset. You can set duration as seconds ("30s"), minutes ("30m"), hours ("30h"), days ("30d").
            max_parallel_requests: Optional[int] - Rate limit a user based on the number of parallel requests. Raises 429 error, if user's parallel requests > x.
            metadata: Optional[dict] - Metadata for key, store information for key. Example metadata = {"team": "core-infra", "app": "app2", "email": "ishaan@berri.ai" }
            guardrails: Optional[List[str]] - List of active guardrails for the key
            permissions: Optional[dict] - key-specific permissions. Currently just used for turning off pii masking (if connected). Example - {"pii": false}
            model_max_budget: Optional[dict] - key-specific model budget in USD. Example - {"text-davinci-002": 0.5, "gpt-3.5-turbo": 0.5}. IF null or {} then no model specific budget.
            model_rpm_limit: Optional[dict] - key-specific model rpm limit. Example - {"text-davinci-002": 1000, "gpt-3.5-turbo": 1000}. IF null or {} then no model specific rpm limit.
            model_tpm_limit: Optional[dict] - key-specific model tpm limit. Example - {"text-davinci-002": 1000, "gpt-3.5-turbo": 1000}. IF null or {} then no model specific tpm limit. Examples:
        """
        # 定义请求的 URL 和头部信息
        url = f'{self.base_url}/key/generate'
        headers = self.headers
   
        payload = {
            "duration": duration,
            "key_alias": key_alias,
            "key": key,
            "team_id": team_id,
            "user_id": user_id,
            "models": models,
            "aliases": aliases,
            "config": config,
            "spend": spend,
            "send_invite_email": send_invite_email,
            "max_budget": max_budget,
            "budget_duration": budget_duration,
            "max_parallel_requests": max_parallel_requests,
            "metadata": metadata,
            "guardrails": guardrails,
            "permissions": permissions,
            "model_max_budget": model_max_budget,
            "model_rpm_limit": model_rpm_limit,
            "model_tpm_limit": model_tpm_limit,
        }

            
        return self._post(
            url, 
            headers=headers,
            json=payload,
            )
    
    