from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from utils import logging_utils

if TYPE_CHECKING:
    from model.types import TransitionType, MarkingType, PlaceType, PetriNetType, ArcType, RegionModelType, ContextType
    from model.petri_net.wrapper import WrapperPetriNet
    from model.petri_net.time_spin import TimeMarking

logger = logging_utils.get_logger(__name__)


def add_arc_from_to(fr: PlaceType | TransitionType, to: PlaceType | TransitionType, net: PetriNetType,
                    weight: float = 1, type: object = None) -> ArcType:
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
    logger.debug("Adding arc from %s to %s", fr, to)
    a = WrapperPetriNet.Arc(fr, to, weight)

    net.arcs.add(a)
    fr.out_arcs.add(a)
    to.in_arcs.add(a)
    return a


def remove_transition(net: PetriNetType, transition: TransitionType) -> None:
    """
    Removes a transition from the Petri net, including its associated arcs.
    :param net: The Petri net from which to remove the transition.
    :param transition: The transition to remove.
    """
    logger.debug("Removing transition %s", transition)
    for arc in list(transition.in_arcs):
        remove_arc(net, arc)

    for arc in list(transition.out_arcs):
        remove_arc(net, arc)

    net.transitions.discard(transition)
    del transition


def remove_place(net: PetriNetType, place: PlaceType) -> None:
    """
    Removes a place from the Petri net, including its associated arcs.
    :param net: The Petri net from which to remove the place.
    :param place: The place to remove.
    """
    logger.debug("Deleting place %s", place.name)
    for arc in list(place.in_arcs):
        remove_arc(net, arc)

    for arc in list(place.out_arcs):
        remove_arc(net, arc)

    net.places.discard(place)
    del place


def remove_arc(net: PetriNetType, arc: ArcType) -> None:
    """
    Removes an arc from the Petri net.
    :param net: The Petri net from which to remove the arc.
    :param arc: The arc to remove.
    """
    logger.debug("Deleting arc from %s to %s", arc.source.name, arc.target.name)

    net.arcs.discard(arc)
    arc.source.out_arcs.discard(arc)
    arc.target.in_arcs.discard(arc)
    del arc


def get_region_by_id(root_region: RegionModelType, region_id: str) -> RegionModelType | None:
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


def collapse_places(net: PetriNetType, old: PlaceType, new: PlaceType) -> None:
    """
    Collapse old node into new node in the Petri net. They must be separate,
    this means that doesn't exist a path from old to new and from new to old.
    """
    if type(old) != type(new) or old.name == new.name:
        logger.error("Cannot collapse places of different types or same name. %s != %s", type(old), type(new))
        raise TypeError(f"Cannot collapse places of different types or same name. {type(old)} != {type(new)}")

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


def get_all_choices(ctx: ContextType, marking: MarkingType, choices: list[TransitionType] = None) -> list[
    TransitionType]:
    """
    Fills the choices with default transitions if they are not already present.
    If no default transitions are found, it returns the choices as is.
    :param ctx:
    :param marking:
    :param choices:
    :return:
    """
    logger.info("Getting all choices for marking %s with current choices %s", marking, choices)
    if choices is None:
        choices = []

    choices = ctx.strategy.get_default_choices(ctx, marking, choices=choices)[:]
    logger.debug("Default choices are %s", choices)

    # Ensure that only one transition per place is present in the choices
    choices_place = {list(t.in_arcs)[0].source for t in choices if t.in_arcs}

    for t in ctx.semantic.enabled_transitions(ctx.net, marking):
        place = list(t.in_arcs)[0].source
        if place not in choices_place:
            choices.append(t)
            choices_place.add(place)
            logger.debug("Adding transition %s to choices", t, place.name)

    logger.info("All choices are %s", choices)
    return list(choices)


def get_empty_impacts(net: PetriNetType) -> list[float]:
    # Default impacts
    default_impacts = None
    for p in net.places:
        impacts = p.impacts
        if impacts is not None:
            default_impacts = [0] * len(impacts)
            break

    if default_impacts is None:
        logger.exception("Default impacts are None")
        raise RuntimeError("Impacts length not found")
    return default_impacts


def is_final_marking(ctx: ContextType, marking: MarkingType) -> bool:
    """
    Checks if the given marking is a final marking in the context.
    :param ctx: The NetContext containing the final marking.
    :param marking: The marking to check.
    :return: True if the marking is a final marking, False otherwise.
    """
    from model.petri_net.time_spin import TimeMarking
    if not isinstance(marking, TimeMarking):
        logger.warning("Marking is not of type TimeMarking")
        return False

    fm = ctx.final_marking

    for place in ctx.net.places:
        fm_token = fm[place].token
        marking_token = marking[place].token

        if fm_token != marking_token:
            return False

    return True


def get_place_by_name(net: PetriNetType, place_name: str) -> PlaceType | None:
    """
    Trova un posto nel Petri net per nome.
    """
    for place in net.places:
        if place.name == place_name:
            return place
    return None
