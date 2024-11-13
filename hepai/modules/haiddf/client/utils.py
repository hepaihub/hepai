
import os
from typing import Any, Dict, Union, List
from dataclasses import dataclass

from functools import wraps
import httpx
from .resources._base_resource import HErrorResponse

def parse_data_to_class_deprecated(data: Dict[str, Any], target_class: Any):
    """
    Parses data into an instance of the target class.
    
    :param data: Dictionary containing the data.
    :param target_class: The class to which the data is to be parsed.
    :return: An instance of target_class initialized with the data.
    """
    # Filter the data dictionary to only include keys that are in the target class
    filtered_data = {
        key: value for key, value in data.items() if key in target_class.__annotations__
    }
    
    # Handle nested dataclasses if needed
    for field_name, field_type in target_class.__annotations__.items():
        # if isinstance(filtered_data.get(field_name), List):
        #     ## List内可能还有Dict
        #     inner_type = getattr(field_type, '__args__', [Any])[0]

        #     pass
        if isinstance(filtered_data.get(field_name), dict) and hasattr(field_type, '__dataclass_fields__'):
            filtered_data[field_name] = parse_data_to_class_deprecated(filtered_data[field_name], field_type)

    # Creating an instance of the target class with the filtered data
    return target_class(**filtered_data)

def parse_data_to_class(data: Dict[str, Any], target_class: Any):
    """
    Parses data into an instance of the target class.
    
    :param data: Dictionary containing the data.
    :param target_class: The class to which the data is to be parsed.
    :return: An instance of target_class initialized
    with the data.
    """
    return target_class(**data)

def post_process_decorator(func) -> Union[str, Dict, HErrorResponse]:
    """
    Dealing with the response of http request
    
    Args:
        cast_to: The class to which the data is to be parsed.
    """
    dev_mode = os.getenv("DEV_MODE", False)

    @wraps(func)
    def wrapper(*args, **kwargs):
        cast_to = kwargs.pop("cast_to", None)
        ignore_error = kwargs.pop("ignore_error", False)

        response: httpx.Response = func(*args, **kwargs)
        if response.status_code == 200:
            try:
                rst = response.json()
            except ValueError:
                # If JSON decoding fails, return the text content
                return response.text
            if cast_to is None:
                return rst
            else:
                # 将Json数据转换为指定的数据类
                return parse_data_to_class(rst, cast_to)
        elif response.status_code == 500:
            raise HErrorResponse(
                status_code=response.status_code,
                message=response.reason_phrase or "Unknown error",
                content=response.text
            )
        else:

            if dev_mode and not ignore_error:  # 如果debug, 就在这里直接报错
                # Construct an HErrorResponse and raise it
                raise HErrorResponse(
                    status_code=response.status_code,
                    message=response.reason_phrase or "Unknown error",
                    content=response.text
                )
            # Construct an HErrorResponse and return it
            return HErrorResponse(
                status_code=response.status_code,
                message=response.reason_phrase or "Unknown error",
                content=response.text
            )
    return wrapper
