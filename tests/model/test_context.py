import os
import pathlib

import pytest

from model.context import NetContext
from model.extree import ExecutionTree
from model.region import RegionModel
from model.petri_net.time_spin import TimeMarking

PWD = pathlib.Path(__file__).parent.parent.parent.absolute()


@pytest.fixture
def iron_region():
    with open(os.path.join(PWD, "tests/iron.json")) as f:
        content = f.read()

    return RegionModel.model_validate_json(content)

def test_from_region(iron_region):
    ctx = NetContext.from_region(iron_region)

    assert ctx.initial_marking is not None and isinstance(ctx.initial_marking, TimeMarking)
    assert ctx.final_marking is not None and isinstance(ctx.final_marking, TimeMarking)

def test_tree_from_context(iron_region):
    ctx = NetContext.from_region(iron_region)
    tree = ExecutionTree.from_context(ctx, iron_region)
    assert tree is not None
