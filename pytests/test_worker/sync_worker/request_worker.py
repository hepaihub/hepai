from hepai import HRModel

model = HRModel.connect(
    name="hepai/custom-model",
    base_url="http://localhost:4260/apiv2"
)

funcs = model.functions()  # Get all remote callable functions.
print(f"Remote callable funcs: {funcs}")

# 请求远程模型的custom_method方法
output = model.custom_method(a=1, b=2)
assert isinstance(output, int), f"output: type: {type(output)}, {output}"
print(f"Output of custon_method: {output}, type: {type(output)}")

# 测试流式响应
stream = model.get_stream(stream=True)  # Note: You should set `stream=True` to get a stream.
print(f"Output of get_stream:")
for x in stream:
    print(f"{x}, type: {type(x)}", flush=True)