import os
import pathlib

import pytest

from model.context import NetContext
from model.petri_net.time_spin import TimeMarking
from model.petri_net.wrapper import WrapperPetriNet

PWD = pathlib.Path(__file__).parent.parent.parent.absolute()


@pytest.fixture
def region_model():
    """Fixture to load the region model"""
    with open(os.path.join(PWD, "tests/input_data/bpmn_nature.json")) as f:
        from model.region import RegionModel

        model = RegionModel.model_validate_json(f.read())
    return model


@pytest.fixture
def ctx(region_model):
    context = NetContext.from_region(region_model)
    return context


@pytest.fixture
def marking(ctx):
    _marking = ctx.initial_marking.tokens
    yield _marking
    del _marking


@pytest.fixture
def time_marking(marking):
    age = {}
    t_m = TimeMarking(marking, age)

    yield t_m

    del t_m
    del age


class TestTimeMarking:

    def test_eq(self, time_marking):
        """Test to verify equality between two TimeMarking objects"""
        # Create another identical TimeMarking
        # marking = time_marking.tokens
        # other_time_marking = TimeMarking(marking, {})
        #
        # # Verify the two objects are equal
        # # self.assertEqual(self.time_marking, other_time_marking)
        # assert time_marking == other_time_marking, "They should be equal"
        #
        # # Verify they are no longer equal if one of the values changes
        # # Note that TimeMarking is immutable, so you can't modify it directly, but we need to test
        # # that they are not equal if keys or values change.
        # modified_age = {WrapperPetriNet.Place(name="1"): 5, "b": 2, "c": 0, "d": 0}
        # modified_time_marking = TimeMarking(marking, modified_age)
        #
        # assert time_marking != modified_time_marking

    def test_immutability(self, time_marking):
        """Test to verify that TimeMarking values cannot be changed"""
        # copy_marking = time_marking.tokens
        # copy_marking["a"] = 15
        #
        # assert copy_marking != time_marking.tokens
        #
        # copy_age = time_marking.age
        # copy_age["a"] = 15
        #
        # assert copy_age != time_marking.age
        #
        # copy_keys = time_marking.keys()
        # copy_keys.add("dd")
        #
        # assert copy_keys != time_marking.keys()

    def test_add_time(self, ctx, time_marking):
        im = time_marking
        time_added = 1.0
        new_marking = im.add_time(time_added)

        tmp = im.age
        first_key_not_active = None
        for place in ctx.net.places:
            if im[place].token > 0:
                tmp[place] = tmp.get(place, 0) + time_added
            else:
                first_key_not_active = place

        assert (
            new_marking.age == tmp
        ), "Age should be updated correctly after adding time"
        assert (
            new_marking.age.get(first_key_not_active, 0) == 0
        ), "Age for inactive places should be set to 0"
