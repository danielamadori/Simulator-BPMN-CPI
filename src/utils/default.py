from typing import Callable

import numpy as np

from model.region import RegionModel, find_region_by_id, RegionType


class Defaults:

    @classmethod
    def get_default_by_region(cls, root_region: RegionModel, _id: str) -> RegionModel | None:
        region = find_region_by_id(root_region, _id)
        if not region:
            return None

        return cls.__get_default_function_by_region_type(region.type)(region)

    @classmethod
    def __get_default_function_by_region_type(cls, region_type: RegionType) -> Callable[
        [RegionModel], RegionModel | None]:
        default_functions = {
            RegionType.CHOICE: cls.__choice_child,
            RegionType.NATURE: cls.__nature_child
        }

        return default_functions[region_type]

    @staticmethod
    def __choice_child(region: RegionModel) -> RegionModel | None:
        if not region:
            return None

        return region.children[0]

    @staticmethod
    def __nature_child(region: RegionModel) -> RegionModel | None:
        if not region:
            return None

        return np.random.choice(region.children, region.distribution)
