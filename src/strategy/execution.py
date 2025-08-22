from __future__ import annotations

import copy
from typing import Collection, TYPE_CHECKING

from model.region import RegionType
from utils.default import get_default_transition
from utils.net_utils import get_region_by_id, get_default_impacts

if TYPE_CHECKING:
    from model.types import ContextType, MarkingType, TransitionType, PlaceType


class ClassicExecution:

    def saturate(self, ctx: ContextType, marking: MarkingType) -> tuple[MarkingType, float]:
        """
        Saturate the current marking by checking if there are any enabled transitions.
        :param ctx: Current context
        :param marking: Current marking
        :return: new saturated marking, time delta
        """
        net = ctx.net
        if len(ctx.semantic.enabled_transitions(net, marking)) > 0:
            return marking, 0

        # Get current place with tokens
        current_places = list(filter(lambda x: marking.tokens[x] > 0, marking.keys()))
        min_delta = float("inf")
        for p in current_places:
            # Get the duration of the place
            duration = p.duration
            # Check if transition after place is parallel
            current_delta = duration - marking[p].age
            if len(p.out_arcs) > 0:
                transition = list(p.out_arcs)[0].target
                out_place = list(transition.out_arcs)[0].target
                exit_id = out_place.exit_id
                if exit_id is not None:
                    exit_region = get_region_by_id(ctx.region, exit_id)
                    if exit_region.type == RegionType.PARALLEL:
                        # If the place is parallel and is an exit place, skip the duration of the place
                        current_delta = float("inf")
            min_delta = min(min_delta, current_delta)

        if min_delta == float("inf"):
            # No places with tokens, return the current marking and 0 delta
            return marking, 0

        # Return the current marking with updated ages
        return marking.add_time(min_delta), min_delta

    def consume(self, ctx: ContextType, marking: MarkingType, choices: Collection[TransitionType] | None = None) -> \
            tuple[MarkingType, int, list[float], float]:
        """
        Consume the current marking by executing transitions based on user choices or default choices if not selected.
        :param ctx: Current context containing the net and semantic.
        :param marking: Current marking of the net.
        :param choices: collection of user-selected transitions.
        :return: new marking, probability of the execution, impacts of the execution, execution time.
        """
        # Get default choices if not provided
        default_choices = get_default_choices(ctx, marking, choices=list(choices) if choices is not None else None)

        # Start the consume process
        new_marking, probability, impacts, delta = self.__consume(
            ctx=ctx, marking=marking, user_choices=default_choices
        )

        return new_marking, probability, impacts, delta

    def __consume(self, ctx: ContextType, marking: MarkingType,
                  user_choices: Collection[TransitionType] | None = None) -> tuple[
        MarkingType, int, list[float], float]:
        """
        Recursive function to consume the current marking until there's one (or more)
        transitions with stop that isn't in user_choices
        :param ctx: Current context
        :param marking: Current marking
        :param user_choices: User-selected transitions filled with default transitions
        :return: new marking, probability, impacts, delta
        """
        if user_choices is None:
            user_choices = []

        saturated_marking, time_delta = ctx.strategy.saturate(ctx, marking)
        enabled_transitions = ctx.semantic.enabled_transitions(ctx.net, saturated_marking)
        user_choices = set(user_choices) & enabled_transitions

        default_impacts = get_default_impacts(ctx.net)

        # Check if there is a transition with stop that's not in choices
        strategy_get_choices = get_choices(ctx, marking)
        is_place_chosen = {p: False for p in strategy_get_choices.keys()}
        for t in user_choices:
            in_place = list(t.in_arcs)[0].source
            is_place_chosen[in_place] = True

        # if found then stop or if marking == final_marking
        if not all(is_place_chosen.values()) or saturated_marking == ctx.final_marking:
            return marking, 1, default_impacts, 0

        result_marking = copy.copy(saturated_marking)
        choices = list(user_choices)
        expected_impacts = copy.deepcopy(default_impacts)
        probability = 1
        fired_transition = set()

        # Execute choices
        for t in choices:
            if ctx.semantic.is_enabled(ctx.net, t, result_marking):
                fired_transition.add(t)
            temp_marking, __probability, impacts = execute_transition(ctx, t, result_marking)
            if temp_marking != result_marking:
                user_choices.discard(t)
                result_marking = temp_marking
                expected_impacts = add_impacts(expected_impacts, impacts)
                probability *= __probability

        # Get all enabled transition to fire
        for t in ctx.semantic.enabled_transitions(ctx.net, result_marking):
            if ctx.semantic.is_enabled(ctx.net, t, result_marking):
                fired_transition.add(t)
            result_marking, __probability, impacts = execute_transition(ctx, t, result_marking)
            expected_impacts = add_impacts(expected_impacts, impacts)
            probability *= __probability

        if len(fired_transition) == 0:
            return marking, 1, default_impacts, time_delta

        # Recursive call
        result_marking, new_probability, impacts, delta = self.__consume(ctx, result_marking, user_choices)

        return result_marking, probability * new_probability, add_impacts(expected_impacts, impacts), time_delta + delta


