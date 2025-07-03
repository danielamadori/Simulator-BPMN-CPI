import json
from functools import singledispatch

from pm4py import PetriNet

from model.context import NetContext
from model.extree import ExTree
from model.snapshot import Snapshot
from src.model.types import N, M, P, T
from utils.net_utils import NetUtils


@singledispatch
def serialize(obj):
    raise NotImplementedError()


@serialize.register
def _(obj: NetContext):
    net = serialize(obj.net)
    initial_marking = serialize(obj.initial_marking)
    final_marking = serialize(obj.final_marking)
    return json.dumps({
        "net": net,
        "initial_marking": initial_marking,
        "final_marking": final_marking,
        "semantic": obj.semantic.__class__.__name__,
        "strategy": obj.strategy.__class__.__name__,
    })


# Petri Net serialization
@serialize.register
def _(obj: N):
    places = [serialize(place) for place in obj.places]
    transitions = [serialize(transition) for transition in obj.transitions]
    arcs = [serialize(arc) for arc in obj.arcs]

    return json.dumps({
        "name": obj.name,
        "places": places,
        "transitions": transitions,
        "arcs": arcs,
    })


@serialize.register
def _(obj: P):
    prop = {
        "id": obj.name,
        "type": str(NetUtils.get_type(obj)),
        "label": NetUtils.get_label(obj),
        "entry_region_id": NetUtils.Place.get_entry_id(obj),
        "exit_region_id": NetUtils.Place.get_exit_id(obj),
        "impacts": json.dumps(NetUtils.Place.get_impacts(obj)),
        "duration": NetUtils.Place.get_duration(obj),
    }

    return json.dumps(prop)


@serialize.register
def _(obj: M):
    result = {}
    for key in obj.keys():
        token, age = obj[key]
        result[key] = {
            "token": token,
            "age": age
        }

    return json.dumps(result)


@serialize.register
def _(obj: T):
    prop = {
        "id": obj.name,
        "type": str(NetUtils.get_type(obj)),
        "label": NetUtils.get_label(obj),
        "region_id": NetUtils.Transition.get_region_id(obj),
        "probability": NetUtils.Transition.get_probability(obj),
        "stop": NetUtils.Transition.get_stop(obj),
    }

    return json.dumps(prop)


@serialize.register
def _(obj: PetriNet.Arc):
    prop = {
        "source": obj.source.name,
        "target": obj.target.name,
        "weight": obj.weight,
    }

    return json.dumps(prop)


# Execution Tree serialization
@serialize.register
def _(obj: ExTree):
    nodes = []
    for node in obj.get_nodes():
        nodes.append({
            "parent": node.parent.id if node.parent else None,
            "snapshot": serialize(node.snapshot),
            "children": [child.id for child in node.children],
        })

    return json.dumps({
        "current_node": obj.current_node.id,
        "nodes":nodes
    })


@serialize.register
def _(obj: Snapshot):
    return json.dumps({
        "marking": serialize(obj.marking),
        "time": obj.execution_time,
        "impacts": obj.impacts,
        "probability": obj.probability,
    })
