import random
from uuid import uuid4
from model.region import RegionModel, RegionType


def region_factory(region_type: RegionType, id: str = None) -> RegionModel:
    if not id:
        id = uuid4().hex

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
        child1 = region_factory(RegionType.TASK, f"{id}_child1")
        child2 = region_factory(RegionType.TASK, f"{id}_child2")
        return RegionModel(
            id=id,
            type=region_type,
            impacts=None,
            duration=0,
            children=[child1, child2],
            distribution=None,
        )

    elif region_type == RegionType.NATURE:
        child1 = region_factory(RegionType.TASK, f"{id}_c1")
        child2 = region_factory(RegionType.TASK, f"{id}_c2")
        return RegionModel(
            id=id,
            type=region_type,
            impacts=None,
            duration=0,
            children=[child1, child2],
            distribution=[0.5, 0.5],
        )

    elif region_type == RegionType.CHOICE:
        child1 = region_factory(RegionType.TASK, f"{id}_c1")
        child2 = region_factory(RegionType.TASK, f"{id}_c2")
        return RegionModel(
            id=id,
            type=region_type,
            impacts=None,
            duration=0,
            children=[child1, child2],
            distribution=[],  # opzionale per CHOICE
        )

    raise ValueError(f"Tipo di regione non supportato: {region_type}")
