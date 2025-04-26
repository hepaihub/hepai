from dataclasses import dataclass, field
from typing import List, Optional, Dict, Literal, Generator, Union
import json, re, time
from openai.types.chat import ChatCompletionChunk
from .base_assistant import BaseObject


@dataclass
class Text:
    value: str
    annotations: List[dict] = field(default_factory=list)

    def to_dict(self):
        return {
            "value": self.value,
            "annotations": self.annotations
        }

@dataclass
class Content:
    type: Literal["text", "image", "video", "audio", "file"]
    text: Text = None

    def to_dict(self):
        return {
            "type": self.type,
            "text": self.text.to_dict() if self.text else None
        
        }

@dataclass
class ThreadMessage(BaseObject):
    id: str
    object: str
    created_at: int
    assistant_id: Optional[str] 
    thread_id: str
    run_id: Optional[str]
    role: str
    content: List[Content]

    order_id: Optional[str]
    attachments: List[dict] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)

    sender: Optional[str] = None  # Indicate who created this message, e.g. specific username or assistant name
    task_type: Optional[str] = None  # Indicate the task type of this message, e.g. "draw", "translate", "summarize", etc.

    def __post_init__(self):
        super(ThreadMessage, self).__post_init__()
        self._thread = None
        pass

    @property
    def thread(self):
        return self._thread
    
    @thread.setter
    def thread(self, value):
        self._thread = value

    def to_dict(self, only_output_keys=True):
        """
        由于Content字段是元素为Content对象的列表，需要特殊处理
        """
        new_dict = dict()
        for k, v in self.__dict__.items():
            if only_output_keys and k not in self.output_keys:
                continue
            if k == "content" and v:
                v = [x.to_dict() for x in v]
            new_dict[k] = v
        return new_dict

    @property
    def output_keys(self):
        return ["id", "object", "created_at", "assistant_id", "thread_id", "run_id", 
                "role", "content", "order_id", "attachments", "metadata", "sender",
                "task_type"]

    @property
    def allowed_update_keys(self):
        return ["content", "attachments", "metadata", "sender", "task_type"]
    
    def to_oai_message(self):
        """转换为OAI消息格式"""
        if self.content is None:
            return None

        assert len(self.content) == 1, "Only one content is allowed in a message"

        # print("/n/n messages:",self.content[0])
        return {
            "content": self.content[0].text.value,
            "role": self.role,
        }
    
    def content_str(self):
        assert len(self.content) == 1, "Only one content is allowed in a message"
        return self.content[0].text.value
    
    def construct_status_event(self, status: str=None):
        status = status or self.status
        return {
            "data": self.to_dict(),
            "event": f"thread.message.{status}"
        }
    
    def convert_str_to_stream_message_delta(self, text: str, chunk_size: int=5, sleep_time: float=0.1):
        '''
        Convert a string to a stream of ChatCompletionChunk.
        chunk_size: the maximum length of each chunk.
        '''     
        Tester_OUTPUT = text.split("[**Tester OUTPUT**]") # 兼容tester的流式输出
        if len(Tester_OUTPUT) == 4: # 通过[**Tester OUTPUT**]确定是tester的输出，并进行分割
            chunks = [Tester_OUTPUT[0]+Tester_OUTPUT[1]+Tester_OUTPUT[2]+Tester_OUTPUT[3]]
        else:
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        # print(f"chunks: {chunks}")
        for i, chunk in enumerate(chunks):
            time.sleep(sleep_time)
            data = self.construct_delta_event(chunk, id=0)
            yield f'data: {json.dumps(data)}\n\n'
        
        return text

    def convert_Generator_to_message_delta(self, stream: Generator):
        
        """
        Support for Dicts in the stream, in addition to pure str.
        目前支持yeild的类型为str或ChatCompletionChunk。 后续添加
        """
        response = {
            'content': '', 
            'role': '', 
            'function_call': None,
            'tool_calls': [{
                'id': '',
                'function': {
                    'arguments': '',
                    'name': ''
                },
                'type': '', 
                'index': 0
            }]
        }
        full_response = ""
        for i, x in enumerate(stream):
            # assert isinstance(x, ChatCompletionChunk), "The stream should be a generator of ChatCompletionChunk"
            if isinstance(x, str):
                content = x
                event_id = 0
                if "![Image](data:image;base64," in x:
                    print("TODO: base_thread_message.py: Image will not be added to messages.")
            elif isinstance(x, ChatCompletionChunk):
                content:str = x.choices[0].delta.content
                event_id = x.id
            else:
                raise ValueError("The stream should be a generator of str or ChatCompletionChunk")

            if content:
                full_response += content
                # response["content"] += content
                # send to the stream
                data = self.construct_delta_event(content, id=event_id)
                yield f'data: {json.dumps(data)}\n\n'      

        # full_response = response["content"]
        tmp_content = Content(
            type="text",
            text=Text(
                value=full_response,
                annotations=[]
                ))
        assert self.content == [], "Content should be [] when finishing the stream"
        self.content = [tmp_content]
        return full_response
    
    def convert_oai_stream_to_message_delta(self, stream: Generator):
        
        """
        Support for Dicts in the stream, in addition to pure str.
        """
        response = {
            'content': '', 
            'role': '', 
            'function_call': None,
            'tool_calls': [{
                'id': '',
                'function': {
                    'arguments': '',
                    'name': ''
                },
                'type': '', 
                'index': 0
            }]
        }

        for i, x in enumerate(stream):
            assert isinstance(x, ChatCompletionChunk), "The stream should be a generator of ChatCompletionChunk"
            content = x.choices[0].delta.content

            if content:
                response["content"] += content
                # send to the stream
                data = self.construct_delta_event(content, id=x.id)
                yield f'data: {json.dumps(data)}\n\n'      

        full_response = response["content"]
        tmp_content = Content(
            type="text",
            text=Text(
                value=full_response,
                annotations=[]
                ))
        assert self.content == [], "Content should be [] when finishing the stream"
        self.content = [tmp_content]
        return full_response
            
    def emit_delta_event(self, stream: Generator):

        message_delta_generator = self.convert_oai_stream_to_message_delta(stream)
        self.queue.put(message_delta_generator)

    def construct_delta_event(self, content: str, id: str):
        '''
        - 构造OpenAI ChatCompletionChunk, 可以根据自己的要求修改data内容, 适配智能体的特殊输出和前端的解析
            - 为了兼容图像路径/url输出, 这里构造了"image_url"字段用于解析图像url
        '''
        

        # 提取pic_url和pdf_url-这里为了兼容Tseter的输出，将图片和pdf文件路径提取出来
        pic_urls = []
        pic_pattern = r'<pic: (.*?) >'
        matches = re.findall(pic_pattern, content)
        if matches:
            for match in matches:
                if match!="None":
                    pic_urls.append(match)
        pdf_urls = []
        pdf_pattern = r'<pdf: (.*?) >'
        matches = re.findall(pdf_pattern, content)
        if matches:
            for match in matches:
                if match!="None":    
                    pdf_urls.append(match)
        data = {
                    "id": id,
                    "object": "thread.message.delta",
                    "delta": {
                        "content": [
                        {
                            "index": 0,
                            "type": "text",
                            "text": { 
                                "value": content, 
                                "annotations": [] }
                        }
                        ]
                    }
                    }
        if len(pic_urls)>0 or len(pdf_urls)>0:
            data = {
                    "id": id,
                    "object": "thread.message.delta",
                    "delta": {
                        "content": [
                        {
                            "index": 0,
                            "type": "image_url",
                            "image_url": { 
                                "text": content,
                                "url": pic_urls,
                                "pdf_url": pdf_urls,
                                "detail": "auto" }
                        }
                        ]
                    }
                    }
                    
        return {
            "data": data,
            "event": f"thread.message.delta"
        }
    
    def construct_ask_human_input_event(self):

        data = {
            "id": "msg_123",
            "object": "thread.message.delta",
            "content": [
                {
                    "index": 0,
                    "type": "text",
                    "text": {
                        "value": "[ST]Please provide your input.[END]",
                        "annotations": []
                    }
                }
            ],
        }
        return {
            "data": data,
            "event": f"thread.message.delta"
        }


        

    
   