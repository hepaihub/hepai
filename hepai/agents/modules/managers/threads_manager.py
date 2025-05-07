"""
用来管理不同的用户所创建的线程，以及线程的状态
"""
from typing import List, Dict
import os, sys
from pathlib import Path
here = Path(__file__).parent
import time
import json

try:
    from hepai.agents.version import __version__
except:
    sys.path.insert(1, f'{here.parent.parent.parent}')
    from hepai.agents.version import __version__
from hepai.agents.utils import BaseJsonSaver
from hepai.agents.version import __appname__
from hepai.agents.configs import CONST

from hepai.agents.modules.managers.base_thread_message import ThreadMessage, Content, Text
from hepai.agents.modules.managers.base_thread import Thread, ThreadDeleted
from hepai.agents.modules.managers.base_run import ThreadRun, TruncationStrategy
from hepai.agents.modules.managers.base_pages import CursorPage
from hepai.agents.utils import Logger, EventCollector

logger = Logger.get_logger("threads_manager.py")

class ThreadsManager(BaseJsonSaver):
    """
    离线存储所有的线程
    """

    version = "1.0.0"
    metadata = {
        "description": "Thread is conversation session between user and AI assistant, the ThreadsManages is used to store all threads",
        "mapping_username2indexes": {},  # 用来存储用户名到线程索引的映射，方便快速查找
        }

    def __init__(
        self,
        file_name: str = f'threads.json',
        file_dir: str = f'{Path.home()}/.{__appname__}',
        **kwargs
        ) -> None:
        super().__init__(auto_save=True, **kwargs)

        self.file_path = os.path.join(file_dir, file_name)
        self._data = self._init_load(self.file_path, version=self.version, metadata=self.metadata)

        self.message_save_dir = f"{file_dir}/thread_messages"
        self.run_save_dir = f"{file_dir}/thread_runs"
        if not os.path.exists(self.message_save_dir):
            os.makedirs(self.message_save_dir)
        if not os.path.exists(self.run_save_dir):
            os.makedirs(self.run_save_dir)

        self.alive_threads = dict()
        ## TODO: 新建的thread保存到内存中，方便快速查找，减少磁盘IO，thread被访问时，更新时间，超时的线程删除

    def save_messages_to_disk(self, file_path: str, messages: List[str | ThreadMessage]):
        """
        保存数据到硬盘，如果数据已经存在，不覆盖
        """
        # if os.path.exists(file_path):
        #     return
        if not messages:  # messages为空，不需要保存
            return
        if isinstance(messages[0], str):
            # 在一个线程上的一个message是str，表示其未被加载，不需要保存
            return
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            for message in messages:
                msg_dict = message.to_dict(only_output_keys=True)
                f.write(json.dumps(msg_dict) + '\n')
        logger.debug(f"Messages saved to `{Path(file_path).relative_to(self.message_save_dir)}`")

    def save_runs_to_disk(self, file_path: str, run: List[str | ThreadRun]):
        # if os.path.exists(file_path):  # 如果文件已经存在，不覆盖，这个不对，一个线程的数据可能更新
        #     return
        if not run:  # run为空，不需要保存
            return
        if isinstance(run[0], str):
            # 在一个线程上的一个run是str，表示其未被加载，不需要保存
            return
        
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            for run in run:
                run_dict = run.to_dict(only_output_keys=True)
                f.write(json.dumps(run_dict) + '\n')
        logger.debug(f"Runs saved to `{Path(file_path).relative_to(self.run_save_dir)}`")
        pass

    def save(self, file_path: str = None, data: dict = None, username=None, **kwargs):
        """
        单个thread的对象里可能存在runs和message对象
        无法直接序列化到json文件里，需要单独保存到硬盘中。
        Args:
            username: str, optional. The username of the thread owner.
        """
        data = data or self.data

        entities = data.get("entities", [])
        if username:
            entities = [x for x in entities if x.get("username") == username]

        for entity in entities:
            messages = entity.pop("messages", [])
            runs = entity.pop("runs", [])

            thread_id = entity["id"]
            username = entity["username"]

            # 单独保存message
            if len(messages) > 0:
                if isinstance(messages[0], str):
                    msg_ids = messages
                else:
                    msg_ids = [msg.id for msg in messages]
            else:
                msg_ids = []
            entity["messages"] = msg_ids
            msg_save_path = f"{self.message_save_dir}/{username}/messages_of_{thread_id}.jsonl"
            self.save_messages_to_disk(msg_save_path, messages)
        
            # 单独保存run
            if len(runs) > 0:
                if isinstance(runs[0], str):
                    run_ids = runs
                else:
                    run_ids = [run.id for run in runs]
            else:
                run_ids = []
            entity["runs"] = run_ids
            run_save_path = f"{self.run_save_dir}/{username}/runs_on_{thread_id}.jsonl"
            self.save_runs_to_disk(run_save_path, runs)

        return super().save(file_path=file_path, data=data)

    ### --- Threads --- ###
    def create_threads(self, username=None, **kwargs):
        """
        创建一个线程
        {
        "id": "thread_abc123",
        "object": "thread",
        "created_at": 1699012949,
        "metadata": {},
        "tool_resources": {}
        }
        """
        username = username or self.DEFAULT_USERNAME
        save_immediately = kwargs.get('save_immediately', False)
        messages: List[Dict] = kwargs.get('messages', [])
        tool_resources: List = kwargs.get('tool_resources', {})
        metadata: Dict = kwargs.get('metadata', {})

        # thread_id = self.auto_id(prefix='thread_', length=30)
        # 使用openwebui的chat_id作为thread_id
        chat_id = kwargs.get('chat_id', None)
        if chat_id:
            thread_id = 'thread_'+chat_id
        else:
            thread_id = self.auto_id(prefix='thread_', length=30)
            
        try:
        #    thread = self.alive_threads[thread_id]
        #    return thread
            return self.get_thread(thread_id, username=username)
        except:
            order_ids = [int(x['order_id']) for x in self.entities]
            order_id = int(max(order_ids)) if order_ids else 0
            order_id = f'{order_id+1:0>8}'

        metadata["Stream_status"] = "thread_start"

        thread = Thread(
            id=thread_id,
            object="thread",
            created_at=int(time.time()),
            metadata=metadata,
            tool_resources=tool_resources,
            username=username,
            order_id=order_id
        )

        if messages:
            raise NotImplementedError("Creating thread with messages is not supported yet.")
        self.append_entity(thread, username=username, save_immediately=save_immediately)
        self.alive_threads[thread_id]=thread
        return thread
        
    def load_messages_from_disk(self, file_path: str) -> List[ThreadMessage]:
        """
        从硬盘读取数据并转为List[ThreadMessage]
        """
        if not os.path.exists(file_path):
            return []  # 文件不存在，返回空列表

        messages = []
        with open(file_path, 'r') as f:
            for line in f:
                msg_dict = json.loads(line.strip())  # 将一行JSON字符串解析为字典
                message = ThreadMessage(**msg_dict)  # 根据字典创建ThreadMessage实例
                content = Content(
                    type="text",
                    text=Text(
                        value=msg_dict["content"][0]["text"]["value"], 
                        annotations=[]
                    ))
                message.content = [content]
                messages.append(message)
        
        logger.debug(f"Messages loaded from `{file_path}`")
        return messages
    
    def get_thread(self, thread_id, username=None, return_index=False):
        """从json文件获取线程"""
        if username:  # 提供用户名，缩小搜搜范围，搜索的快
            threads_indexes = self.data["metadata"]["mapping_username2indexes"].get(username, [])
            if not threads_indexes:
                raise ModuleNotFoundError(f"No thread found for user `{username}`")
        else:
            threads_indexes = list(range(len(self.entities)))
            if not threads_indexes:
                raise ModuleNotFoundError(f"No thread found")
        
        filtered = [(self.entities[idx], idx) for idx in threads_indexes if self.entities[idx]['id'] == thread_id]
        if not filtered:
            raise ModuleNotFoundError(f"No thread found for user `{username}` and id `{thread_id}`")
        threads, indexes = zip(*filtered)
        if not threads:
            raise ModuleNotFoundError(f"Thread not found, id: `{thread_id}`")
        if len(threads) > 1:
            raise ValueError(f"Multiple threads found, id: `{thread_id}`")
        thread = Thread(**threads[0])
        if len(thread.messages)>0:
            if isinstance(thread.messages[0],str):
                # 如果是从json文件中回复的，message=str，需要从硬盘加载message
                msg_save_path = f"{self.message_save_dir}/{username}/messages_of_{thread_id}.jsonl"
                messages = self.load_messages_from_disk(msg_save_path)
                thread.messages = messages
        if thread.deleted:
            raise ModuleNotFoundError(f"Thread has been deleted, id: `{thread_id}`")
        if return_index:
            assert len(indexes) == 1, f"Multiple threads found, id: `{thread_id}`"
            return thread, indexes[0]
        return thread

    def retrieve_thread(self, thread_id, username=None, **kwargs):
        """
        获取线程
        """
        return self.get_thread(thread_id, username=username, **kwargs)

    
    def update_thread(self, thread_id, username=None, **kwargs):
        save_immediately = kwargs.pop('save_immediately', False)
        thread, idx = self.get_thread(thread_id, username=username, return_index=True)

        # 还需自动更新是否修改的标识和谁更新的，存储到metadata中
        thread.update(auto_metadata=True, **kwargs)
        self.update_entity(thread, idx, save_immediately=save_immediately)
        return thread
    
    def delete_thread(self, thread_id, username=None, permanent=False, **kwargs):
        """
        Delete a thread
        Args:
            thread_id: str, required
            username: str, optional. Boost the search speed by providing the username.
            permanent: bool, optional. If True, the thread will be permanently deleted. Default is False.
        """
        save_immediately = kwargs.get('save_immediately', False)
        permanent = True if permanent == 'true' else False  # fit webui query
        if not permanent:  # 软删除，只标记为删除
            asst = self.update_thread(thread_id, username=username, deleted=True, save_immediately=save_immediately)
            assert asst.deleted, "Thread not deleted"
        else:
            asst, idx = self.get_thread(thread_id, username=username, return_index=True)
            self.remove_entity(asst, idx, save_immediately=save_immediately)
        return ThreadDeleted(id=thread_id, object="thread.deletec", deleted=True)
    
    ### --- Messages --- ###
    def get_message(self, thread_id, message_id, username=None):
        """Get message from thread"""
        thread = self.get_thread(thread_id, username=username)
        messages = thread.messages
        filtered = [msg for msg in messages if msg.id == message_id]
        if not filtered:
            raise ModuleNotFoundError(f"No message found for thread `{thread_id}` and id `{message_id}`")
        if len(filtered) > 1:
            raise ValueError(f"Multiple messages found, id: `{message_id}`")
        return filtered[0]
    
    def update_message(self, thread_id, message_id, username=None, **kwargs):
        """
        Update a message in a thread
        """
        message: ThreadMessage = self.get_message(thread_id, message_id, username=username)

        message.update(auto_metadata=True, **kwargs)

        # TODO: 保存到文件
        return message
        
    def retrieve_message(self, thread_id: str, message_id: str, username=None, **kwargs):
        """
        Retrieve a message from a thread
        """
        return self.get_message(thread_id, message_id, username=username, **kwargs)

    def list_messages(
            self,
            thread_id: str,
            limit: int = 20,
            order: str = 'desc',
            after: str = None,
            before: str = None, 
            run_id: str = None,
            username: str = None,
            **kwargs
        ) -> List[Dict]:
        """
        list messages of a thread
        :param thread_id: str, thread id, required
        :param limit: int, optinal. A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 20.
        :param order: str, optinal. Sort order by the created_at timestamp of the objects. asc for ascending order and desc for descending order.
        :param after: str, optinal. A cursor for use in pagination. after is an object ID that defines your place in the list. For instance, if you make a list request and receive 100 objects, ending with obj_foo, your subsequent call can include after=obj_foo in order to fetch the next page of the list.
        :param before: str, optinal. A cursor for use in pagination. before is an object ID that defines your place in the list. For instance, if you make a list request and receive 100 objects, starting with obj_bar, your subsequent call can include before=obj_bar in order to fetch the previous page of the list.
        :praam run_id: str, optinal. Filter messages by the run ID that generated them.
        :param username: str, optinal. Boost the search speed by providing the username.
        """
        return_format = kwargs.get('return_format', Dict)

        thread = self.get_thread(thread_id, username=username)
        messages = thread.messages

        if run_id:  # 过滤run_id
            messages = [msg for msg in messages if msg.run_id == run_id]

        reverse = True if order == 'desc' else False
        messages = sorted(messages, key=lambda x: x.created_at, reverse=reverse)  # 默认升序
        if after:  # 其后的
            raise NotImplementedError("Pagination is not supported yet.")
            # cursor = [msg.id for msg in messages].index(after)
            # messages = [msg for msg in messages if msg.id > after]
        if before:  # 其前的
            raise NotImplementedError("Pagination is not supported yet.")
        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]
        
        if len(messages) == 0:
            res = {
                "object": "list",
                "data": messages,
                "first_id": None,
                "last_id": None,
                "has_more": False,
            }
        else:
            res = {
                "object": "list",
                "data": messages,
                "first_id": messages[0].id,
                "last_id": messages[-1].id,
                "has_more": has_more,
            }
        if return_format in [Dict, dict, 'dict', 'Dict']:
            return res
        return CursorPage(**res)
    
   # 接收前端封装的消息，并打包成ThreadMessage，其中content需要进行格式判断
    def create_message(
            self, 
            thread: str | Thread, 
            role, 
            content, 
            **kwargs) -> ThreadMessage:
        """
        Create a message in a thread, auto append to the thread.
        Args:
            thread: str | Thread, required. Thread ID or Thread object.
            role: str, required. The role of the sender, can be 'user', 'assistant', 'system'.
            content: str, required. The content of the message.
            save_immediately: bool, optional. If True, save the message immediately. Default is False.
        """
        save_immediately = kwargs.get('save_immediately', False)
        stream = kwargs.get('stream', False)
        evc: EventCollector = kwargs.get('event_collector', None)
        username = kwargs.get('username', None)
        # NOTE: 这里不知道为啥非得限定'user', 'assistant', 'system'三个角色，请问是为了什么？这里进行了删除
        # assert role in ['user', 'assistant', 'system'], f"Invalid role: {role}"
        message_id = self.auto_id(prefix='msg_', length=30, deduplicate=False)

        if isinstance(thread, str):  
            thread: Thread = self.get_thread(thread, username=username)
        if thread.locked:
            raise ValueError(f"Thread `{thread.id}` is locked, cannot add new message.")
        
        logger.debug(f"Creating message in thread `{thread.id}` with role `{role}`")
        
        order_ids = [x.get("order_id") for x in thread.messages]
        order_id = int(max(order_ids))+1 if order_ids else 1
        order_id = f'{order_id:0>8}'

        if isinstance(content, str):
            content = [
                Content(
                    type="text",
                    text=Text(
                        value=content, 
                        annotations=kwargs.get('annotations', [])
                    )),
                ]
        elif isinstance(content, List):
            for i in range(len(content)):
                content[i]=Content(
                    type="text",
                    text=Text(
                        value=content[i].text.value, 
                        annotations=kwargs.get('annotations', [])
                    ))

        else:
            content = content

        thread_message = ThreadMessage(
            id=message_id,
            object="thread.message",
            created_at=int(time.time()),
            assistant_id=kwargs.get('assistant_id', None),
            thread_id=thread.id,
            run_id=kwargs.get('run_id', None),
            role=role,
            content=content,
            order_id=order_id,
            attachments=kwargs.get('attachments', []),
            metadata=kwargs.get('metadata', {}),
            sender=kwargs.get('sender', None),
            task_type=kwargs.get('task_type', None),
            )
        
        thread.messages.append(thread_message)
        thread_message.thread = thread  # 交叉引用

        if evc and stream:
            evc.add_event_source(thread_message.event_generator())
            thread_message.set_status("created", emit=True)

        return thread_message
    
    
        
    ### --- Runs --- ###
    async def a_create_runs(self, thread_id, assistant_id, **kwargs):
        """
        20240522，协程函数调用调试未通过
        """
        events_collector = kwargs.get('events_collector', None)
        run = await self.create_runs(thread_id, assistant_id, **kwargs)
        
        if events_collector:
            events_collector.append(self.run_created_event(run))
        return run

    def run_created_event(self, run):
        data = {
            "data": run.to_dict(),
            "event": "thread.run.created"
        }
        yield f"data: {json.dumps(data)}\n\n"

    def create_runs_stream(self, thread_id, assistant_id, **kwargs):
        thread_run = self.create_runs(thread_id, assistant_id, **kwargs)
        thread_run.set_status("created", emit=True)
        return thread_run, thread_run.event_generator()
        
    def create_runs(self, thread_id, assistant_id, **kwargs):
        """
        Create a run
        """
        save_immediately = kwargs.get('save_immediately', False)
        username = kwargs.get('username', None)

        thread: Thread = self.get_thread(thread_id, username=username)
        
        run_id = self.auto_id(prefix='run_', length=30, deduplicate=False)
        thread_run = ThreadRun(
            id=run_id,
            object="thread.run",
            created_at=int(time.time()),
            assistant_id=assistant_id,
            thread_id=thread.id,
            status="queued",
            started_at=None,
            expires_at=None,
            cancelled_at=None,
            failed_at=None,
            completed_at=None,
            last_error=None,
            model=kwargs.get('model', CONST.DEFAULT_MODEL),
            instructions=kwargs.get('instructions', None),
            incomplete_details=None,
            tools=kwargs.get('tools', []),
            metadata={},
            usage=None,
            temperature=kwargs.get('temperature', 0.6),
            top_p=kwargs.get('top_p', 1),
            max_prompt_tokens=1000,
            max_completion_tokens=1000,
            truncation_strategy=TruncationStrategy(type="auto", last_messages=None),
            response_format="auto",
            tool_choice="auto",
            username=thread.username,
        )

        # 交叉引用
        thread.runs.append(thread_run)  # 把run添加到线程中
        thread_run.thread = thread  # 把线程添加到run中
            
        return thread_run
    
    def get_run(self, thread_id, run_id, username=None):
        thread = self.get_thread(thread_id, username=username)
        runs = thread.runs
        filtered = [run for run in runs if run.id == run_id]
        if not filtered:
            raise ModuleNotFoundError(f"No run found for thread `{thread_id}` and id `{run_id}`")
        if len(filtered) > 1:
            raise ValueError(f"Multiple runs found, id: `{run_id}`")
        return filtered[0]

    def retrieve_run(self, thread_id, run_id, username=None, **kwargs):
        """
        Retrieve a run
        """
        return self.get_run(thread_id, run_id, username=username, **kwargs)
        

