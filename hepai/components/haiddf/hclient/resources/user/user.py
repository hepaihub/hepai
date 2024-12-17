

from typing import Union, Dict
from ..._types import Stream
from .._resource import SyncAPIResource

from ..._return_class import HAPIKeyListPage, HUserListPage

from ..._related_class import (
    APIKeyInfo, APIKeyDeletedInfo, UserInfo, UserDeletedInfo
)


class User(SyncAPIResource):

    @property
    def prefix(self) -> str:
        return "/user"
    
    def list_users(self):
        return self._get(
            f"{self.prefix}/list_users",
            cast_to=HUserListPage,
        )
    
    def create_user(self, **kwargs):
        payload = kwargs
        return self._post(
            f'{self.prefix}/create_user',
            body=payload,
            cast_to=UserInfo,
        )

    def delete_user(self, user_id: str):
        payload = {
            "user_id": str(user_id),
        }
        return self._post(
            f'{self.prefix}/delete_user',
            body=payload,
            cast_to=UserDeletedInfo,
        )
    
    def auth_user(self, username: str, password: str):
        payload = {
            "username": username,
            "password": password,
        }
        return self._post(
            f'{self.prefix}/auth_user',
            body=payload,
            cast_to=UserInfo,
        )
    
    