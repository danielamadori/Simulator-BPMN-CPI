#  Copyright (c) 2025.
import copy

from model.region import RegionType
from model.status import ActivityState
from strategy.base import get_min_delta, execute_transition
from strategy.execution import get_default_choices, add_impacts
from utils import logging_utils
from utils.net_utils import get_empty_impacts

logger = logging_utils.get_logger(__name__)

def parse(region: "RegionModelType", status:dict["RegionModelType", "ActivityState"]):
    if region.is_task():
        return

    status[region] = ActivityState.WAITING

    for child in region.children:
        parse(child, status)

    if region.is_sequential():
        if status[region.children[0]] == ActivityState.ACTIVE or status[region.children[1]] == ActivityState.ACTIVE:
            status[region] = ActivityState.ACTIVE
        elif status[region.children[1]] == ActivityState.COMPLETED:
            status[region] = ActivityState.COMPLETED

    if region.is_parallel():
        all_completed = True
        for child in region.children:
            if status[child] == ActivityState.ACTIVE:
                all_completed = False
                status[child] = ActivityState.ACTIVE

        if all_completed:
            status[region.children[0]] = ActivityState.COMPLETED

    # Exclusive gateway
    if region.children:
        for child in region.children:
            if status[child] == ActivityState.ACTIVE or status[child] == ActivityState.COMPLETED:
                status[region] = status[child]
                break

class CounterExecution:

    def saturate(self, ctx: "ContextType", marking: "MarkingType", regions:dict[int: "RegionModelType"], status: dict["RegionModelType", "ActivityState"]):
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
            execution_time += min_delta

            if any(map(lambda t: t.stop, transitions_to_fire)):
                logger.debug("Stop transition found, exiting saturation")
                break

            for t in transitions_to_fire:
                region = regions[int(t.region_id)]
                status[region]= ActivityState.ACTIVE
                logger.debug(f"Executing transition {t}")
                current_marking, p, imp = execute_transition(ctx, t, current_marking)
                probability *= p
                impacts = add_impacts(impacts, imp or default_impacts)
                logger.debug(
                    f"After executing {t}, marking {current_marking}, probability {probability}, impacts {impacts}, execution_time {execution_time}")

        # Update completed tasks status
        for p in ctx.net.places:
            if int(p.name) in regions and regions[int(p.name)].is_task() and status[regions[int(p.name)]] == ActivityState.ACTIVE: #regions:dict[int: "RegionModelType"],
                region = regions[int(p.name)] #Place name is region id

                remaining_time = float(p.duration) - current_marking[p].age

                #print("Checking: ", p.name, region.label,"remaining_time:",  remaining_time, str(status[region]))
                if remaining_time <= 0:
                    print("Completed: ", p.name, region.label,str(status[region]))
                    status[region] = ActivityState.COMPLETED

        parse(regions[0], status)

        logger.debug(
            f"Saturation complete. Final marking {current_marking}, probability {probability}, impacts {impacts}, execution_time {execution_time}")
        return current_marking, probability, impacts, execution_time

    def consume(self, ctx: "ContextType", marking: "MarkingType", regions:dict[int: "RegionModelType"], status: dict["RegionModelType", "ActivityState"], decisions: list["TransitionType"] | None = None):
        logger.debug(f"Consuming marking {marking}")
        if decisions is None:
            decisions = []

        logger.debug("User decisions: %s", decisions)
        decisions = get_default_choices(ctx, marking, decisions)
        logger.debug("Final decisions after adding defaults and filter: %s", decisions)

        impacts = get_empty_impacts(ctx.net)
        default_impacts = get_empty_impacts(ctx.net)
        # No extra time added for choices, assuming immediate execution
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
                f"After executing decisions {t}, marking {current_marking}, probability {probability}, impacts {impacts}, execution_time {execution_time}")

        new_marking, prob, imp, exec_time = self.saturate(ctx, current_marking, regions, status)
        probability *= prob
        impacts = [imp1 + imp2 for imp1, imp2 in zip(impacts, imp)]
        execution_time += exec_time

        logger.debug(
            f"Consumption complete. Final marking {new_marking}, probability {probability}, impacts {impacts}, execution_time {execution_time}")
        return new_marking, probability, impacts, execution_time, decisions
