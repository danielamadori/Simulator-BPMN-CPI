from enum import Enum
import json
import pytest

from converter.spin import from_region
from model.region import RegionModel
from model.time_spin import TimeNetSematic, TimeMarking
from strategy.execution import ClassicExecution
from utils.net_utils import NetUtils, PropertiesKeys
import math


@pytest.fixture
def net():
    with open("tests/iron.json") as f:
        model = RegionModel.model_validate_json(f.read())

    _net, im, fm = from_region(model)
    return _net, im, fm


@pytest.fixture
def marking(net):
    _net, im, fm = net

    new_base_marking = {k:0 for k in im.keys()}
    for p in _net.places:
        if NetUtils.Place.get_entry_id(p) in ['5','6']:
            print("FOUND")
            new_base_marking[p] = 1

    return TimeMarking(new_base_marking)


@pytest.fixture
def nature():
    with open("tests/input_data/bpmn_nature.json") as f:
        model = RegionModel.model_validate_json(f.read())

    return from_region(model)


def test_saturate(nature):
    strategy = ClassicExecution()
    net, im, fm = nature
    sat_m, delta = strategy.saturate(net, im)

    assert sat_m == im
    assert delta == 0

    sem = TimeNetSematic()
    for t in sem.enabled_transitions(net, sat_m):
        sat_m = sem.fire(net, t, sat_m)
        break

    sat_m, delta = strategy.saturate(net, sat_m)

    assert sat_m != im
    assert delta != 0


def test_consume(net, marking):
    _net, _, fm = net

    strategy = ClassicExecution()
    choices = []
    for t in _net.transitions:
        if NetUtils.Transition.get_region_id(t) == "6":
            if (
                NetUtils.Transition.get_probability(t) == 0.8
                and NetUtils.Transition.get_stop(t) == True
            ):
                choices.append(t)
        if (
            NetUtils.Transition.get_region_id(t) == "5"
            and NetUtils.Transition.get_stop(t) == True
        ):
            if NetUtils.Place.get_entry_id(list(t.out_arcs)[0].target) == "12":
                choices.append(t)

    final_place = None
    for p in _net.places:
        if NetUtils.Place.get_entry_id(p) == "1":
            final_place = p
            break

    consumed_m, _p, _i, _t = strategy.consume(_net, marking, choices)

    assert math.isclose(_p, 0.8)
    assert _i == [38, 2]
    assert math.isclose(_t, 1)
