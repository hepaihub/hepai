
import os
from hepai import HepAI 

# api_key = os.getenv("HEPAI_API_KEY")  # 从环境变量中读取API-KEY
api_key = os.getenv("DDF_ZDZHANG_API_KEY")  # 从环境变量中读取API-KEY
base_url = "https://aiapi001.ihep.ac.cn/apiv2"
client = HepAI(api_key=api_key, base_url=base_url)

# models = client.list_models()
models = client.models.list()
print(models)