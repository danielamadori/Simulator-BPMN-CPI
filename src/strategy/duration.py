import copy

from pm4py.objects.petri_net.semantics import ClassicSemantics

from model.petri_net.time_spin import TimeMarking
from strategy.execution import add_impacts, get_default_choices
from utils.net_utils import NetUtils, get_default_impacts


class DurationExecution:
    """
    Class to calculate the duration of execution in a Petri net.
    It calculates the time to consume to reach a saturated marking based on the current marking.
    """

    def saturate(self, ctx, marking: TimeMarking) -> tuple[TimeMarking, float, list[int], float, float]:
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

            if any(map(lambda t: NetUtils.Transition.get_stop(t), enabled_transitions)):
                break

            all_in_place = [arc.source for t in enabled_transitions for arc in t.in_arcs]
            delta_places = {p: max(NetUtils.Place.get_duration(p) - marking[p]['age'], 0) for p in all_in_place}
            min_delta = float("inf")
            for p in delta_places:
                current_delta = max(delta_places[p], 0)
                if current_delta < min_delta:
                    min_delta = current_delta

            marking = marking.add_time(min_delta)
            duration -= min_delta

            for t in ctx.semantic.enabled_transitions(ctx.net, marking):
                marking = ctx.semantic.execute(ctx.net, t, marking)
                probability = NetUtils.Transition.get_probability(t) * probability
                in_place = list(t.in_arcs)[0].source
                impact = add_impacts(impact, NetUtils.Place.get_impacts(in_place))

        return marking, probability, impact, original_duration - duration, duration

    def consume(self, ctx, marking: TimeMarking, choices: list | None = None) -> tuple[TimeMarking, float, list, float]:
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
            duration += NetUtils.Place.get_duration(in_place)
            probability *= NetUtils.Transition.get_probability(choice)
            impact = add_impacts(impact, NetUtils.Place.get_impacts(in_place))

        new_marking, new_probability, new_impact, new_time_delta, _ = ctx.strategy.saturate(ctx, new_marking)
        duration += new_time_delta
        probability *= new_probability
        impact = add_impacts(impact, new_impact)

        return new_marking, probability, impact, duration


def calculate_steps(ctx, marking: TimeMarking) -> tuple[float, bool]:
    """
    Calculate time to consume to reach a saturated marking in the Petri net based on the current marking.
    :param ctx: current context containing the net.
    :param marking: current marking of the net.
    :return: duration and can continue flag.
    """
    semantics = ClassicSemantics()

    durations = {p: NetUtils.Place.get_duration(p) - marking[p]['age'] for p in ctx.net.places}
    __duration = 0
    __can_continue = True

    raw_marking = marking.tokens
    while True:
        # Get enabled transitions based on the current marking
        __enabled_transitions = semantics.enabled_transitions(ctx.net, raw_marking)
        # Check if any transition can continue
        __can_continue &= any(map(lambda t: not NetUtils.Transition.get_stop(t), __enabled_transitions))

        # If no enabled transitions or can't continue, break the loop
        if len(__enabled_transitions) == 0 or not __can_continue:
            break

        # Fire enabled transitions
        for t in __enabled_transitions:
            in_place = list(t.in_arcs)[0].source
            __duration += durations[in_place]
            raw_marking = semantics.execute(t, ctx.net, raw_marking)

            # # If transition has multiple outgoing arcs is parallel
            # if len(t.out_arcs) > 1:
            #     max_parallel_duration = None
            #     use_max = True
            #     out_places = [arc.target for arc in t.out_arcs]
            #
            #     for p in out_places:
            #         copy_raw_marking = copy.copy(raw_marking)
            #         for p1 in out_places:
            #             if p == p1:
            #                 continue
            #             copy_raw_marking[p1] = 0
            #
            #         # Calculate the duration of the parallel branch
            #         branch_duration, __branch_can_continue = calculate_steps(ctx, TimeMarking(copy_raw_marking))
            #         # If it can't continue, we need to use minimum duration
            #         use_max &= __branch_can_continue
            #
            #         if use_max and (
            #                 max_parallel_duration is None or max_parallel_duration < branch_duration and use_max):
            #             max_parallel_duration = branch_duration
            #         elif not use_max and (max_parallel_duration is None or max_parallel_duration > branch_duration):
            #             max_parallel_duration = branch_duration
            #             __can_continue = False
            #
            #     __duration += max_parallel_duration

    return __duration, __can_continue