def get_stoppable_active_transitions(ctx: ContextType, marking: MarkingType) -> set[TransitionType]:
    """
    Get the active transitions that can be stopped. It filters the enabled transitions to only include those
    that have the stop attribute set to True.
    :param ctx: Current context containing the net and semantic.
    :param marking: Current marking of the net.
    :return: A set of transitions that are currently enabled and can be stopped.
    """
    enabled_transitions = ctx.semantic.enabled_transitions(ctx.net, marking)
    # Filtro per transizioni con stop attivo
    enabled_transitions = filter(
        lambda x: x.stop, enabled_transitions
    )

    result = set(enabled_transitions)

    return result


def get_choices(ctx: ContextType, marking: MarkingType) -> dict[PlaceType, list[TransitionType]]:
    """
    Get the stoppable transitions grouped by place. It returns a dictionary where the keys are the places
    and the values are lists of transitions that can be executed from that place.
    :param ctx: Current context containing the net and semantic.
    :param marking: Current marking of the net.
    :return: dictionary with places as keys and lists of transitions as values.
    """
    enabled_transitions = get_stoppable_active_transitions(ctx, marking)

    groups = {}
    for t in enabled_transitions:
        parent_place = list(t.in_arcs)[0].source
        if groups.get(parent_place) is None:
            groups.update({parent_place: []})

        groups[parent_place].append(t)

    return groups


def get_default_choices(ctx: ContextType, marking: MarkingType, choices: list[TransitionType] = None) -> list[
    TransitionType]:
    """
    Get the default choices for the current marking.
    Choices represent all transition that are already chosen by the user.
    If choices are provided, it filters the default transitions to only include those that are in the choices.
    If no choices are provided, it returns all default transitions for the current marking.
    This method ensures that for each place, if no transition is chosen, the default transition is added to the choices.
    :param ctx: context containing the net and semantic.

    :param marking: Current marking.
    :param choices: Transitions chosen by the user.
    :return: Set of default transitions.
    """
    if choices is None:
        choices = []

    # Get all choices from the context and marking grouped by place
    all_choices_dict = get_choices(ctx, marking)
    # Flat values from the dictionary to a set
    all_choices = set([t for place in all_choices_dict for t in all_choices_dict[place]])
    new_choices = set(choices) & all_choices

    for place in all_choices_dict:
        place_choices = all_choices_dict[place]
        found = False
        for t in place_choices:
            if t in new_choices:
                found = True
                break
        if found:
            continue

        default_transition = get_default_transition(ctx, place, marking)
        if default_transition is None:
            continue
        new_choices.add(default_transition)

    return list(new_choices)


def add_impacts(i1: list[float], i2: list[float]) -> list[float]:
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
