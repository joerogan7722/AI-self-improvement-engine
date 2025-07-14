from typing import Literal, Optional, TypedDict


class Todo(TypedDict, total=False):
    file_path: str
    change_type: Literal["add", "modify", "delete"]
    description: str
    line_start: Optional[int]
    line_end: Optional[int]
