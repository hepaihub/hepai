

import os, sys
from pathlib import Path
import unittest
import time
here = Path(__file__).parent
try:
    from hepai import HepAI
except:
    sys.path.insert(1, str(here.parent.parent))
    from hepai import HepAI
from hepai.types import Stream, ChatCompletion


class TestGPT4o(unittest.TestCase):
    api_key=os.getenv("DDF_FREE_API_KEY"),
    api_key = "sk-EqzwdtKMGiJJfMhrPYHmcjAkcBLadcJqzwRKlSItANzJvRJ"
    client = HepAI(
                api_key=api_key,
                base_url=os.getenv("DDF_BASE_URL"),
            )
    
    def test_gpt_4o(self):
        
        q = "Sai hello"
        # q = "tell me a joke"
        model = "openai/gpt-4o-mini"

        # 测试非流
        rst: ChatCompletion = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": q}],
        )
        print(rst)
        # assert isinstance(rst, ChatCompletion), "rst must be a ChatCompletion object"
        # print(rst.choices[0].message.content)
        print(f"[TestGPT4o] PASSED chat.completion.create")

        stream = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": q}],
            stream=True,
        )
        assert isinstance(stream, Stream), "stream must be a Stream object"
        full_rst = ""
        for chunk in stream:
            char = chunk.choices[0].delta.content
            if char:
                # time.sleep(0.2)
                print(char, end="", flush=True)
                full_rst += char
        print(f"\n[TestGPT4o] PASSED chat.completion.create with stream")


if __name__ == "__main__":
    # unittest.main()
    TestGPT4o().test_gpt_4o()