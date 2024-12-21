import os, sys
from pathlib import Path

try:
    from hepai import __version__
except:
    here = Path(__file__).parent
    sys.path.insert(1, f'{here.parent.parent}')
    from hepai import __version__


import os
from hepai import HepAI
from hepai.types import APIKeyInfo, HUserListPage


api_key = os.getenv("DDF_APP_ADMIN_API_KEY")  # 从环境变量中读取API-KEY
base_url = "https://aiapi001.ihep.ac.cn/apiv2"  # 服务端地址
client = HepAI(api_key=api_key, base_url=base_url)

# 先获取用户列表和ID
users: HUserListPage = client.list_users()
user = users.data[-1]  # 获取最后一个用户的ID
print(f'User: {user}')

api_key: APIKeyInfo = client.create_api_key(
    umt_id=user.umt_id,  # 通过umt_id创建API-KEY
    ) 
assert isinstance(api_key, APIKeyInfo), f"Create API Key failed, rst: {api_key}"
print(f'Create API Key success, API-KEY: {api_key}')