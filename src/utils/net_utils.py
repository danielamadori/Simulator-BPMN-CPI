from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING

from model.region import RegionModel

if TYPE_CHECKING:
    from model.types import T, M
    from model.petri_net.wrapper import WrapperPetriNet
    from model.petri_net.time_spin import TimeMarking


def add_arc_from_to(fr, to, net, weight=1, type=None) -> WrapperPetriNet.Arc:
    """
    Function used instead of pm4py.objects.petri_net.utils.petri_utils.add_arc_from_to to add wrapped arc.

    :param fr: transition/place from
    :param to:  transition/place to
    :param net: net to use
    :param weight: weight associated to the arc
    :param type: type of arc. Possible values: None
    :return: arc attached to petri net
    """
    from model.petri_net.wrapper import WrapperPetriNet
    a = WrapperPetriNet.Arc(fr, to, weight)

    net.arcs.add(a)
    fr.out_arcs.add(a)
    to.in_arcs.add(a)
    return a


def remove_transition(net: WrapperPetriNet, transition: WrapperPetriNet.Transition):
    """
    Removes a transition from the Petri net, including its associated arcs.
    :param net: The Petri net from which to remove the transition.
    :param transition: The transition to remove.
    """
    for arc in list(transition.in_arcs):
        remove_arc(net, arc)

    for arc in list(transition.out_arcs):
        remove_arc(net, arc)

    net.transitions.discard(transition)
    del transition


def remove_place(net: WrapperPetriNet, place: WrapperPetriNet.Place):
    """
    Removes a place from the Petri net, including its associated arcs.
    :param net: The Petri net from which to remove the place.
    :param place: The place to remove.
    """
    for arc in list(place.in_arcs):
        remove_arc(net, arc)

    for arc in list(place.out_arcs):
        remove_arc(net, arc)

    net.places.discard(place)
    del place


def remove_arc(net: WrapperPetriNet, arc: WrapperPetriNet.Arc):
    """
    Removes an arc from the Petri net.
    :param net: The Petri net from which to remove the arc.
    :param arc: The arc to remove.
    """
    net.arcs.discard(arc)
    arc.source.out_arcs.discard(arc)
    arc.target.in_arcs.discard(arc)
    del arc


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


def collapse_places(net: WrapperPetriNet, old: WrapperPetriNet.Place, new: WrapperPetriNet.Place):
    """
    Collapse old node into new node in the Petri net. They must be separate,
    this means that doesn't exist a path from old to new and from new to old.
    """
    if type(old) != type(new) or old.name == new.name:
        return

    new.exit_id = old.exit_id

    for arc in list(old.in_arcs):
        add_arc_from_to(arc.source, new, net)
        remove_arc(net, arc)

    remove_place(net, old)


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


def get_default_impacts(net: WrapperPetriNet):
    # Default impacts
    default_impacts = None
    for p in net.places:
        impacts = p.impacts
        if impacts is not None:
            default_impacts = [0] * len(impacts)
            break
    if default_impacts is None:
        logging.getLogger("execution").debug("Default impacts are None")
        raise RuntimeError("Impacts length not found")
    return default_impacts


def is_final_marking(ctx, marking: M) -> bool:
    """
    Checks if the given marking is a final marking in the context.
    :param ctx: The NetContext containing the final marking.
    :param marking: The marking to check.
    :return: True if the marking is a final marking, False otherwise.
    """
    from model.petri_net.time_spin import TimeMarking
    if not isinstance(marking, TimeMarking):
        return False

    fm = ctx.final_marking

    if fm.keys() != marking.keys():
        return False

    for place in ctx.net.places:
        fm_token = fm[place]['token']
        marking_token = marking[place]['token']

        if fm_token != marking_token:
            return False

    return True
