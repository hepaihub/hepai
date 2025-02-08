from hepai import HRModel
import asyncio

async def main():

    model = await HRModel.async_connect(
        name="hepai/custom-model",
        base_url="http://localhost:4260/apiv2"
    )

    funcs = model.functions() # Get all remote callable functions.
    print(f"Remote callable funcs: {funcs}")

    # # 请求远程模型的custom_method方法
    # output = await model.custom_method(a=1, b=2)
    # assert isinstance(output, int), f"output: type: {type(output)}, {output}"
    # print(f"Output of custon_method: {output}, type: {type(output)}")

    # 测试流式响应
    stream = await model.a_get_stream() 
    print(f"Output of get_stream:")
    async for x in stream:
        print(f"{x}, type: {type(x)}", flush=True)

if __name__ == '__main__':
    asyncio.run(main())