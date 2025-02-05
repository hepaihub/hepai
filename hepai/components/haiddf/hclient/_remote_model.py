

import types
from . import resources
from ._related_class import WorkerInfo


class LRemoteModel:
    """
    Local Remote Model
    """

    def __init__(
            self,
            name: str,
            worker_info: WorkerInfo,
            worker_resource: resources.AsyncWorker
            ) -> None:
        self.name = name
        self.wr: resources.AsyncWorker = worker_resource
        if not isinstance(worker_info, WorkerInfo):
            raise ValueError(f"Failed to get remote model: {worker_info}")

        self.model_resource = worker_info.get_model_resource(model_name=name)
        self.model_functions = self.model_resource.model_functions
        # self.model_functions = ["train", "__call__"]
        if len(self.model_functions) == 0:
            raise ValueError(f"Remote model `{self.name}` has no functions can be called remotely, please check the worker model.")

        # 自动注册远程模型的函数
        for func in self.model_functions:
            original_func = self.function_warpper(self.name, func)
            # Use functools.wraps to preserve original function metadata when creating new methods
            # @functools.wraps(original_func)
            # def wrapper(*args, **kwargs):
            #     return original_func(*args, **kwargs)
            # setattr(self, func, types.MethodType(wrapper, self))
            setattr(self, func, types.MethodType(original_func, self))
   

    def function_warpper(self, model_name: str, function_name: str):
        def call_remote_function(*args, **kwargs):
            if isinstance(args[0], LRemoteModel):
                # 为了处理通过types.MethodType注册时，第一个参数是self的情况
                args = args[1:]
            rst =  self.wr.request(
                target={
                    "model": model_name, 
                    "function": function_name
                    },
                args=args,
                kwargs=kwargs,
            )
            return rst
        return call_remote_function
    
    def __call__(self, *args, **kwargs):
        return self.function_warpper(self.name, '__call__')(*args, **kwargs)

    def functions(self):
        return self.model_functions


class LRModel(LRemoteModel):
    """
    Alias of Local Remote Model
    """
    ...