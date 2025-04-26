

from typing import List, Dict, Any
from dataclasses import dataclass, field

@dataclass
class CursorPage:
    """
    Generic cursor-based pagination class
    """
    object: str
    data: List[any]
    first_id: str = None
    last_id: str = None
    has_more: bool = False

