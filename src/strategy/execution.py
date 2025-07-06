from __future__ import annotations

from abc import ABC, abstractmethod
from copy import copy
from typing import Collection, Set, TypeVar

import numpy as np

from model.time_spin import NetUtils, TimeMarking
from model.types import T, M
from utils.default import get_default_transition

ContextType = TypeVar("ContextType", bound="NetContext")


class ExecutionInterface(ABC):

    @abstractmethod
    def consume(self, ctx: ContextType, marking: M, choices: Collection[T] | None = None):
        pass

    @abstractmethod
    def get_choices(self, ctx: ContextType, marking: M):
        pass

    @abstractmethod
    def saturate(self, ctx: ContextType, marking: M):
        pass


class ClassicExecution(ExecutionInterface):

    def get_stoppable_active_transitions(self, ctx: ContextType, marking: M) -> Set[T]:
        enabled_transitions = ctx.semantic.enabled_transitions(ctx.net, marking)
        # Filtro per transizoni con stop attivo
        enabled_transitions = filter(
            lambda x: NetUtils.Transition.get_stop(x), enabled_transitions
        )

        return set(enabled_transitions)

    def get_choices(self, ctx: ContextType, marking: M):
        enabled_transitions = self.get_stoppable_active_transitions(ctx, marking)

        groups = {}
        for t in enabled_transitions:
            parent_place = list(t.in_arcs)[0].source
            if groups.get(parent_place) is None:
                groups.update({parent_place: []})

            groups[parent_place].append(t)

        return groups

    def saturate(self, ctx: ContextType, marking: M) -> tuple[M, float]:
        net = ctx.net
        if len(ctx.semantic.enabled_transitions(net, marking)) > 0:
            return marking, 0

        # Get current place with tokens
        current_places = list(filter(lambda x: marking.marking[x] > 0, marking.keys()))
        min_delta = float("inf")
        for p in current_places:
            # Get the duration of the place
            duration = NetUtils.Place.get_duration(p)
            min_delta = min(min_delta, duration - marking.age[p])

        if min_delta == float("inf"):
            # No places with tokens, return the current marking and 0 delta
            return marking, 0

        # Return the current marking with updated ages
        return marking.add_time(min_delta), min_delta

    def consume(self, ctx: ContextType, marking: M, choices: Collection[T] | None = None):
        if not choices:
            choices = []
        else:
            choices = list(choices)

        all_choices = self.get_choices(ctx, marking)
        new_choices = set(choices)
        # Check if only one transition is chosen for each parent place
        place_chosen = {p: None for p in all_choices.keys()}
        for t in choices:
            parent_place = list(t.in_arcs)[0].source
            if parent_place not in all_choices:
                continue
            if place_chosen[parent_place]:
                raise ValueError(f"{place_chosen[parent_place]} and {parent_place} can't be both choosen")

            place_chosen[parent_place] = t

        # Check if all places have a chosen transition if not get the default transition
        for p in place_chosen:
            if place_chosen[p]:
                continue
            default_transition = get_default_transition(ctx, p)
            if default_transition is None:
                continue
            new_choices.add(default_transition)

        choices = (set(choices) & new_choices) | new_choices

        # Start the consume process
        new_marking, probability, impacts, delta = self.__consume(
            ctx, marking, list(choices)
        )

        return new_marking, probability, impacts, delta

    def __consume(self, ctx: ContextType, marking: M, choices: Collection[T] | None = None) -> tuple[
        TimeMarking, int, list[int], float]:
        if not choices:
            choices = ()

        choices = set(choices)

        net = ctx.net
        saturated_marking, delta = self.saturate(ctx, marking)
        probability = 1
        sem = ctx.semantic

        # Get impacts length
        len_impacts = None
        for p in net.places:
            impacts = NetUtils.Place.get_impacts(p)
            if impacts and len(impacts) > 0:
                len_impacts = len(impacts)
                break

        default_impacts = [0.0] * len_impacts
        impacts = [0.0] * len_impacts
        impacts = np.array(impacts)

        # Get places selected by choices
        selected_places_names = set([list(t.in_arcs)[0].source.name for t in choices])

        # Add all transitions that are enabled and not in choices
        for t in sem.enabled_transitions(net, saturated_marking):
            if NetUtils.Transition.get_stop(t) and t not in choices:
                continue
            parent_place = list(t.in_arcs)[0].source
            if parent_place.name in selected_places_names:
                continue

            choices.add(t)

        # Consume the transitions
        new_marking = copy(saturated_marking)
        transition_fired = []
        for t in choices:
            if not sem.is_enabled(net, t, new_marking):
                continue
            new_marking = sem.fire(net, t, new_marking)
            probability *= NetUtils.Transition.get_probability(t)

            parent_place = list(t.in_arcs)[0].source
            place_impacts = NetUtils.Place.get_impacts(parent_place) or default_impacts
            impacts += np.array(place_impacts)
            # impacts = add_impacts(impacts, place_impacts)
            transition_fired.append(t)

        # Remove fired transitions from choices
        for t in transition_fired:
            choices.remove(t)

        if new_marking == saturated_marking:
            return new_marking, probability, impacts.tolist(), delta
        else:
            new_marking, next_p, next_i, next_delta = self.__consume(
                ctx, new_marking, choices
            )
            impacts += np.array(next_i)
            # impacts = add_impacts(impacts, next_i)

            return new_marking, next_p * probability, impacts.tolist(), delta + next_delta


def add_impacts(i1, i2):
    """
    Adds two impact lists element-wise.
    :param i1: First impact list.
    :param i2: Second impact list.
    :return: Element-wise sum of the two impact lists.
    """
    if not i1:
        return i2
    if not i2:
        return i1

    return [x + y for x, y in zip(i1, i2)]