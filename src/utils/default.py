from typing import Callable

import numpy as np

from model.region import RegionModel, find_region_by_id, RegionType
from model.types import T
from utils.net_utils import NetUtils


def get_default_transition(ctx, place) -> T | None:
    """
    Get the default transition for a given region.
    :param ctx: NetContext containing region.
    :param place: Place to find default transition.
    :return: The default transition or None if not found.
    """
    default_choice = Defaults.get_default_by_region(ctx.region, NetUtils.Place.get_entry_id(place))
    if not default_choice:
        return None

    for arc in place.out_arcs:
        t = arc.target
        next_p = list(t.out_arcs)[0].target
        if NetUtils.Place.get_entry_id(next_p) == default_choice.id:
            return t

    return None


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
            RegionType.NATURE: cls.__nature_child,
            RegionType.LOOP: cls.__loop_child
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

        return np.random.choice(region.children, p=region.distribution)

    @staticmethod
    def __loop_child(region: RegionModel) -> RegionModel | None:
        if not region:
            return None

        return region.children[0] if np.random.random() < region.distribution else region