if __name__ == "__main__":
    tm = ThreadsManager()
    
    # 创建
    thread = tm.create_threads()
    print(f'Created thread: {thread}')

    # 获取
    my_thread = tm.retrieve_thread(thread.id)
    print(f'Retrieved thread: {my_thread}')
    assert my_thread.id == thread.id, "Thread ID not match"

    # 修改
    up_thread = tm.update_thread(thread.id, 
        metadata={'description': 'This is updated description'},
        )
    print(f'Updated thread: {up_thread}')
    assert up_thread.metadata['description'] == 'This is updated description', "Thread metadata not updated"
    assert up_thread.metadata['modified'], "Thread metadata not updated"

    # 删除
    # del_thread = tm.delete_thread(thread.id, permanent=True)
    # print(f'Deleted thread: {del_thread}')
    # assert del_thread.deleted, "Thread not deleted"

    message = tm.create_message(
        thread_id=thread.id, role='user', 
        content="How does AI work? Explain it in simple terms.")
    print(f"Created message: {message}")

    listed_messages = tm.list_messages(thread_id=thread.id)
    print(f"Listed messages: {listed_messages}")

    retrieved_message = tm.retrieve_message(thread_id=thread.id, message_id=message.id)
    print(f"Retrieved message: {retrieved_message}")

    up_message = tm.update_message(
        thread_id=thread.id, message_id=message.id, 
        content="How does AI work? Explain it in simple terms2.")
    print(f"Updated message: {up_message}")
    assert up_message.content == "How does AI work? Explain it in simple terms2.", "Message content not updated"
    assert up_message.metadata['modified'], "Message metadata not updated"

    #### Runs ####
    asst_id = "asst_39930f61c6574f139e1bca090"
    thread_run = tm.create_runs(thread_id=thread.id, assistant_id=asst_id)
    print(f"Created run: {thread_run}")

    pass
