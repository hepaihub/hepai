"""
用来管理不同的用户所创建的助手的类
"""
import os, sys
from pathlib import Path
here = Path(__file__).parent
import time

try:
    from hepai.agents.version import __version__
except:
    sys.path.insert(1, f'{here.parent.parent.parent}')
    from hepai.agents.version import __version__
from hepai.agents.utils import BaseJsonSaver, Logger
from hepai.agents.version import __appname__

from .base_assistant import Assistant, Tool, AssistantDeleted

logger = Logger.get_logger("assistants_manager.py")

class AssistantsManager(BaseJsonSaver):
    """
    离线存储所有的AI助手
    """

    version = "1.0.0"
    metadata = {
        "description": "AI assistants manager of all users",
        "mapping_username2indexes": {},  # 用来存储用户名到线程索引的映射，方便快速查找
    }
    
    def __init__(self,
        file_name: str = f'assistants.json',
        file_dir: str = f'{Path.home()}/.{__appname__}',
        **kwargs
        ) -> None:
        super().__init__(auto_save=True, **kwargs)

        self.file_path = os.path.join(file_dir, file_name)

        self._data = self._init_load(self.file_path, version=self.version, metadata=self.metadata)
        pass


    def get_assistant(self, assistant_id, username=None, return_index=False):
        """获取助手"""
        if username:
            assts_indexes = self.data["metadata"]["mapping_username2indexes"].get(username, [])
            if not assts_indexes:
                raise ModuleNotFoundError(f"No assistant found for user `{username}`")
        else:
            assts_indexes = list(range(len(self.entities)))
            if not assts_indexes:
                raise ModuleNotFoundError(f"No assistant found")
        filtered = [(self.entities[idx], idx) for idx in assts_indexes if self.entities[idx]['id'] == assistant_id]
        if not filtered:
            raise ModuleNotFoundError(f"No assistant found for user `{username}` and id `{assistant_id}`")
        assts, indexes = zip(*filtered)
        if not assts:
            raise ModuleNotFoundError(f"Assistant not found, id: `{assistant_id}`")
        if len(assts) > 1:
            raise ValueError(f"Multiple assistants found, id: `{assistant_id}`")
        asst = Assistant(**assts[0])
        if asst.deleted:
            raise ModuleNotFoundError(f"Assistant has been deleted, id: `{assistant_id}`")
        if return_index:
            assert len(indexes) == 1, f"Multiple assistants found, id: `{assistant_id}`"
            return asst, indexes[0]
        return asst


    def create_assistant(self, model, username=None, **kwargs):
        """
        返回值：
        ```json
        {
            "id": "asst_gbPJLxkrpsawUo9opT7SZh2O",
            "object": "assistant",
            "created_at": 1714452287,
            "name": "Math Tutor",
            "description": null,
            "model": "gpt-4-turbo",
            "instructions": "You are a personal math tutor. Write and run code to answer math questions.",
            "tools": [{
                "type": "code_interpreter"
                }],
            "top_p": 1.0,
            "temperature": 1.0,
            "file_ids": [],
            "metadata": {},
            "response_format": "auto"
            }'
        """
        username = username or self.DEFAULT_USERNAME
        id = self.auto_id(prefix='asst_', length=30)

        # order_id = f'{len(self.entities)+1:0>6}'  # 这个不对
        order_ids = [x['order_id'] for x in self.entities]
        order_id = f'{int(max(order_ids))+1:0>6}' if order_ids else '000001'
        
        asst = Assistant(
            id=id,
            object="assistant",
            created_at=int(time.time()),
            name=kwargs.get('name', None),
            description=kwargs.get('description', None),
            model=model,
            instructions=kwargs.get('instructions', None),
            tools=kwargs.get('tools', []),
            tool_resources=kwargs.get('tool_resources', {}),
            top_p=kwargs.get('top_p', 1),
            temperature=kwargs.get('temperature', 0.6),
            # file_ids=kwargs.get('file_ids', []),
            metadata=kwargs.get('metadata', {}),
            response_format=kwargs.get('response_format', 'auto'),

            username=username,
            order_id=order_id
        )
        self.append_entity(asst, username=username, save_immediately=False)

        # 保存的和输出的数据可能不一样
        return asst
        # return self.fit_output(obj, **kwargs)

    def delete_assistant(self, assistant_id, username=None, **kwargs):
        """删除助手"""
        save_immediately = kwargs.pop('save_immediately', False)
        permanent = kwargs.pop('permanent', False)  # 是否永久删除
        permanent = True if permanent == 'true' else permanent  # 适配restful api
        if not permanent:  # 软删除，添加deleted标记
            asst = self.update_assistant(
                assistant_id, username=username, deleted=True,
                save_immediately=save_immediately
                )
            assert asst.deleted, "Assistant not deleted"
        else:
            asst, idx = self.get_assistant(assistant_id, username=username, return_index=True)
            self.remove_entity(asst, idx, save_immediately=save_immediately)

        return AssistantDeleted(
            id=asst.id,
            object="assistant.deleted",
            deleted=True,
        )
    
    def update_assistant(self, assistant_id, username=None, **kwargs):
        """更新助手"""
        save_immediately = kwargs.pop('save_immediately', False)
        asst, idx = self.get_assistant(assistant_id, username=username, return_index=True)
        asst.update(**kwargs)  # 更新类属性

        # 更新到数据库
        self.update_entity(asst, idx, save_immediately=save_immediately)

        # logger.debug(f"asst: {asst}")
        return asst

    def retrieve_assistant(self, assistant_id, username=None, **kwargs):
        """获取模型"""
        return self.get_assistant(assistant_id, username=username, **kwargs)
    
    def list_assistants(self, username, limit=20, order='desc', after=None, before=None):
        """
        list assistants of a user
        {
        "object": "list",
        "data": [
            {
            "id": "asst_abc123",
            "object": "assistant",
            "created_at": 1698982736,
            "name": "Coding Tutor",
            "description": null,
            "model": "gpt-4-turbo",
            "instructions": "You are a helpful assistant designed to make me better at coding!",
            "tools": [],
            "tool_resources": {},
            "metadata": {},
            "top_p": 1.0,
            "temperature": 1.0,
            "response_format": "auto"
            },
            ...
            ],
        "first_id": "asst_abc123",
        "last_id": "asst_abc789",
        "has_more": false
        }
        """
        if after:
            raise NotImplementedError(f"`after` param is not supported yet in version {__version__}")
        if before:
            raise NotImplementedError(f"`before` param is not supported yet in version {__version__}")

        assts_indexes = self.data["metadata"]["mapping_username2indexes"].get(username, [])
        assts = [self.entities[idx] for idx in assts_indexes]
        assts = [Assistant(**x) for x in assts]
        assts = [x for x in assts if not x.deleted]
        reverse = True if order == 'desc' else False
        # assistants = sorted(assistants, key=lambda x: x['created_at'], reverse=reverse)
        assts = sorted(assts, key=lambda x: x.created_at, reverse=reverse)
        has_more = len(assts) > limit
        if has_more:
            assts = assts[:limit]
        if len(assts) == 0:
            # raise ModuleNotFoundError(f"No assistant found for user `{username}`")
            return {
                "object": "list",
                "data": assts,
                "first_id": None,
                "last_id": None,
                "has_more": False,
            }

        return {
            "object": "list",
            "data": assts,
            "first_id": assts[0].id,
            "last_id": assts[-1].id,
            "has_more": has_more,
        }
        

if __name__ == "__main__":
    am = AssistantsManager(debug=True)

    # 增加
    my_asst = am.create_assistant(
        name='Dr.Sai-Primary', username='anonymous', model='gpt-4-turbo',
        save_immediately=True
        )
    print(f'my_asst: {my_asst}')

    # list
    listed_assts = am.list_assistants(
        username='anonymous', limit=20, order='desc')
    print(f'listed_assts: {listed_assts}')

    # 更新
    up_asst = am.update_assistant(
        assistant_id=my_asst.id, 
        username='anonymous', name='Dr.Sai-Primary-Updated')
    print(f'up_asst: {up_asst}')

    # 获取
    my_asst2 = am.retrieve_assistant(assistant_id=my_asst.id)
    print(f'my_asst2: {my_asst2}')

    # 删除
    del_asst = am.delete_assistant(assistant_id=my_asst.id, permanent=True)
    print(f'del_asst: {del_asst}')

