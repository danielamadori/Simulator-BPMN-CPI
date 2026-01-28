import pathlib
import pytest

from model.extree import ExecutionTree
from model.extree.node import Snapshot
from strategy.execution import ClassicExecution, get_default_choices
from utils.net_utils import get_empty_impacts

PWD = pathlib.Path(__file__).parent.parent.parent.absolute()


@pytest.fixture
def region_model():
    """Fixture to load the region model"""
    import os

    with open(os.path.join(PWD, "tests/input_data/bpmn_choice.json")) as f:
        from model.region import RegionModel

        model = RegionModel.model_validate_json(f.read())
    return model


@pytest.fixture
def ctx(region_model):
    """Fixture to create a NetContext from the region model"""
    from model.context import NetContext

    context = NetContext.from_region(region_model)
    context.strategy = ClassicExecution()
    return context


@pytest.fixture
def initial_snapshot(ctx):
    return Snapshot(ctx.initial_marking, 1, [0, 0], 0, {}, [], [])


@pytest.fixture
def extree(initial_snapshot):
    tree = ExecutionTree(initial_snapshot)
    return tree


@pytest.fixture
def saturated_snapshot(ctx, initial_snapshot):
    """Create a saturated snapshot based on the initial snapshot"""
    saturated_marking, delta = ctx.strategy.saturate(ctx, initial_snapshot.marking)
    choices = get_default_choices(ctx, saturated_marking)
    if choices:
        transition = choices[0]
        saturated_marking = ctx.semantic.execute(ctx.net, transition, saturated_marking)
        probability = transition.probability
    else:
        probability = 1
    impacts = get_empty_impacts(ctx.net)

    return Snapshot(saturated_marking, probability, impacts, delta, {}, [], [])


def test_add(ctx, extree, saturated_snapshot, initial_snapshot):
    assert len(extree.get_nodes()) == 1

    saturated_marking, delta = ctx.strategy.saturate(ctx, initial_snapshot.marking)
    choices = get_default_choices(ctx, saturated_marking)

    parent_node = extree.current_node
    new_node = extree.add_snapshot(ctx, saturated_snapshot, choices)
    sat_marking, _ = ctx.strategy.saturate(ctx, ctx.initial_marking)

    assert new_node in extree
    assert len(extree) == 2

    # Check set current node
    assert extree.set_current(parent_node)
    assert extree.current_node == parent_node

    # Check adding the same snapshot again does not create a new node
    assert extree.add_snapshot(ctx, saturated_snapshot, choices) == new_node
    assert len(extree) == 2
