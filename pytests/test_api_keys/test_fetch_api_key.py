import os, sys
from typing import List, Dict, Callable, Generator, Optional, Literal, Union
from pathlib import Path
import unittest
here = Path(__file__).parent
import uuid
from datetime import datetime
# from dateutil.relativedelta import relativedelta


try:
    from hepai import HepAI
except:
    sys.path.insert(1, str(here.parent.parent))
    from hepai import HepAI


from hepai.types import (
    HAPIKeyListPage, APIKeyInfo, APIKeyDeletedInfo, HUserListPage, UserInfo
    )

class TestDDFApiKey(unittest.TestCase):
    
    def test_fetch_api_key(self):
        client = HepAI(
            api_key=os.getenv("DDF_APP_ADMIN_API_KEY"), 
            base_url=os.getenv("DDF_BASE_URL"))
        
        api_key = client.fetch_api_key(username="zdzhang@ihep.ac.cn")

        assert isinstance(api_key, APIKeyInfo), f"Create API Key failed, rst: {api_key}"
        print(f"[TestAppAdminApiKey] Create API Key PASSED: {api_key}")
        
        # 成功创建后还需要删除
        del_api_key: APIKeyDeletedInfo = client.delete_api_key(api_key.id)
        assert isinstance(del_api_key, APIKeyDeletedInfo), f"Delete API Key failed, rst: {del_api_key}"
        print(f"[TestAppAdminApiKey] Delete API Key PASASED: {del_api_key}")


if __name__ == "__main__":
    # unittest.main()
    tdf = TestDDFApiKey()
    tdf.test_fetch_api_key()
