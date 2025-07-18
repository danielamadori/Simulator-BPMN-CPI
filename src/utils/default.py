from typing import Callable

import numpy as np

from model.region import RegionModel, find_region_by_id, RegionType
from model.types import T
from utils.net_utils import NetUtils


def get_default_transition(ctx, place, marking) -> T | None:
    """
    Get the default transition for a given region.
    If no default is found, it returns the first outgoing transition of the place.
    If the place has no outgoing transitions, it returns None.
    IF a loop region try to fire more than limit, it will choose the exit transition.

    :param ctx: NetContext containing region.
    :param place: Place to find default transition.
    :param marking: marking of the Petri net.
    :return: The default transition or None if not found.
    """

    # Check if loop region and visit limit is reached
    exit_transition, is_loop, loop_transition = loop_transitions(place)

    if is_loop and loop_transition and exit_transition:
        if NetUtils.Place.get_visit_limit(place) <= marking[place]["visit_count"]:
            # If loop region and visit limit is reached, return exit transition
            return exit_transition
        default_choice = Defaults.get_default_by_region(ctx.region, NetUtils.Transition.get_region_id(loop_transition))
        loop_place = list(loop_transition.out_arcs)[0].target
        if NetUtils.Place.get_entry_id(loop_place) == default_choice.id:
            return loop_transition
        else:
            return exit_transition

    # Get default region by place
    default_choice = Defaults.get_default_by_region(ctx.region, NetUtils.Place.get_entry_id(place))
    if not default_choice:
        return list(place.out_arcs)[0].target if len(list(place.out_arcs)) > 0 else None

    # Get transition to default region
    for arc in place.out_arcs:
        t = arc.target
        next_p = list(t.out_arcs)[0].target
        if NetUtils.Place.get_entry_id(next_p) == default_choice.id:
            return t

    return None


def loop_transitions(place):
    is_loop = False
    loop_transition = None
    exit_transition = None
    for arc in place.out_arcs:
        out_transition = arc.target
        if NetUtils.get_type(out_transition) == RegionType.LOOP:
            is_loop = True
            if out_transition.label.startswith("Loop"):
                loop_transition = out_transition
            if out_transition.label.startswith("Exit"):
                exit_transition = out_transition

    return exit_transition, is_loop, loop_transition


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

        if np.random.random() < region.distribution:
            return region.children[0]

        return region
