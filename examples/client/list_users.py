



import os
from hepai import HepAI
from hepai._types import HUserListPage

api_key = os.getenv("DDF_API_KEY")  # 从环境变量中读取API-KEY
base_url = "http://localhost:42601/apiv2"  # 服务端地址
client = HepAI(api_key=api_key, base_url=base_url)

users: HUserListPage = client.list_users()
assert isinstance(users, HUserListPage), f"List users failed, rst: {users}"
if len(users) == 0:
    raise Exception("No user found.")
print(f"[TestControllerUsers] List users PASSED: len_users: {len(users)}")