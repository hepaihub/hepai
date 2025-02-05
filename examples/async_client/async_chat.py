"""异步客户端请求"""

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
from hepai.types import ChatCompletion



api_key=os.getenv("DDF_ZDZHANG_API_KEY")
base_url = "https://aiapi001.ihep.ac.cn/apiv2"
# client = HepAI(base_url=base_url, api_key=api_key)
# client = AsyncOpenAI(base_url=base_url, api_key=api_key)
client = AsyncHepAI(base_url=base_url, api_key=api_key, proxy=None)

q = "Sai hello"
# q = "tell me a history of Particle Physics"
model = "openai/gpt-4o-mini"
print(f"Q: {q}")
async def main():
    try:
        rst: ChatCompletion = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": q}],
        )
        print(f"A: {rst.choices[0].message.content}")
    except Exception as e:
        print(e)

asyncio.run(main())