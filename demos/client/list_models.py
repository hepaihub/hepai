
import os
from hepai import HepAI 

api_key = os.getenv("HEPAI_API_KEY")  # 从环境变量中读取API-KEY
client = HepAI(api_key=api_key)

models = client.list_models()
print(models)