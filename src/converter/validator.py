import logging
import math

from model.region import RegionModel, RegionType

logger = logging.getLogger(__name__)


def region_validator(region: RegionModel):
    def explore(_r: RegionModel, expected_impact_length: int = None):
        # logger.debug(f"Exploring the Region: {_r.label} id:{_r.id}")
        # checks for all region types
        if _r.id is None or not isinstance(_r.type, RegionType):
            logger.error(
                f"Region id or type {region.label} id:{region.id} is None or empty"
            )
            return False, None

        if _r.duration is None or _r.duration < 0:
            logger.error(
                f"Region {region.label} id:{region.id} has duration {region.duration} (< 0 or None)"
            )
            return False, None

        # validate the region based on its type
        status, expected_impact_length = __switch_case(_r, expected_impact_length)

        #logger.debug(f"Expected_Value:{expected_impact_length}")

        if status is False:
            return False, None

        if _r.bound is not None and _r.type is not RegionType.LOOP:
            return False, None

        # if there are children
        if _r.children:
            val = expected_impact_length
            for child in _r.children:
                # if the child or its children are not valid
                st, val = explore(child, val)
                if not st:
                    return False, None

        return True, expected_impact_length

    return explore(region, expected_impact_length=None)[0]


def __switch_case(region: RegionModel, expected_impact_length: int = None):
    # map region type to validator function
    switch = {
        RegionType.SEQUENTIAL: __sequential_validator,
        RegionType.TASK: __task_validator,
        RegionType.PARALLEL: __parallel_validator,
        RegionType.CHOICE: __choice_validator,
        RegionType.NATURE: __nature_validator,
        RegionType.LOOP: __loop_validator
    }

    validator_fn = switch.get(region.type)

    if not validator_fn:
        print(
            f"Unsupported region type: {region.type} in region {region.label} with id: {region.id}"
        )
        return False, None

    return validator_fn(region, expected_impact_length)


def __sequential_validator(region: RegionModel, expected_impact_length: int = None):
    # logger.debug("Sequential validator")
    # a sequential region must have at least 2 children
    if not region.children or len(region.children) < 2:
        logger.error(
            f"Sequential region {region.label} id:{region.id} has fewer than 2 children: {len(region.children or [])}"
        )
        return False, None
    if len(region.children) > 2:
        logger.error(
            f"Sequential region {region.label} id:{region.id} has more than 2 children: {len(region.children)}"
        )
        return False, None

    # must not have impacts
    if region.impacts:
        logger.error(
            f"Sequential region {region.label} id:{region.id} has impacts: {region.impacts}"
        )
        return False, None

    # must not have probability distributions
    if region.distribution is not None:
        logger.error(
            f"Sequential region {region.label} id:{region.id} has probability distribution: {region.distribution}"
        )
        return False, None

    # duration???

    return True, expected_impact_length


def __task_validator(region: RegionModel, expected_impact_length: int = None):
    # logger.debug("Task validator")
    # logger.debug(f"My impacts are: {region.impacts}")
    # logger.debug(f"expected_impact_length = {expected_impact_length}")

    if not region.impacts:
        logger.error(
            f"Task region {region.label} id:{region.id} has no impacts: {region.impacts}"
        )
        return False, expected_impact_length

    for impact in region.impacts:
        if impact < 0:
            logger.error(
                f"Task region {region.label} id:{region.id} has negative impacts: {region.impacts}"
            )
            return False, expected_impact_length

    if expected_impact_length is None:
        expected_impact_length = len(region.impacts)
        # logger.debug(
        #     f"Set impact length from {region.label} id: {region.id} to {expected_impact_length}"
        # )
    elif len(region.impacts) != expected_impact_length:
        logger.error(
            f"Task region {region.label} id:{region.id} has an impacts length mismatch ({len(region.impacts or [])} vs {expected_impact_length})"
        )
        return False, expected_impact_length

    if region.children:
        logger.error(
            f"Task region {region.label} id:{region.id} has children: {region.children}"
        )
        return False, expected_impact_length

    if region.distribution:
        logger.error(
            f"Task region {region.label} id:{region.id} has probability distribution: {region.distribution}"
        )
        return False, expected_impact_length

    return True, expected_impact_length


