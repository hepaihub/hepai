


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


from hepai._types import HAPIKeyListPage, APIKeyInfo, APIKEYDeletedInfo


class TestDDFApiKey(unittest.TestCase):
    client = HepAI(
        api_key=os.getenv("DDF_API_KEY"),
        base_url="http://localhost:42601/apiv2",
    )
    
    def test_api_key(self):
        ## Register user
        # user_info = self.client.key.generate()

        api_keys: HAPIKeyListPage = self.client.list_api_keys()
        assert isinstance(api_keys, HAPIKeyListPage), f"List keys failed, rst: {api_keys}"
        print(f"[TestDDFApiKey] List keys PASSED: len_keys: {len(api_keys)}")

        # 创建API Key
        api_key: APIKeyInfo = self.client.create_api_key(
            key_name="Default",
            valid_time=30,
            allowed_models="all",
            user_id=None,
            remarks="Test API Key",
        )
        assert isinstance(api_key, APIKeyInfo), f"Create API Key failed, rst: {api_key}"
        print(f"[TestDDFApiKey] Create API Key PASSED: {api_key}")

        # 删除API Key
        del_api_key: APIKEYDeletedInfo = self.client.delete_api_key(api_key.id)
        assert isinstance(del_api_key, APIKEYDeletedInfo), f"Delete API Key failed, rst: {del_api_key}"
        print(f"[TestDDFApiKey] Delete API Key PASSED: {del_api_key}")


if __name__ == "__main__":
    # unittest.main()

    TestDDFApiKey().test_api_key()