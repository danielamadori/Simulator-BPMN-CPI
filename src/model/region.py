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


# class Task(BaseModel):
#     id: str
#     type: RegionType
#     label: str
#     impacts: List[float]
#     duration: float


class RegionModel(BaseModel):
    """
    Classe che rappresenta i dati ricevuti dal client
    """

    id: str
    type: RegionType
    label: str | None = None
    duration: float = 0
    children: List[RegionModel] | None = None
    distribution: List[float] | None = None
    impacts: List[float] | None = None

    def is_parallel(self):
        return self.type == RegionType.PARALLEL

    def is_choice(self):
        return self.type == RegionType.CHOICE

    def is_sequential(self):
        return self.type == RegionType.SEQUENTIAL

    def is_nature(self):
        return self.type == RegionType.NATURE

    def is_task(self):
        return self.type == RegionType.TASK

    def has_child(self):
        if self.children is None:
            return False

        return len(self.children) != 0
