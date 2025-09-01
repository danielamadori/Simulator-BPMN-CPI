from __future__ import annotations

from typing import Callable, TYPE_CHECKING

import numpy as np

from model.region import RegionModel, find_region_by_id, RegionType
from utils import logging_utils

if TYPE_CHECKING:
    from model.types import TransitionType, ContextType, PlaceType, MarkingType, RegionModelType

logger = logging_utils.get_logger(__name__)

def get_default_transition(ctx: ContextType, place: PlaceType, marking: MarkingType) -> TransitionType | None:
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
    logger.debug(f"Getting default transition for place {place}")
    # Check if loop region and visit limit is reached
    exit_transition, is_loop, loop_transition = check_loop_transitions(place)

    if is_loop and loop_transition and exit_transition:
        logger.debug(f"Selecting default transition for loop region")
        if place.visit_limit <= marking[place].visit_count:
            # If loop region and visit limit is reached, return exit transition
            logger.debug(f"Visit limit reached for place {place.name}, choosing exit transition {exit_transition.name}")
            return exit_transition
        default_choice = Defaults.get_default_by_region(ctx.region, loop_transition.region_id)
        loop_place = list(loop_transition.out_arcs)[0].target
        if loop_place.entry_id == default_choice.id:
            return loop_transition
        else:
            return exit_transition

    # Get default region by place
    default_choice = Defaults.get_default_by_region(ctx.region, place.entry_id)
    if not default_choice:
        logger.debug(f"No default transition found for place {place.name}. Selecting first outgoing transition.")
        return list(place.out_arcs)[0].target if len(list(place.out_arcs)) > 0 else None

    # Get transition to default region
    for arc in place.out_arcs:
        t = arc.target
        next_p = list(t.out_arcs)[0].target
        if next_p.entry_id == default_choice.id:
            return t

    logger.warning(f"No matching transition found for default region {default_choice.id} from place {place.name}")
    return None


def check_loop_transitions(place: PlaceType):
    if place.region_type != RegionType.LOOP:
        return None, False, None

    is_loop = False
    loop_transition = None
    exit_transition = None
    for arc in place.out_arcs:
        out_transition = arc.target
        if out_transition.region_type == RegionType.LOOP:
            is_loop = True
            if out_transition.label.startswith("Loop"):
                loop_transition = out_transition
            if out_transition.label.startswith("Exit"):
                exit_transition = out_transition

    return exit_transition, is_loop, loop_transition


class Defaults:

    @classmethod
    def get_default_by_region(cls, root_region: RegionModelType, _id: str) -> RegionModelType | None:
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
    def __choice_child(region: RegionModelType) -> RegionModelType | None:
        if not region:
            return None

        return region.children[0]

    @staticmethod
    def __nature_child(region: RegionModelType) -> RegionModelType | None:
        if not region:
            return None

        return np.random.choice(region.children, p=region.distribution)

    @staticmethod
    def __loop_child(region: RegionModelType) -> RegionModelType | None:
        if not region:
            return None

        if np.random.random() < region.distribution:
            return region.children[0]

        return region
