


import os, sys
from typing import List, Dict, Callable, Generator, Optional, Literal, Union
from pathlib import Path
import unittest
here = Path(__file__).parent
import uuid
from datetime import datetime
from dateutil.relativedelta import relativedelta


try:
    from hepai import HepAI
except:
    sys.path.insert(1, str(here.parent.parent))
    from hepai import HepAI


from hepai.types import (
    HAPIKeyListPage, APIKeyInfo, APIKeyDeletedInfo, HUserListPage, UserInfo
    )


class TestDDFApiKey(unittest.TestCase):
    
    
    def test_api_key(self):
        client = HepAI(
                api_key=os.getenv("DDF_APP_ADMIN_API_KEY"),
                base_url=os.getenv("DDF_BASE_URL"),
            )   

        # 获取用户信息
        # user_info: UserInfo = self.client.get_user_id_by_name("")
        users: HUserListPage = client.list_users()
        assert isinstance(users, HUserListPage), f"List users failed, rst: {users}"

        # 验证不能为admin创建api_key
        admin: UserInfo = [u for u in users if u.user_level.to_str() == "admin"][0]
        try:
            rst = client.create_api_key(user_id=admin.id)
        except Exception as e:
            assert "Permission denied" in str(e), f"Create API Key failed, rst: {e}"
            print(f"[TestAppAdminApiKey] 正确地拒绝了为admin创建api_key: {e}")
        
        # 验证可为其他用户创建api_key
        free_user: UserInfo = [u for u in users if u.user_level.to_str() == "free"][0]
        api_key: APIKeyInfo = client.create_api_key(user_id=free_user.id)
        assert isinstance(api_key, APIKeyInfo), f"Create API Key failed, rst: {api_key}"
        print(f"[TestAppAdminApiKey] Create API Key PASSED: {api_key}")
       
        # 成功创建后还需要删除
        del_api_key: APIKeyDeletedInfo = client.delete_api_key(api_key.id)
        assert isinstance(del_api_key, APIKeyDeletedInfo), f"Delete API Key failed, rst: {del_api_key}"
        print(f"[TestAppAdminApiKey] Delete API Key PASASED: {del_api_key}")
        pass


    def test_free_api_key(self):

        pass


if __name__ == "__main__":
    # unittest.main()

    TestDDFApiKey().test_api_key()