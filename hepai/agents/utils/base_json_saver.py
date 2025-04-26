
from typing import List
import os
import json
import uuid
from dataclasses import dataclass, field
import atexit
import schedule

import damei as dm
logger = dm.get_logger("base_json_saver.py")


class BaseJsonSaver:
    """
    提供一些基础操作本地某个特定Json文件的方法
    """
    file_path = None
    data = None
    version = "1.0.0"
    metadata = {}
    DEFAULT_USERNAME = "anonymous"


    def __init__(
        self, 
        auto_save: bool = False, 
        auto_save_interval: int = 10,  # 10 minutes
        debug: bool = False,
        **kwargs
        ) -> None:
        self._data = None
        self.dirty = False  # 是否有数据更新
        self.debug = debug

        if auto_save:
            atexit.register(self.check_and_save)
            # schedule.every(auto_save_interval).minutes.do(self.check_and_save)
            schedule.every(auto_save_interval).seconds.do(self.check_and_save)
            # schedule.run_all()

    @property
    def data(self):
        return self._data

    @property
    def metadata(self):
        return self._data["metadata"]
    
    @property
    def entities(self):
        return self._data.get("entities", {})
    
    @property
    def ids(self):
        ids = list(set([x.get('id', None) for x in self.entities]))
        return ids
        

    def _init_load(self, file_path: str, **kwargs):
        """
        从本地加载数据
        """
        if not os.path.exists(file_path):
            version = kwargs.get("version", self.version)
            metadata = kwargs.get("metadata", self.metadata)
            data = {
                "version": version,
                "metadata": metadata,
                "entities": []
            }
            # save
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            self.save(file_path, data)
            return data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data

    def check_and_save(self, username=None, **kwargs):
        logger.debug("Check and save")
        if self.dirty:
            self.save(username=username, **kwargs)
    
    def save(self, file_path: str = None, data: dict = None, **kwargs):
        """
        save data to file
        """
        file_path = file_path or self.file_path
        data = data or self.data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.debug(f"Data saved to {file_path}")
        self.dirty = False
        return True
    
    def auto_id(self, prefix: str = '', length: int = 30, deduplicate: bool | List = True):
        """
        自动生成一个20位的id。
        """
        new_id = uuid.uuid4().hex
        short_id = str(new_id).replace('-', '')
        short_id = prefix + short_id[:length-len(prefix)]
        if deduplicate:
            if isinstance(deduplicate, list):
                if short_id in deduplicate:
                    return self.auto_id()
            else:
                if short_id in self.ids:  # 如果已经存在，则重新生成
                    return self.auto_id()
        return short_id
    
    def remove_entity(self, entity: dict | object, index: int, save_immediately: bool = False):
        """永久删除一个实体，并更新映射关系"""
        if not isinstance(entity, dict):
            entity = entity.to_dict()
        poped_entity = self.entities.pop(index)
        assert poped_entity.get('id') == entity.get('id'), "poped_entity.id must equal to entity.id"
       
        # 更新映射关系
        new_mapping = dict()
        for i, ent in enumerate(self.entities):
            username = ent.get('username', self.DEFAULT_USERNAME)
            if username not in new_mapping:
                new_mapping[username] = [i]
            else:
                new_mapping[username].append(i)
        self.data["metadata"]["mapping_username2indexes"] = new_mapping
            
        if save_immediately:
            self.save()
            return
        self.dirty = True
    
    def update_entity(self, entity: dict | object, index: int, save_immediately: bool = False):
        """
        更新一个实体
        """
        if not isinstance(entity, dict):
            entity = entity.to_dict()
        assert entity.get("id", None) is not None, "entity must have an id"
        self.entities[index] = entity
        if save_immediately:
            self.save()
            return
        self.dirty = True


    def append_entity(self, entity: dict | object, username=None, save_immediately: bool = False):
        """
        添加一个实体
        """
        if not isinstance(entity, dict):
            entity = entity.to_dict()
        assert entity.get("id", None) is not None, "entity must have an id"
        assert entity.get('id') not in self.ids, "id must be unique"
        self.entities.append(entity)

        # 保存映射关系，便于快速查找
        username = username or self.DEFAULT_USERNAME
        current_index = len(self.entities) - 1
        old_indexes =self.data["metadata"]["mapping_username2indexes"].get(username, [])
        assert current_index not in old_indexes, "current_index must not in old_indexes"
        new_indexes = old_indexes + [current_index]
        self.data['metadata']['mapping_username2indexes'][username] = new_indexes
        
        if save_immediately:
            self.save()
            return
        self.dirty = True  # 标记为脏数据，以便自动保存



