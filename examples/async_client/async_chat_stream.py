"""异步客户端请求+流式输出"""

import os, sys
from pathlib import Path
here = Path(__file__).parent
import asyncio

# from openai import AsyncOpenAI
try:
    from hepai import __version__
except:
    sys.path.insert(1, f"{here.parent.parent}")
    from hepai import __version__

from hepai import HepAI, AsyncHepAI
from hepai.types import Stream, ChatCompletionChunk, AsyncStream



api_key=os.getenv("DDF_ZDZHANG_API_KEY")
base_url = "https://aiapi001.ihep.ac.cn/apiv2"
# client = HepAI(base_url=base_url, api_key=api_key)
# client = AsyncOpenAI(base_url=base_url, api_key=api_key)
client = AsyncHepAI(base_url=base_url, api_key=api_key)

# q = "Sai hello"
q = "tell me a history of Particle Physics"
model = "openai/gpt-4o-mini"
print(f"Q: {q}")
async def main():
    stream = True
    rst: AsyncStream = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": q}],
        stream=stream,
    )

    async for chunk in rst:
        chunk: ChatCompletionChunk = chunk
        x = chunk.choices[0].delta.content
        if x:
            print(x, end="", flush=True)

asyncio.run(main())