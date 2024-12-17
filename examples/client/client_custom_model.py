
from hepai import HepAI
from hepai.types import HRModel

# 创建HepAI客户端
client = HepAI(base_url="http://localhost:42602/apiv2")

# 获取一个远程模型对象
model_name = "hepai/custom-model"
rmodel: HRModel = client.get_remote_model(model_name=model_name)

# 请求远程模型的custom_method方法
rst = rmodel.custom_fn(input)
assert isinstance(rst, int), f"rst: type: {type(rst)}, {rst}"
print(f"Request `custom_method` on remote model PASSED, type: {type(rst)}, value: {rst}")
