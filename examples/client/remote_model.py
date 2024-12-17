import os
from hepai import HepAI
from hepai._types import HRemoteModel

# 创建HepAI客户端
client = HepAI(api_key=os.getenv("DDF_API_KEY"))

# 获取一个远程模型对象
model_name = "hepai/demo-model"
remote_model: HRemoteModel = client.get_remote_model(model_name=model_name)

# 请求远程模型的__call__方法
rst = remote_model(1, 2, extra="extra")
assert isinstance(rst, str), f"rst: type: {type(rst)}, {rst}"
print(f"Request str via remote model PASSED, type: {type(rst)}, value: {rst}")

# 请求远程模型的get_int方法，想调用什么方法，自定义方法即可
rst = remote_model.get_int(1, 2)
assert isinstance(rst, int), f"rst: type: {type(rst)}, {rst}"
print(f"Request int via remote model PASSED, type: {type(rst)}, value: {rst}")

# 请求远程模型的get_float方法
rst = remote_model.get_float(1., 2)
assert isinstance(rst, float), f"rst: type: {type(rst)}, {rst}"
print(f"Request float via remote model PASSED, type: {type(rst)}, value: {rst}")

# 请求远程模型的get_list方法
rst = remote_model.get_list([1, 2, 3], [4, 5, 6])
assert isinstance(rst, list), f"rst: type: {type(rst)}, {rst}"
print(f"Request list via remote model PASSED, type: {type(rst)}, value: {rst}")

# 请求远程模型的get_dict方法
rst = remote_model.get_dict({"a": 1, "b": 2}, {"x": 3, "y": 4})
assert isinstance(rst, dict), f"rst: type: {type(rst)}, {rst}"
print(f"Request dict via remote model PASSED, type: {type(rst)}, value: {rst}")