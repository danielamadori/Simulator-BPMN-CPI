import itertools
import random
from model.region import RegionModel, RegionType

_id_counter = itertools.count()


def _next_id() -> int:
    return next(_id_counter)


def region_factory(region_type: RegionType, id: int = None) -> RegionModel:
    if id is None:
        id = _next_id()

    if region_type == RegionType.TASK:
        return RegionModel(
            id=id,
            type=region_type,
            impacts=[random.randint(1, 10) for _ in range(3)],
            duration=random.randint(1, 10),
            children=None,
            distribution=None,
        )

    elif region_type == RegionType.SEQUENTIAL or region_type == RegionType.PARALLEL:
        child1 = region_factory(RegionType.TASK, _next_id())
        child2 = region_factory(RegionType.TASK, _next_id())
        return RegionModel(
            id=id,
            type=region_type,
            impacts=None,
            duration=0,
            children=[child1, child2],
            distribution=None,
        )

    elif region_type == RegionType.NATURE:
        child1 = region_factory(RegionType.TASK, _next_id())
        child2 = region_factory(RegionType.TASK, _next_id())
        return RegionModel(
            id=id,
            type=region_type,
            impacts=None,
            duration=0,
            children=[child1, child2],
            distribution=[0.5, 0.5],
        )

    elif region_type == RegionType.CHOICE:
        child1 = region_factory(RegionType.TASK, _next_id())
        child2 = region_factory(RegionType.TASK, _next_id())
        return RegionModel(
            id=id,
            type=region_type,
            impacts=None,
            duration=0,
            children=[child1, child2],
            distribution=[],  # optional for CHOICE
        )

    raise ValueError(f"Unsupported region type: {region_type}")
