from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, ChoiceDelta
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice



# 标准openai chat/completions stream模式
chatcompletionchunk = {
                "id":"chatcmpl-123",
                "object":"chat.completion.chunk",
                "created":1694268190,
                "model":"DrSai", 
                "system_fingerprint": "fp_44709d6fcb", 
                "usage": None,
                "choices":[{"index":0,
                            "delta":{"content":"", "function_call": None, "role": None, "tool_calls": None},
                            "logprobs":None,
                            "finish_reason":None}] # 非None或者stop字段会触发前端askuser
                } 
chatcompletionchunkend = {
    "id":"chatcmpl-123",
    "object":"chat.completion.chunk",
    "created":1694268190,
    "model":"DrSai", 
    "system_fingerprint": "fp_44709d6fcb", 
    "choices":[{'delta': {'content': None, 'function_call': None, 'refusal': None, 'role': None, 'tool_calls': None}, 'finish_reason': 'stop', 'index': 0, 'logprobs': None}]
    }

chatcompletions = {
    'id': 'chatcmpl-123', 
    'choices': [
    {'finish_reason': 'stop', 
    'index': 0, 
    'logprobs': None, 
    'message': {
        'content': '', 
        'refusal': None, 
        'role': 'assistant', 
        'audio': None, 
        'function_call': None, 
        'tool_calls': None}}], 
        'created': 1739758379, 
        'model': 'DrSai', 
        'object': 'chat.completion', 
        'service_tier': 'default', 
        'system_fingerprint': 'fp_13eed4fce1', 
        'usage': {
            'completion_tokens': 10, 'prompt_tokens': 8, 
            'total_tokens': 18, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 
            'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}}

def split_string(s, n):
    return [s[i:i+n] for i in range(0, len(s), n)]

