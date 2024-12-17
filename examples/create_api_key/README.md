
# 为他人创建API-KEY
import os
from hepai import HepAI
from hepai._types import APIKeyInfo, HUserListPage


api_key = os.getenv("APP_ADMIN_API_KEY")  # 从环境变量中读取API-KEY
base_url = "https://aiapi001.ihep.ac.cn/apiv2"  # 服务端地址
client = HepAI(api_key=api_key, base_url=base_url)

# 先获取用户列表和ID
users: HUserListPage = self.client.list_users()
user_id = users.data[-1].id  # 获取最后一个用户的ID

api_key: APIKeyInfo = self.client.create_api_key(
    user_id=free_user.id
    ) 
assert isinstance(api_key, APIKeyInfo), f"Create API Key failed, rst: {api_key}"
print(f'Create API Key success, API-KEY: {api_key}')