

from typing import Literal, Optional, List, Dict
from ._base_resource import SyncAPIResource
from .._client_class import HUserListPage
from .._related_class import UserInfo, UserDeletedInfo

class UserResource(SyncAPIResource):

    @property
    def path(self):
        return '/user'

    def list_users(self):
        url = f'{self.base_url}{self.path}/list_users'
        return self._get(url, headers=self.headers, cast_to=HUserListPage)
    
    def create_user(self, **kwargs):
        url = f'{self.base_url}{self.path}/create_user'
        return self._post(
            url, 
            headers=self.headers, 
            json=kwargs,
            cast_to=UserInfo,
            )
    
    def delete_user(self, user_id: str):
        url = f'{self.base_url}{self.path}/delete_user'
        payload = {
            "user_id": str(user_id),
        }
        return self._post(
            url, 
            headers=self.headers, 
            json=payload,
            cast_to=UserDeletedInfo,
            )

    ## --- 以下的LiteLLM的，准备弃用 --- ##
    def list_customers(self):
        """
        curl --location --request GET 'http://0.0.0.0:4000/customer/list'         --header 'Authorization: Bearer sk-1234'
        """
        url = f'{self.base_url}/customer/list'
        headers = self.headers
        return self._get(url, headers=headers)
    
    def create_customer(
            self,
            user_id: str,
            alias: Optional[str] = None,
            blocked: bool = False,
            max_budget: Optional[float] = None,
            budget_id: Optional[str] = None,
            allowed_model_region: Optional[Literal["eu"]] = None,
            default_model: Optional[str] = None,
            metadata: Optional[dict] = None,
            ):
        """
        user_id: str - The unique identifier for the user.
        alias: Optional[str] - A human-friendly alias for the user.
        blocked: bool - Flag to allow or disallow requests for this end-user. Default is False.
        max_budget: Optional[float] - The maximum budget allocated to the user. Either 'max_budget' or 'budget_id' should be provided, not both.
        budget_id: Optional[str] - The identifier for an existing budget allocated to the user. Either 'max_budget' or 'budget_id' should be provided, not both.
        allowed_model_region: Optional[Literal["eu"]] - Require all user requests to use models in this specific region.
        default_model: Optional[str] - If no equivalent model in the allowed region, default all requests to this model.
        metadata: Optional[dict] = Metadata for customer, store information for customer. Example metadata = {"data_training_opt_out": True}
        
        curl:
            curl --location 'http://0.0.0.0:4000/customer/new'         --header 'Authorization: Bearer sk-1234'         --header 'Content-Type: application/json'         --data '{
            "user_id" : "ishaan-jaff-3",
            "allowed_region": "eu",
            "budget_id": "free_tier",
            "default_model": "azure/gpt-3.5-turbo-eu" <- all calls from this user, use this model? 
        }'

        # return end-user object
        """
        url = f'{self.base_url}/customer/new'
        headers = self.headers
        data = {
            "user_id": user_id,
            "alias": alias,
            "blocked": blocked,
            "max_budget": max_budget,
            "budget_id": budget_id,
            "allowed_model_region": allowed_model_region,
            "default_model": default_model,
            "metadata": metadata,
        }
        return self._post(url, headers=headers, json=data)

    def create(
            self,
            user_id: Optional[str] = None,
            user_alias: Optional[str] = None,
            teams: Optional[List[str]] = [],
            organization_id: Optional[str] = None,
            user_email: Optional[str] = None,
            send_invite_email: Optional[bool] = False,
            user_role: Literal["proxy_admin", "proxy_admin_viewer", "internal_user", "internal_user_viewer", "team", "customer"] = "customer",
            max_budget: Optional[float] = None,
            budget_duration: Optional[Literal["30s", "30m", "30h", "30d"]] = None,
            models: Optional[List[str]] = [],
            tpm_limit: Optional[int] = None,
            rpm_limit: Optional[int] = None,
            auto_create_key: bool = True,
            ):
        """
        Use this to create a new INTERNAL user with a budget. Internal Users can access LiteLLM Admin UI to make keys, request access to models. This creates a new user and generates a new api key for the new user. The new api key is returned.
        Args:
            user_id: Optional[str] - Specify a user id. If not set, a unique id will be generated.
            user_alias: Optional[str] - A descriptive name for you to know who this user id refers to.
            teams: Optional[list] - specify a list of team id's a user belongs to.
            organization_id: Optional[str] - specify the org a user belongs to.
            user_email: Optional[str] - Specify a user email.
            send_invite_email: Optional[bool] - Specify if an invite email should be sent.
            user_role: Optional[str] - Specify a user role - "proxy_admin", "proxy_admin_viewer", "internal_user", "internal_user_viewer", "team", "customer". Info about each role here: https://github.com/BerriAI/litellm/litellm/proxy/_types.py#L20
            max_budget: Optional[float] - Specify max budget for a given user.
            budget_duration: Optional[str] - Budget is reset at the end of specified duration. If not set, budget is never reset. You can set duration as seconds ("30s"), minutes ("30m"), hours ("30h"), days ("30d").
            models: Optional[list] - Model_name's a user is allowed to call. (if empty, key is allowed to call all models)
            tpm_limit: Optional[int] - Specify tpm limit for a given user (Tokens per minute)
            rpm_limit: Optional[int] - Specify rpm limit for a given user (Requests per minute)
            auto_create_key: bool - Default=True. Flag used for returning a key as part of the /user/new response
        Returns:
            key: (str) The generated api key for the user
            expires: (datetime) Datetime object for when key expires.
            user_id: (str) Unique user id - used for tracking spend across multiple keys for same user id.
            max_budget: (float|None) Max budget for given user.
        """

        url = f'{self.base_url}/user/new'
        headers = self.headers
        data = {
            "user_id": user_id,
            "user_alias": user_alias,
            "teams": teams,
            "organization_id": organization_id,
            "user_email": user_email,
            "send_invite_email": send_invite_email,
            "user_role": user_role,
            "max_budget": max_budget,
            "budget_duration": budget_duration,
            "models": models,
            "tpm_limit": tpm_limit,
            "rpm_limit": rpm_limit,
            "auto_create_key": auto_create_key,
        }
        return self._post(url, headers=headers, json=data)
