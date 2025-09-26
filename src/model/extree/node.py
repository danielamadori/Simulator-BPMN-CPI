#  Copyright (c) 2025.
from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING

from anytree import NodeMixin

if TYPE_CHECKING:
    from model.types import MarkingType


class Snapshot:
    """
    Snapshot of a Petri net at a specific state during execution.

    Attributes:
        marking (MarkingType): The current marking of the Petri net.
        probability (float): The probability of reaching this marking.
        impacts (list[float]): The impacts associated with this marking.
        execution_time (float): The time taken to reach this marking.
    """
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


class NodeAttributes:

    snapshot: Snapshot

    def __init__(self, snapshot: Snapshot):
        self.snapshot = snapshot


class ExecutionTreeNode(NodeAttributes, NodeMixin):
    """
    Node in the execution tree representing a state in the execution of a Petri net.

    Attributes:
        name (str): Name of the node.
        id (str): Unique identifier for the node.
        snapshot (Snapshot): Snapshot of the Petri net at this node.
        parent (ExecutionTreeNode | None): Parent node in the execution tree.
        children (list[ExecutionTreeNode]): List of child nodes in the execution tree.
    """

    def __init__(self, name: str, _id: str, snapshot: Snapshot, parent: ExecutionTreeNode | None = None,
                 children: list[ExecutionTreeNode] | None = None):
        super().__init__(snapshot)
        self.name = name
        self.id = _id
        self.parent = parent
        if children is None:
            self.children = []

    def __str__(self):
        return f"({self.name=}, {self.id=})"

    def __repr__(self):
        return f"({self.name=}, {self.id=})"
