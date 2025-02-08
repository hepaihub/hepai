from hepai import HRModel
from typing import Any
import time
import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

DEFAULT_STREAM_DATA = [
    1, 2, 3,
    "x", "y", "z",
    [[1, 2], [3, 4], [5, 6]],
    {"a": "b", "c": "d"},
]

class CustomWorkerModel(HRModel):  # Define a custom worker model inheriting from HRModel.
    def __init__(self, name: str = "hepai/custom-model", **kwargs):
        super().__init__(name=name, **kwargs)

    @HRModel.remote_callable  # Decorate the function to enable remote call.
    def custom_method(self, a: int = 1, b: int = 2) -> int:
        """Define your custom method here."""
        return a + b
    
    # @HRModel.remote_callable
    # async def a_get_stream(self, data: Any = None, interval: float = 0.2):
    #     """An example of a function that returns a stream type"""

    #     data = data if data is not None else DEFAULT_STREAM_DATA
    #     for i, x in enumerate(data):
    #         time.sleep(interval)  # 注：此处为了演示，故意加了延迟，实际使用时应该去掉
    #         yield f"data: {json.dumps(x)}\n\n"
    
    @HRModel.remote_callable
    async def a_get_stream(self, data: Any = None, interval: float = 0.2):
        """An example of a function that returns a stream type"""

        data = data if data is not None else DEFAULT_STREAM_DATA
        
        # This is an async generator
        async def event_generator():
            for x in data:
                await asyncio.sleep(interval)  # 使用异步的sleep
                yield f"data: {json.dumps(x)}\n\n"

        # Wrap the async generator in a StreamingResponse
        return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    CustomWorkerModel.run()  # Run the custom worker model.