#  Copyright (c) 2025.
import copy

from strategy.base import get_min_delta, execute_transition
from strategy.execution import get_default_choices, add_impacts
from utils import logging_utils
from utils.net_utils import get_empty_impacts

logger = logging_utils.get_logger(__name__)


class CounterExecution:

    def saturate(self, ctx: "ContextType", marking: "MarkingType"):
        logger.debug(f"Saturating marking {marking}")

        current_marking = copy.deepcopy(marking)
        probability = 1.0
        impacts = get_empty_impacts(ctx.net)
        default_impacts = get_empty_impacts(ctx.net)
        execution_time = 0.0
        while True:
            min_delta, transitions_to_fire = get_min_delta(ctx, current_marking)
            min_delta = max(min_delta, 0)

            if len(transitions_to_fire) == 0:
                logger.debug("No transitions to fire")
                break

            logger.debug("Adding %f time to marking", min_delta)
            current_marking = current_marking.add_time(min_delta)

            if any(map(lambda t: t.stop, transitions_to_fire)):
                logger.debug("Stop transition found, exiting saturation")
                break

            for t in transitions_to_fire:
                logger.debug(f"Executing transition {t}")
                current_marking, p, imp = execute_transition(ctx, t, current_marking)
                probability *= p
                impacts = add_impacts(impacts, imp or default_impacts)
                execution_time += min_delta
                logger.debug(
                    f"After executing {t}, marking {current_marking}, probability {probability}, impacts {impacts}, execution_time {execution_time}")


        logger.debug(
            f"Saturation complete. Final marking {current_marking}, probability {probability}, impacts {impacts}, execution_time {execution_time}")
        return current_marking, probability, impacts, execution_time

    def consume(self, ctx: "ContextType", marking: "MarkingType", choices: list["TransitionType"] | None = None):
        logger.debug(f"Consuming marking {marking}")
        if choices is None:
            choices = []

        logger.debug("User choices: %s", choices)
        choices = get_default_choices(ctx, marking, choices)
        logger.debug("Final choices after adding defaults and filter: %s", choices)

        impacts = get_empty_impacts(ctx.net)
        default_impacts = get_empty_impacts(ctx.net)
        execution_time = 0.0
        probability = 1.0

        current_marking = copy.deepcopy(marking)

        for t in choices:
            logger.debug(f"Executing choice transition {t}")
            in_place = list(t.in_arcs)[0].source
            current_marking = ctx.semantic.execute(ctx.net, t, current_marking)
            probability *= t.probability
            impacts = [imp + imp_t for imp, imp_t in zip(impacts, in_place.impacts or default_impacts)]
            execution_time += in_place.duration
            logger.debug(
                f"After executing choice {t}, marking {current_marking}, probability {probability}, impacts {impacts}, execution_time {execution_time}")

        new_marking, prob, imp, exec_time = self.saturate(ctx, current_marking)
        probability *= prob
        impacts = [imp1 + imp2 for imp1, imp2 in zip(impacts, imp)]
        execution_time += exec_time

        logger.debug(
            f"Consumption complete. Final marking {new_marking}, probability {probability}, impacts {impacts}, execution_time {execution_time}")
        return new_marking, probability, impacts, execution_time


# def transitions_to_saturation(ctx: "ContextType", marking: "MarkingType") -> list["TransitionType"]:
#     logger.debug("Transitions to saturation")
#
#     semantic = ctx.semantic
#     transitions = []
#     current_marking = copy.deepcopy(marking)
#
#     while True:
#         min_delta, min_delta_transitions = get_min_delta(ctx, current_marking)
#         current_marking = current_marking.add_time(min_delta)
#         logger.debug(f"Added {min_delta} time units to marking")
#         active_transitions = min_delta_transitions
#         logger.debug(f"Active transitions: {active_transitions}")
#
#         if any(map(lambda t: t.stop, active_transitions)) or not active_transitions:
#             break
#
#         for t in active_transitions:
#             transitions.append(t)
#             current_marking = semantic.execute(ctx.net, t, current_marking)
#
#     logger.debug(f"Transitions to saturation: {transitions}")
#     return transitions

#
# def get_input_places(t: "TransitionType") -> list["PlaceType"]:
#     return [arc.source for arc in t.in_arcs]
