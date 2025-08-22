from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from pm4py.objects.petri_net.semantics import ClassicSemantics

from strategy.execution import add_impacts, get_default_choices
from utils.net_utils import get_default_impacts

if TYPE_CHECKING:
    from model.types import MarkingType, TransitionType, ContextType


class DurationExecution:
    """
    Class to calculate the duration of execution in a Petri net.
    It calculates the time to consume to reach a saturated marking based on the current marking.
    """

    def saturate(self, ctx: ContextType, marking: MarkingType) -> tuple[MarkingType, float, list[float], float, float]:
        """
        Calculate time to consume to reach a saturated marking in the Petri net based on the current marking.
        :param ctx: current context containing the net.
        :param marking: current marking of the net.
        :return: new marking, probability, impact, execution_time, remaining time.
        """
        duration, can_continue = calculate_steps(ctx, marking)
        original_duration = duration
        probability = 1.0
        impact = get_default_impacts(ctx.net)

        semantics = ClassicSemantics()

        while duration > 0:
            enabled_transitions = semantics.enabled_transitions(ctx.net, marking.tokens)

            if any(map(lambda t: t.stop, enabled_transitions)):
                break

            all_in_place = [arc.source for t in enabled_transitions for arc in t.in_arcs]
            delta_places = {p: max(p.duration - marking[p].age, 0) for p in all_in_place}
            min_delta = float("inf")
            for p in delta_places:
                current_delta = max(delta_places[p], 0)
                if current_delta < min_delta:
                    min_delta = current_delta

            marking = marking.add_time(min_delta)
            duration -= min_delta

            for t in ctx.semantic.enabled_transitions(ctx.net, marking):
                marking = ctx.semantic.execute(ctx.net, t, marking)
                probability = t.probability * probability
                in_place = list(t.in_arcs)[0].source
                impact = add_impacts(impact, in_place.impacts)

        return marking, probability, impact, original_duration - duration, duration

    def consume(self, ctx: ContextType, marking: MarkingType, choices: list[TransitionType] | None = None) -> tuple[
        MarkingType, float, list[float], float]:
        """
        Consume the Petri net based on the current marking and choices.
        :param ctx: current context containing the net.
        :param marking: current marking of the net.
        :param choices: list of transitions to consume.
        :return: new marking, probability, impact, execution_time, remaining time.
        """
        if choices is None:
            choices = []

        impact = get_default_impacts(ctx.net)
        duration = 0
        probability = 1

        new_marking = copy.copy(marking)
        user_choices = get_default_choices(ctx, new_marking, choices)

        for choice in user_choices:
            in_place = list(choice.in_arcs)[0].source
            new_marking = ctx.semantic.execute(ctx.net, choice, new_marking)
            duration += in_place.duration
            probability *= choice.probability
            impact = add_impacts(impact, in_place.impacts)

        new_marking, new_probability, new_impact, new_time_delta, _ = ctx.strategy.saturate(ctx, new_marking)
        duration += new_time_delta
        probability *= new_probability
        impact = add_impacts(impact, new_impact)

        return new_marking, probability, impact, duration


def calculate_steps(ctx: ContextType, marking: MarkingType) -> tuple[float, bool]:
    """
    Calculate time to consume to reach a saturated marking in the Petri net based on the current marking.
    :param ctx: current context containing the net.
    :param marking: current marking of the net.
    :return: duration and can continue flag.
    """
    semantics = ClassicSemantics()

    durations = {p: p.duration - marking[p].age for p in ctx.net.places}
    __duration = 0
    __can_continue = True

    raw_marking = marking.tokens
    while True:
        # Get enabled transitions based on the current marking
        __enabled_transitions = semantics.enabled_transitions(ctx.net, raw_marking)
        # Check if any transition can continue
        __can_continue &= any(map(lambda t: not t.stop, __enabled_transitions))

        # If no enabled transitions or can't continue, break the loop
        if len(__enabled_transitions) == 0 or not __can_continue:
            break

        # Fire enabled transitions
        for t in __enabled_transitions:
            in_place = list(t.in_arcs)[0].source
            __duration += durations[in_place]
            raw_marking = semantics.execute(t, ctx.net, raw_marking)

    return __duration, __can_continue
