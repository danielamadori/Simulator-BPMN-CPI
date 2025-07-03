# import pytest
# from pm4py import Marking
#
# from model.extree import ExTree
# from model.snapshot import Snapshot
# from model.time_spin import TimeMarking
#
#
# @pytest.fixture
# def snapshot():
#     tm = TimeMarking(Marking(a=1, b=0, c=0, d=0, e=0))
#     _snapshot = Snapshot(tm, 0.8, [5, 2], 2)
#
#     return _snapshot
#
#
# @pytest.fixture
# def extree(snapshot):
#     tree = ExTree(snapshot)
#
#     return tree
#
#
# def test_add(extree, snapshot):
#     assert len(extree.get_nodes()) == 1
#
#     parent_node = extree.current_node
#     new_node = extree.add_snapshot(snapshot)
#
#     assert new_node in extree
#     assert extree.set_current(parent_node)
#     assert extree.current_node == parent_node
#     assert extree.add_snapshot(snapshot) == new_node
#     assert len(extree) == 2
