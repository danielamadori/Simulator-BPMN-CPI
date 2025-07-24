from __future__ import annotations

import logging
from enum import Enum

from model.region import RegionModel
from model.types import P, T, M

def get_region_by_id(root_region: RegionModel, region_id: str) -> RegionModel | None:
    """
    Recursively searches for a region by its ID in the given root region.
    :param root_region: The root region to start the search from.
    :param region_id: The ID of the region to find.
    :return: The RegionModel if found, otherwise None.
    """
    if root_region.id == region_id:
        return root_region

    if root_region.children is None or len(root_region.children) == 0:
        return None

    for subregion in root_region.children:
        found_region = get_region_by_id(subregion, region_id)
        if found_region:
            return found_region

    return None

class NetUtils:

    @classmethod
    def get_label(cls, node: P | T):
        return node.properties.get(PropertiesKeys.LABEL)

    @classmethod
    def get_type(cls, node: P | T):
        return node.properties.get(PropertiesKeys.TYPE)

    class Place:

        @classmethod
        def get_duration(cls, node: P | T):
            return node.properties.get(PropertiesKeys.DURATION, 0)

        @classmethod
        def get_entry_id(cls, place: P):
            return place.properties.get(PropertiesKeys.ENTRY_RID)

        @classmethod
        def get_exit_id(cls, place: P):
            return place.properties.get(PropertiesKeys.EXIT_RID)

        @classmethod
        def get_impacts(cls, place: P):
            return place.properties.get(PropertiesKeys.IMPACTS)

        @classmethod
        def get_visit_limit(cls, place: P):
            return place.properties.get(PropertiesKeys.VISIT_LIMIT)

    class Transition:

        @classmethod
        def get_region_id(cls, transition: T):
            return transition.properties.get(PropertiesKeys.ENTRY_RID)

        @classmethod
        def get_probability(cls, transition: T):
            return transition.properties.get(PropertiesKeys.PROBABILITY)

        @classmethod
        def get_stop(cls, transition: T):
            return transition.properties.get(PropertiesKeys.STOP)



class PropertiesKeys(Enum):
    ENTRY_RID = "entry_rid"  # Entry Region ID
    EXIT_RID = "exit_rid"  # Exit Region ID
    LABEL = "label"
    TYPE = "type"
    DURATION = "duration"
    IMPACTS = "impacts"
    PROBABILITY = "probability"
    STOP = "stop"
    VISIT_LIMIT = 'fire_limit'


def get_all_choices(ctx, marking: M, choices: list[T] = None) -> list[T]:
    """
    Fills the choices with default transitions if they are not already present.
    If no default transitions are found, it returns the choices as is.
    :param ctx:
    :param marking:
    :param choices:
    :return:
    """
    if choices is None:
        choices = []

    choices = ctx.strategy.get_default_choices(ctx, marking, choices=choices)[:]
    choices_place = {list(t.in_arcs)[0].source for t in choices if t.in_arcs}

    for t in ctx.semantic.enabled_transitions(ctx.net, marking):
        place = list(t.in_arcs)[0].source
        if place not in choices_place:
            choices.append(t)
            choices_place.add(place)

    return list(choices)


def get_default_impacts(net):
    # Default impacts
    default_impacts = None
    for p in net.places:
        impacts = NetUtils.Place.get_impacts(p)
        if impacts is not None:
            default_impacts = [0] * len(impacts)
            break
    if default_impacts is None:
        logging.getLogger("execution").debug("Default impacts are None")
        raise RuntimeError("Impacts length not found")
    return default_impacts
