import pytest
from pm4py.objects.bpmn.obj import Marking

from converter.spin import from_region
from model.region import RegionModel
from model.petri_net.time_spin import TimeMarking, TimeNetSematic


@pytest.fixture()
def iron_net():
    with open("tests/iron.json") as f:
        _json = f.read()

    r_obj = RegionModel.model_validate_json(_json)
    _net, _im, _fm = from_region(r_obj)

    yield _net, _im, _fm

    del _net
    del r_obj
    del _json


@pytest.fixture()
def marking(iron_net):
    _m = iron_net[1]
    age = _m.age
    for p in _m.marking:
        if len(p.in_arcs) == 0:
            age[p] = 1

    return TimeMarking(_m.marking, age)


class TestTimeSemantic:

    def test_is_enabled(self, iron_net, marking):
        active_transition = None
        other_transition = None
        net, _, _ = iron_net

        for p in net.places:
            if len(p.in_arcs) == 0:
                active_transition = list(p.out_arcs)[0].target
            elif not other_transition:
                other_transition = list(p.out_arcs)[0].target

        sem = TimeNetSematic()

        assert sem.is_enabled(net, active_transition, marking) == True
        assert sem.is_enabled(net, other_transition, marking) == False

        assert sem.enabled_transitions(net, marking) == {active_transition}

    def test_execute(self, iron_net, marking):
        net, im, _ = iron_net
        semantic = TimeNetSematic()
        en_t = semantic.enabled_transitions(net, marking)
        next_places = set()

        t = list(en_t)[0]
        if t.out_arcs:
            next_places.add(list(t.out_arcs)[0].target)

        _m = Marking()
        for p in net.places:
            if p in next_places:
                _m[p] = 1
            else:
                _m[p] = 0

        expected_time_marking = TimeMarking(_m)
        real_time_marking = semantic.execute(net, t, marking)

        # print(f"Current: {real_time_marking}")
        # print(f"Expected: {expected_time_marking}")
        assert real_time_marking == expected_time_marking
