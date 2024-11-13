import os
from hepai import HepAI
from hepai._types import APIKeyInfo


api_key = os.getenv("DDF_API_KEY")  # 从环境变量中读取API-KEY
base_url = "http://localhost:42601/apiv2"  # 服务端地址
client = HepAI(api_key=api_key, base_url=base_url)
    
new_api_key: APIKeyInfo = client.create_api_key(
        key_name="Default",
        valid_time=30,
        allowed_models="all",
        user_id="xxx",  # 用户ID，如果不指定则默认为自己创建，如果指定则为指定用户创建
        remarks="Test API Key",
    )
assert isinstance(new_api_key, APIKeyInfo), f"Create API Key failed, {new_api_key}"
print(f'Create API Key success, API-KEY: {new_api_key}')