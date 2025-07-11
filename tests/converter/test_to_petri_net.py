from typing import Tuple

import pytest

from converter.spin import from_region
from model.petri_net.wrapper import PetriNet
from model.region import RegionModel, RegionType
from utils.net_utils import PropertiesKeys


@pytest.fixture()
def task():
    with open("tests/input_data/bpmn_task.json") as f:
        _json = f.read()
    _t = RegionModel.model_validate_json(_json)
    yield _t
    del _t


@pytest.fixture()
def parallel():
    with open("tests/input_data/bpmn_parallel.json") as f:
        _json = f.read()
    _t = RegionModel.model_validate_json(_json)
    yield _t
    del _t


@pytest.fixture()
def choice():
    with open("tests/input_data/bpmn_choice.json") as f:
        _json = f.read()
    _t = RegionModel.model_validate_json(_json)
    yield _t
    del _t


@pytest.fixture()
def nature():
    with open("tests/input_data/bpmn_nature.json") as f:
        _json = f.read()
    _t = RegionModel.model_validate_json(_json)
    yield _t
    del _t


def get_region_ids(region: RegionModel, *types: RegionType):
    _ids = set()

    if not types:
        types = [
            RegionType.TASK,
            RegionType.NATURE,
            RegionType.CHOICE,
            RegionType.PARALLEL,
        ]

    def __apply(_r: RegionModel):
        if _r.is_task() and RegionType.TASK in types:
            _ids.add(_r.id)
            return

        _ids.add(_r.id)
        for child in _r.children:
            if child.type in types:
                __apply(child)

    __apply(region)

    return _ids


def get_region_props_from_net(
        net: PetriNet,
        region: RegionModel,
        keys: Tuple[PropertiesKeys] = None,
        types: Tuple[RegionType] = None,
):
    if keys is None:
        return None
    if types is None:
        types = ()

    _dict = {rid: {} for rid in get_region_ids(region, *types)}

    for p in net.places:
        rid = (
                p.properties[PropertiesKeys.ENTRY_RID]
                or p.properties[PropertiesKeys.EXIT_RID]
        )
        for key_prop in keys:
            if key_prop not in p.properties.keys():
                continue
            prop = p.properties[key_prop]
            if prop is not None:
                if key_prop != PropertiesKeys.DURATION or (
                        _dict[rid].get(key_prop, 0) == 0
                ):
                    _dict[rid].update({key_prop: prop})

    for t in net.transitions:
        rid = t.properties[PropertiesKeys.ENTRY_RID]
        for key_prop in keys:
            if key_prop not in t.properties.keys():
                continue
            prop = t.properties[key_prop]
            if prop is not None:
                _dict[rid].update({key_prop: prop})

    return _dict


def pytest_generate_tests(metafunc):
    if "region_fixture" in metafunc.fixturenames:
        metafunc.parametrize(
            "region_fixture", ["parallel", "choice", "nature"], scope="class"
        )


class TestBaseRegion:

    @pytest.fixture(autouse=True)
    def setup_region(self, request, region_fixture):
        self.region = request.getfixturevalue(region_fixture)
        self.net, self.im, self.fm = from_region(self.region)
        self.first_place = None
        self.last_place = None
        for p in self.net.places:
            if (
                    p.properties[PropertiesKeys.ENTRY_RID]
                    and not p.properties[PropertiesKeys.EXIT_RID]
            ):
                self.first_place = p
            elif (
                    not p.properties[PropertiesKeys.ENTRY_RID]
                    and p.properties[PropertiesKeys.EXIT_RID]
            ):
                self.last_place = p

    def test_entry_exit_places(self):
        assert self.first_place is not None
        assert self.last_place is not None

    def test_type_property_matches(self):
        props = get_region_props_from_net(
            self.net, self.region, keys=[PropertiesKeys.TYPE]
        )

        done = False
        for rid, data in props.items():
            if self.region.id != rid:
                continue
            else:
                done = True
            assert data[PropertiesKeys.TYPE] in (
                self.region.type,
                self.region.type.value,
            )

        assert done

    def test_children(self):
        if not self.region.children:
            assert True

        child_ids = {r.id for r in self.region.children}
        child_ids.add(self.region.id)
        place_child_rids = (
            a.target.properties[PropertiesKeys.ENTRY_RID]
            for a in self.first_place.out_arcs
        )

        for child_id in place_child_rids:
            assert child_id in child_ids

    def test_duration(self):
        keys = [PropertiesKeys.DURATION]
        props = get_region_props_from_net(self.net, self.region, keys=keys)

        assert props[self.region.id][PropertiesKeys.DURATION] == self.region.duration
        assert (
                list(
                    filter(
                        lambda p: p.properties[PropertiesKeys.EXIT_RID] == self.region.id,
                        self.net.places,
                    )
                )[0].properties[PropertiesKeys.DURATION]
                == 0
        )


class TestTask:

    def test_entry_exit(self, task):
        net, _, _ = from_region(task)
        rid_keys = (PropertiesKeys.ENTRY_RID, PropertiesKeys.EXIT_RID)
        _entry_exit_dict = get_region_props_from_net(net, task, keys=rid_keys)

        for rid in _entry_exit_dict:
            cur = _entry_exit_dict[rid]
            assert cur.get(PropertiesKeys.ENTRY_RID) is not None
            assert cur.get(PropertiesKeys.EXIT_RID) is not None

    def test_other_props(self, task: RegionModel):
        net, _, _ = from_region(task)
        rid_keys = (
            PropertiesKeys.LABEL,
            PropertiesKeys.DURATION,
            PropertiesKeys.IMPACTS,
            PropertiesKeys.TYPE,
        )
        _entry_exit_dict = get_region_props_from_net(net, task, keys=rid_keys)

        for rid in _entry_exit_dict:
            cur = _entry_exit_dict[rid]
            assert cur.get(PropertiesKeys.LABEL) == task.label
            assert cur.get(PropertiesKeys.DURATION) == task.duration
            assert cur.get(PropertiesKeys.IMPACTS) == task.impacts
            assert (
                    cur.get(PropertiesKeys.TYPE) == task.type
                    or cur.get(PropertiesKeys.TYPE) == task.type.value
            )
