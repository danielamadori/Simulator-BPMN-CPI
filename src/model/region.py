from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, field_validator, ConfigDict


class RegionType(Enum):
    """
    Enum for different types of BPMN+CPI regions.
    1. SEQUENTIAL: Sequential execution of child regions.
    2. PARALLEL: Parallel execution of child regions.
    3. NATURE: Natural region, typically a single task.
    4. CHOICE: Choice between child regions.
    5. TASK: A single task region.
    6. LOOP: A loop region that can repeat its child regions.

    More types can be added as needed.
    """

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    NATURE = "nature"
    CHOICE = "choice"
    TASK = "task"
    LOOP = "loop"


class RegionModel(BaseModel):
    """
    BPMN+CPI parse tree model.

    Attributes:
        id (str | int): Unique identifier for the region.
        type (RegionType): Type of the region defined in RegionType enum.
        label (str | None): Optional label for the region.
        duration (float): Duration of the region, default is 0.
        children (list[RegionModel] | None): List of child regions, default is None
        distribution (list[float] | float | None): Distribution of the region, default is None.
        impacts (list[float] | None): Impacts of the region, default is None
        bound (int | None): Bound for loop regions, default is None.
    """

    id: str | int
    type: RegionType
    label: str | None = None
    duration: float = 0
    children: list[RegionModel] | None = None
    distribution: list[float] | float | None = None
    impacts: list[float] | None = None
    bound: int | None = None

    model_config = ConfigDict(extra='allow')

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
