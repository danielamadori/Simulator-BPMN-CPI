#  Copyright (c) 2025.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pm4py.objects.petri_net.semantics import ClassicSemantics

from utils.net_utils import is_final_marking

if TYPE_CHECKING:
    from model.types import ContextType, MarkingType, TransitionType, PlaceType


class StrategyProto(Protocol):
    """Protocol for strategy classes."""

    def saturate(self, ctx: "ContextType", marking: "MarkingType") -> tuple[MarkingType, float, list[float], float]:
        """Saturate the Petri net based on the current marking.
        :param ctx: Net context
        :param marking: Current marking
        :rtype: tuple[MarkingType, float, list[float], float]
        :return: new marking, probability of the saturation, impacts of the saturation, execution time of the saturation
        """
        raise NotImplementedError

    def consume(self, ctx: "ContextType", marking: "MarkingType", choices: list["TransitionType"] | None = None) -> tuple[MarkingType, float, list[float], float]:
        """Consume the Petri net based on the current marking and choices.
        :param ctx: Net context
        :param marking: Current marking
        :param choices: List of user choices (transitions to fire)
        :rtype: tuple[MarkingType, float, list[float], float]
        :return: new marking, probability of the consumption, impacts of the consumption, execution time of the consumption
        """
        raise NotImplementedError

def get_min_delta(ctx: "ContextType", m: "MarkingType") -> tuple[float, list["TransitionType"]]:
    if is_final_marking(ctx, m):
        return float('inf'), []

    min_delta_transitions = []

    # Get all input places that enables transitions using pm4py semantics
    raw_semantic = ClassicSemantics()
    active_transitions = raw_semantic.enabled_transitions(ctx.net, m.tokens)
    valid_places = set()
    for t in active_transitions:
        input_places = [arc.source for arc in t.in_arcs]
        for place in input_places:
            valid_places.add(place)

    # Calculate the minimum delta time for all tokens in valid places
    min_delta = float('inf')
    for place in valid_places:
        token, age, _ = m[place]
        first_out_transition = get_first_target(place)

        # Check if the first outgoing transition is a parallel exit
        if is_parallel_exit(first_out_transition):
            # Take max age among all input places of the parallel exit transition
            parallel_exit_places = _get_parallel_exit_places(first_out_transition)
            max_delta = [p.duration - m[p].age for p in parallel_exit_places]
            min_delta = min(min_delta, max(max_delta))
        else:
            min_delta = min(min_delta, place.duration - age)

    # Get all transitions that can be fired at min_delta
    for place in valid_places:
        token, age, _ = m[place]
        if place.duration - age == min_delta:
            for arc in place.out_arcs:
                min_delta_transitions.append(arc.target)

    return min_delta, min_delta_transitions

def get_first_source(component: "TransitionType | PlaceType") -> "TransitionType | PlaceType":
    return list(component.in_arcs)[0].source

def get_first_target(component: "TransitionType | PlaceType") -> "TransitionType | PlaceType":
    return list(component.out_arcs)[0].target

def _get_parallel_exit_places(t: "TransitionType") -> list["PlaceType"]:
    places = []
    if not is_parallel_exit(t):
        return places

    for arc in t.in_arcs:
        places.append(arc.source)

    return places

def is_parallel_exit(t: "TransitionType") -> bool:
    return t.region_type == "parallel" and len(t.in_arcs) > 1


def execute_transition(ctx: ContextType, t: TransitionType, marking: MarkingType) -> tuple[
    MarkingType, float, list[float]]:
    """
    Execute a transition in the Petri net and return the new marking, probability of the transition, and impacts.
    :param ctx:
    :param t:
    :param marking:
    :return: marking after transition execution, probability of the transition, impacts of the transition.
    """
    marking = ctx.semantic.execute(ctx.net, t, marking)
    in_place = list(t.in_arcs)[0].source
    probability = t.probability
    impacts = in_place.impacts

    return marking, probability, impacts
