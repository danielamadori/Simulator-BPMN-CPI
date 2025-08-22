from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.types import MarkingType

'''
Secondo me si può spostare anche dentro extree
'''


# Snapshot è la struttura del nodo dell'albero
class Snapshot:
    __marking: MarkingType
    __probability: float
    __impacts: list[float]
    __exec_time: float

    def __init__(self, marking: MarkingType, probability: float, impacts: list[float], time: float):
        self.__marking = marking
        self.__probability = probability
        self.__impacts = impacts
        self.__exec_time = time

    @property
    def marking(self) -> MarkingType:
        return copy(self.__marking)

    @property
    def probability(self) -> float:
        return self.__probability

    @property
    def impacts(self) -> list[float]:
        return copy(self.__impacts)

    @property
    def execution_time(self) -> float:
        return self.__exec_time

    def __eq__(self, other) -> bool:
        if not isinstance(other, Snapshot):
            return False

        if other.__marking != self.__marking:
            return False
        if other.__impacts != self.__impacts:
            return False
        if other.__probability != self.__probability:
            return False
        if other.__exec_time != self.__exec_time:
            return False

        return True
