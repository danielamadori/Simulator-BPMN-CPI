import math
import os
import pathlib

import pytest
from pm4py import Marking

from model.context import NetContext
from model.region import RegionModel
from model.petri_net.time_spin import TimeMarking

PWD = pathlib.Path(__file__).parent.parent.parent.absolute()


@pytest.fixture
def ctx():
    with open(os.path.join(PWD, "tests/iron.json")) as f:
        model = RegionModel.model_validate_json(f.read())

    return NetContext.from_region(model)


@pytest.fixture
def saturated_initial_marking(ctx):
    _net, im, fm = ctx.net, ctx.initial_marking, ctx.final_marking

    new_base_marking = Marking()
    for p in _net.places:
        if p.entry_id in ['5', '6']:
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


def test_consume(ctx, saturated_initial_marking):
    _net, _, fm = ctx.net, ctx.initial_marking, ctx.final_marking

    strategy = ctx.strategy
    choices = []
    for t in _net.transitions:
        if t.region_id == "6":
            if (
                    t.probability == 0.8
                    and t.stop == True
            ):
                choices.append(t)
        if (
                t.region_id == "5"
                and t.stop == True
        ):
            if list(t.out_arcs)[0].target.entry_id == "12":
                choices.append(t)

    bho = strategy.consume(ctx, saturated_initial_marking, choices)
    consumed_m, _p, _i, _t = bho

    assert type(_i) == list

    assert math.isclose(_p, 0.8)
    assert _i == [38, 2]
    assert math.isclose(_t, 1)
