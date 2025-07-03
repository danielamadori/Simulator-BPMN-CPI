import pytest

from model.extree import ExTree
from model.snapshot import Snapshot

PWD = "/home/matthewexe/Documents/Uni/Tirocinio/code"

@pytest.fixture
def region_model():
    """Fixture to load the region model"""
    import os
    with open(os.path.join(PWD, "tests/input_data/bpmn_nature.json")) as f:
        from model.region import RegionModel
        model = RegionModel.model_validate_json(f.read())
    return model

@pytest.fixture
def ctx(region_model):
    """Fixture to create a NetContext from the region model"""
    from model.context import NetContext
    context = NetContext.from_region(region_model)
    return context

@pytest.fixture
def initial_snapshot(ctx):
    return Snapshot(ctx.initial_marking, 1, [0,0], 0)

@pytest.fixture
def extree(initial_snapshot):
    tree = ExTree(initial_snapshot)
    return tree

@pytest.fixture
def saturated_snapshot(ctx, initial_snapshot):
    """Create a saturated snapshot based on the initial snapshot"""
    saturated_marking, delta = ctx.strategy.saturate(ctx, initial_snapshot.marking)
    # Consuming the initial marking to create a saturated snapshot
    saturated_marking, probability, impacts, delta = ctx.strategy.consume(ctx, saturated_marking)

    return Snapshot(
        saturated_marking,
        probability,
        impacts,
        delta
    )


def test_add(ctx, extree, saturated_snapshot):
    assert len(extree.get_nodes()) == 1

    parent_node = extree.current_node
    new_node = extree.add_snapshot(ctx, saturated_snapshot)
    assert new_node in extree
    assert len(extree) == 2

    # Check set current node
    assert extree.set_current(parent_node)
    assert extree.current_node == parent_node

    # Check adding the same snapshot again does not create a new node
    assert extree.add_snapshot(ctx, saturated_snapshot) == new_node
    assert len(extree) == 2
