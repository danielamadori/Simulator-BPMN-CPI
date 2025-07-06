from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel


class RegionType(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    NATURE = "nature"
    CHOICE = "choice"
    TASK = "task"
    LOOP = "loop"

class RegionModel(BaseModel):
    """
    Classe che rappresenta i dati ricevuti dal client
    """

    id: str
    type: RegionType
    label: str | None = None
    duration: float = 0
    children: List[RegionModel] | None = None
    distribution: List[float] | float | None = None
    impacts: List[float] | None = None

    def is_parallel(self) -> bool:
        return self.type == RegionType.PARALLEL

    def is_choice(self) -> bool:
        return self.type == RegionType.CHOICE

    def is_sequential(self) -> bool:
        return self.type == RegionType.SEQUENTIAL

    def is_nature(self) -> bool:
        return self.type == RegionType.NATURE

    def is_task(self) -> bool:
        return self.type == RegionType.TASK

    def is_loop(self) -> bool:
        return self.type == RegionType.LOOP

    def has_child(self) -> bool:
        if self.children is None:
            return False

        return len(self.children) != 0


def find_region_by_id(root: RegionModel, _id: str) -> RegionModel | None:
    if root.id == _id:
        return root

    if not root.children:
        return None

    for c in root.children:
        _next = find_region_by_id(c, _id)
        if _next:
            return _next

    return None
