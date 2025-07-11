import pytest

from model.context import NetContext
from model.extree import ExTree
from model.region import RegionModel
from model.petri_net.time_spin import TimeMarking


@pytest.fixture
def iron_region():
    with open("tests/iron.json") as f:
        content = f.read()

    return RegionModel.model_validate_json(content)

def test_from_region(iron_region):
    ctx = NetContext.from_region(iron_region)

    assert ctx.initial_marking is not None and isinstance(ctx.initial_marking, TimeMarking)
    assert ctx.final_marking is not None and isinstance(ctx.final_marking, TimeMarking)

def test_tree_from_context(iron_region):
    tree = ExTree.from_context(NetContext.from_region(iron_region))
