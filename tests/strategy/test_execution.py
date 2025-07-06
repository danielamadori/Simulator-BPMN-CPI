import math
import os

import pytest

from model.context import NetContext
from model.endpoints.execute.response import petri_net_to_dot
from model.region import RegionModel
from model.time_spin import TimeMarking
from utils.net_utils import NetUtils

PWD = "/home/matthewexe/Documents/Uni/Tirocinio/code"

@pytest.fixture
def ctx():
    with open(os.path.join(PWD, "tests/iron.json")) as f:
        model = RegionModel.model_validate_json(f.read())

    return NetContext.from_region(model)


@pytest.fixture
def marking(ctx):
    _net, im, fm = ctx.net, ctx.initial_marking, ctx.final_marking

    new_base_marking = {k: 0 for k in im.keys()}
    for p in _net.places:
        if NetUtils.Place.get_entry_id(p) in ['5', '6']:
            print("FOUND")
            new_base_marking[p] = 1

    return TimeMarking(new_base_marking)


@pytest.fixture
def nature_ctx():
    with open(os.path.join(PWD, "tests/input_data/bpmn_nature.json")) as f:
        model = RegionModel.model_validate_json(f.read())

    return NetContext.from_region(model)


def test_saturate(nature_ctx):
    strategy = nature_ctx.strategy
    net, im, fm = nature_ctx.net, nature_ctx.initial_marking, nature_ctx.final_marking
    sat_m, delta = strategy.saturate(nature_ctx, im)

    assert sat_m == im
    assert delta == 0

    sem = nature_ctx.semantic
    for t in sem.enabled_transitions(net, sat_m):
        sat_m = sem.fire(net, t, sat_m)
        break

    sat_m, delta = strategy.saturate(nature_ctx, sat_m)

    assert sat_m != im
    assert delta != 0


def test_consume(ctx, marking):
    _net, _, fm = ctx.net, ctx.initial_marking, ctx.final_marking

    strategy = ctx.strategy
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

    # dot_string = petri_net_to_dot(ctx.net, marking, fm)

    bho = strategy.consume(ctx, marking, choices)
    consumed_m, _p, _i, _t = bho

    # petri_net_to_dot(ctx.net, consumed_m, fm)



    assert type(_i) == list

    assert math.isclose(_p, 0.8)
    assert _i == [38, 2]
    assert math.isclose(_t, 1)
