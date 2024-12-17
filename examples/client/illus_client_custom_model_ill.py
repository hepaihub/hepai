from hepai import HepAI
# Create a HepAI client
client = HepAI()
# Get a remote model object
rm = client.get_remote_model()
# Call method of the remote model
output = rm.custom_fn(input=1)
print(output)  # Expected: 2


from hepai import HepAI
# 创建HepAI客户端
client = HepAI()
# 获取远程模型对象
rm = client.get_remote_model()
# 调用远程模型的方法
output = rm.custom_fn(input=1)
print(output)  # 预期输出: 2