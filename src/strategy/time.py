#  Copyright (c) 2025.
import copy

from model.region import RegionType
from model.status import ActivityState, propagate_status
from strategy.base import get_min_delta, execute_transition
from strategy.execution import get_default_choices, add_impacts
from utils import logging_utils
from utils.net_utils import get_empty_impacts

logger = logging_utils.get_logger(__name__)


class TimeStrategy:
    """
    Strategy that executes for a specific time amount (time_step).
    Unlike CounterExecution which saturates, this advances by the given time step.
    """

    def saturate(self, ctx: "ContextType", marking: "MarkingType", regions: dict[int: "RegionModelType"], 
                 status: dict["RegionModelType", "ActivityState"], time_step: float):
        """
        Execute transitions for a specific time duration.
        
        Args:
            ctx: The execution context
            marking: Current marking state
            regions: Dictionary mapping region IDs to RegionModel objects
            status: Dictionary mapping regions to their ActivityState
        """
        logger.debug(f"TimeStrategy: Advancing by {time_step} time units")

        current_marking = copy.deepcopy(marking)
        probability = 1.0
        impacts = get_empty_impacts(ctx.net)
        default_impacts = get_empty_impacts(ctx.net)
        execution_time = 0.0
        remaining_time = time_step

        while remaining_time >= 0:
            min_delta, transitions_to_fire = get_min_delta(ctx, current_marking)
            min_delta = max(min_delta, 0)

            if len(transitions_to_fire) == 0:
                logger.debug("No transitions to fire")
                # Add remaining time even if no transitions
                current_marking = current_marking.add_time(remaining_time)
                execution_time += remaining_time
                break

            # Only advance by min(min_delta, remaining_time)
            actual_delta = min(min_delta, remaining_time)
            logger.debug(f"Adding {actual_delta} time to marking (min_delta={min_delta}, remaining={remaining_time})")
            current_marking = current_marking.add_time(actual_delta)
            execution_time += actual_delta
            remaining_time -= actual_delta

            # If we haven't reached the transition firing time, stop
            if actual_delta < min_delta:
                logger.debug("Time step exhausted before next transition")
                break

            if any(map(lambda t: t.stop, transitions_to_fire)):
                logger.debug("Stop transition found, exiting")
                break

            for t in transitions_to_fire:
                region = regions[int(t.region_id)]
                status[region] = ActivityState.ACTIVE
                logger.debug(f"Executing transition {t}")
                current_marking, p, imp = execute_transition(ctx, t, current_marking)
                probability *= p
                impacts = add_impacts(impacts, imp or default_impacts)
                logger.debug(
                    f"After executing {t}, marking {current_marking}, probability {probability}, impacts {impacts}")

        # Update completed tasks status
        for p in ctx.net.places:
            entry_id = getattr(p, "entry_id", None)
            exit_id = getattr(p, "exit_id", None)

            if entry_id is not None and int(entry_id) in regions:
                region = regions[int(entry_id)]
                if current_marking[p].token > 0:
                    status[region] = ActivityState.ACTIVE

            if exit_id is not None and int(exit_id) in regions:
                region = regions[int(exit_id)]
                if region.is_task():
                    item = current_marking[p]
                    if item.token > 0 or item.visit_count > 0:
                        status[region] = ActivityState.COMPLETED

        propagate_status(regions[0], status)

        logger.debug(
            f"TimeStrategy complete. Final marking {current_marking}, probability {probability}, impacts {impacts}, execution_time {execution_time}")
        return current_marking, probability, impacts, execution_time

    def consume(self, ctx: "ContextType", marking: "MarkingType", regions: dict[int: "RegionModelType"],
                status: dict["RegionModelType", "ActivityState"], time_step: float,
                decisions: list["TransitionType"] | None = None):
        """
        Execute decisions and then advance by the given time step.
        
        Args:
            ctx: The execution context
            marking: Current marking state
            regions: Dictionary mapping region IDs to RegionModel objects
            status: Dictionary mapping regions to their ActivityState
            time_step: The time duration to advance (n)
            decisions: Optional list of user decisions for gateways
        """
        logger.debug(f"TimeStrategy: Consuming with time_step={time_step}")
        if decisions is None:
            decisions = []

        logger.debug("User decisions: %s", decisions)
        decisions = get_default_choices(ctx, marking, decisions)
        logger.debug("Final decisions after adding defaults and filter: %s", decisions)

        impacts = get_empty_impacts(ctx.net)
        default_impacts = get_empty_impacts(ctx.net)
        execution_time = 0.0
        probability = 1.0

        current_marking = copy.deepcopy(marking)

        for t in decisions:
            logger.debug(f"Executing decisions transition {t}")
            in_place = list(t.in_arcs)[0].source
            current_marking = ctx.semantic.execute(ctx.net, t, current_marking)
            probability *= t.probability
            impacts = [imp + imp_t for imp, imp_t in zip(impacts, in_place.impacts or default_impacts)]
            logger.debug(
                f"After executing decisions {t}, marking {current_marking}, probability {probability}, impacts {impacts}")

        new_marking, prob, imp, exec_time = self.saturate(ctx, current_marking, regions, status, time_step)
        probability *= prob
        impacts = [imp1 + imp2 for imp1, imp2 in zip(impacts, imp)]
        execution_time += exec_time

        logger.debug(
            f"TimeStrategy consumption complete. Final marking {new_marking}, probability {probability}, impacts {impacts}, execution_time {execution_time}")
        return new_marking, probability, impacts, execution_time, decisions
