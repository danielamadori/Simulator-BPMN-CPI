#  Copyright (c) 2025.
import copy

from strategy.execution import get_default_choices
from utils import logging_utils
from utils.net_utils import get_empty_impacts

logger = logging_utils.get_logger(__name__)


class CounterExecution:

    def saturate(self, ctx: "ContextType", marking: "MarkingType"):
        logger.debug(f"Saturating marking {marking}")
        transitions_to_fire = transitions_to_saturation(ctx, marking)

        current_marking = copy.deepcopy(marking)
        probability = 1.0
        impacts = get_empty_impacts(ctx.net)
        default_impacts = get_empty_impacts(ctx.net)
        execution_time = 0.0
        for t in transitions_to_fire:
            logger.debug(f"Executing transition {t}")

            in_place = list(t.in_arcs)[0].source
            current_marking = ctx.semantic.fire(ctx.net, t, current_marking)
            probability *= t.probability
            impacts = [imp + imp_t for imp, imp_t in zip(impacts, in_place.impacts or default_impacts)]
            execution_time += in_place.duration
            logger.debug(
                f"After executing {t}, marking {current_marking}, probability {probability}, impacts {impacts}, execution_time {execution_time}")

        logger.debug(
            f"Saturation complete. Final marking {current_marking}, probability {probability}, impacts {impacts}, execution_time {execution_time}")
        return current_marking, probability, impacts, execution_time

    def consume(self, ctx: "ContextType", marking: "MarkingType", choices: list["TransitionType"] | None = None):
        logger.debug(f"Consuming marking {marking}")
        if choices is None:
            choices = []

        choices = get_default_choices(ctx, marking, choices)

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


def transitions_to_saturation(ctx: "ContextType", marking: "MarkingType") -> list["TransitionType"]:
    logger.debug("Transitions to saturation")

    semantic = ctx.semantic
    transitions = []
    current_marking = copy.deepcopy(marking)

    while True:
        current_marking = current_marking.add_time(float('inf'))
        logger.debug(f"Added infinite time to marking")
        active_transitions = semantic.enabled_transitions(ctx.net, current_marking)
        logger.debug(f"Active transitions: {active_transitions}")

        if any(map(lambda t: t.stop, active_transitions)) or not active_transitions:
            break

        for t in active_transitions:
            transitions.append(t)
            current_marking = semantic.execute(ctx.net, t, current_marking)

    logger.debug(f"Transitions to saturation: {transitions}")
    return transitions


def get_input_places(t: "TransitionType") -> list["PlaceType"]:
    return [arc.source for arc in t.in_arcs]
