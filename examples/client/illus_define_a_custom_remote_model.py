from hepai import HRModel
# Define a Custom Remote Model class
class CustomRomoteModel(HRModel):
    @HRModel.remote_callable
    def custom_fn(self, input: int) -> int:
        """Define custom method here"""
        return input + 1

@dataclass
class CustomWorkerArgs(HWorkerArgs):
    """
    自定义参数类，继承自HWorkerArgs，
        - 可在此处定义自己的默认参数，添加新的参数
        - 也可以在程序运行时通过命令行传入参数，例如：--no_register True
    """
    pass
    
if __name__ == "__main__":
    # 实例化模型
    model = CustomWorkerModel(name="hepai/custom-model")
    # 解析命令行参数
    worker_config = hai.parse_args(CustomWorkerArgs)
    # 实例化APP，是一个fastapi应用
    app = HWorkerAPP(model, worker_config=worker_config)
    print(app.worker.get_worker_info(), flush=True)
    # 启动服务
    uvicorn.run(app, host=app.host, port=app.port)