def __parallel_validator(region: RegionModel, expected_impact_length: int = None):
    # logger.debug("Parallel validator")
    # must have at least 2 children
    if region.children is None or len(region.children) < 2:
        logger.error(
            f"Parallel region {region.label} id:{region.id} does not have at least 2 children: {len(region.children or [])}"
        )
        return False, None

    # must not have impacts
    if region.impacts:
        logger.error(
            f"Parallel region {region.label} id:{region.id} has impacts: {region.impacts}"
        )
        return False, None

    # must not have probability distributions
    if region.distribution is not None:
        logger.error(
            f"Parallel region {region.label} id:{region.id} has distribution: {region.distribution}"
        )
        return False, None

    # duration??

    return True, expected_impact_length


def __nature_validator(region: RegionModel, expected_impact_length: int = None):
    # logger.debug("Nature validator")
    # must have at least 2 children
    if region.children is None or len(region.children) < 2:
        logger.error(
            f"Nature region {region.label} id:{region.id} does not have at least 2 children: {len(region.children or [])}"
        )
        return False, None

    if region.distribution is None and not isinstance(region.distribution, list):
        logger.error(
            f"Choice region {region.label} id:{region.id} does not have a probability distribution: {region.distribution}"
        )
        return False, None

    # must have a probability distribution and len(prob) = number of children
    if region.distribution is None or not isinstance(region.distribution, list) or len(region.distribution) != len(
            region.children or []
    ):
        logger.error(
            f"Nature region {region.label} id:{region.id} does not have a probability distribution or len(prob) != number of children"
        )
        return False, None

    # the probability distribution sum should be close to 1
    prob_sum = sum(region.distribution)
    if not math.isclose(prob_sum, 1.0, rel_tol=1e-9):
        logger.error(
            f"Nature region {region.label} id:{region.id} does not sum to 1: {prob_sum}"
        )
        return False, None

    # must not have impacts
    if region.impacts:
        logger.error(
            f"Nature region {region.label} id:{region.id} has impacts: {region.impacts}"
        )
        return False, None

    # duration?

    return True, expected_impact_length


def __choice_validator(region: RegionModel, expected_impact_length: int = None):
    # logger.debug("Choice validator")
    # must have at least 2 children
    if region.children is None or len(region.children) < 2:
        logger.error(
            f"Choice region {region.label} id:{region.id} does not have at least 2 children: {len(region.children or [])}"
        )
        return False, None

    # must not have a probability distribution
    if region.distribution is not None:
        logger.error(f"Choice region {region.label} id:{region.id} must not have probabilities")

    # if a probability distribution is provided, it must be close to 1
    if region.distribution:
        prob_sum = sum(region.distribution)
        if not math.isclose(prob_sum, 1.0, rel_tol=1e-9):
            logger.error(
                f"Choice region {region.label} id:{region.id} has a probability sum that does not equal 1: {prob_sum}"
            )
            return False, None

    # must not have impacts
    if region.impacts:
        logger.error(
            f"Choice region {region.label} id:{region.id} has impacts: {region.impacts}"
        )
        return False, None

    # duration?

    return True, expected_impact_length


def __loop_validator(region: RegionModel, expected_impact_length: int = None):
    # logger.debug("Loop validator")
    children = region.children
    if children is None or len(children) != 1:
        logger.error(
            f"Loop region {region.id} must have exactly one child, found: {len(children or [])}"
        )
        return False, None

    if not isinstance(region.distribution, float) or region.distribution is None:
        logger.error(f"Loop region {region.id} must have a float probability distribution")
        return False, None

    if region.bound is None or not isinstance(region.bound, (int, float)):
        logger.error(f"Loop region {region.id} must have a defined bound")
        return False, None

    return True, expected_impact_length
