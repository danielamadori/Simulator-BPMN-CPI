# from __future__ import annotations
from enum import Enum

# from dataclasses import dataclass
from typing import Dict, Generic, TypeVar

from pm4py.objects.petri_net.obj import Marking, PetriNet
from pm4py.objects.petri_net.semantics import PetriNetSemantics

# from pm4py.objects.petri_net.utils.petri_utils import add_place, add_arc_from_to, add_transition


class TimeMarking:
    def __init__(self, marking: Marking, age: Dict[str, float] = None):
        if age is None:
            age = {}

        self._marking = marking.copy()
        self._age = age.copy()
        self._keys = set(marking.keys())

        # Verifica che le chiavi di `marking` siano un superset delle chiavi di `age`
        if not self._keys.issuperset(age.keys()):
            raise ValueError(f"Invalid keys in 'age': {age.keys() - self._keys}")

        # Aggiungi le chiavi di default a `_age` se non sono presenti
        for x in self._keys:
            if x not in self._age:
                self._age[x] = 0

    @property
    def marking(self):
        return (
            self._marking.copy()
        )  # Restituisce una copia per mantenere l'immutabilità

    @property
    def age(self):
        return self._age.copy()  # Restituisce una copia per mantenere l'immutabilità

    def keys(self):
        return self._keys.copy()

    def __getitem__(self, key: str):
        if key not in self._keys:
            raise KeyError(f"Invalid key: '{key}' does not exists.")
        return (self.marking[key], self.age[key])

    def __contains__(self, el):
        return el in self._keys

    def __eq__(self, other):
        if not isinstance(other, TimeMarking):
            return False

        if self.keys() != other.keys():
            return False

        for key in self._keys:
            if self[key] != other[key]:
                return False

        return True

    def __repr__(self):
        result = {k: self[k] for k in self.keys()}
        return repr(result)

    def __str__(self):
        return repr(self)


N = TypeVar("N", bound=PetriNet)
T = TypeVar("T", bound=PetriNet.Transition)
P = TypeVar("P", bound=PetriNet.Place)
M = TypeVar("M", bound=TimeMarking)


class NetUtils:

    @classmethod
    def get_label(cls, node: P | T):
        return node.properties.get(PropertiesKeys.LABEL)

    @classmethod
    def get_type(cls, node: P | T):
        return node.properties.get(PropertiesKeys.TYPE)

    class Place:

        @classmethod
        def get_duration(cls, node: P | T):
            return node.properties.get(PropertiesKeys.DURATION, 0)

        @classmethod
        def get_entry_id(cls, place: P):
            return place.properties.get(PropertiesKeys.ENTRY_RID)

        @classmethod
        def get_exit_id(cls, place: P):
            return place.properties.get(PropertiesKeys.EXIT_RID)

    class Transition:

        @classmethod
        def get_region_id(cls, transition: T):
            return transition.properties.get(PropertiesKeys.ENTRY_RID)

        @classmethod
        def get_impacts(cls, transition: T):
            return transition.properties.get(PropertiesKeys.IMPACTS)

        @classmethod
        def get_probability(cls, transition: T):
            return transition.properties.get(PropertiesKeys.PROBABILITY)

        @classmethod
        def get_stop(cls, transition: T):
            return transition.properties.get(PropertiesKeys.STOP)


class TimeNetSematic(Generic[N]):

    def is_enabled(self, net: N, transition: T, marking: M):
        for arc in transition.in_arcs:
            p = arc.source
            d = NetUtils.Place.get_duration(p)
            token, age = marking[p]
            print(
                f"{p.name}[token={token},age={age}]\tcheck: {PetriNetSemantics.is_enabled(net, transition, marking.marking)}\t{age<d}"
            )
            if (
                not PetriNetSemantics.is_enabled(net, transition, marking.marking)
                or age < d
            ):
                return False

        return True

    def fire(self, net: N, transition: T, marking: M):
        new_age = marking.age
        for arc in transition.in_arcs:
            p = arc.source
            new_age[p] = 0

        c = PetriNetSemantics.fire(net, transition, marking.marking)
        m = Marking(c)

        return TimeMarking(m, new_age)

    def execute(self, net: N, transition: T, marking: M):
        if not self.is_enabled(net, transition, marking):
            return marking

        return self.fire(net, transition, marking)

    def enabled_transitions(self, net: N, marking: M):
        enabled = set()

        for t in net.transitions:
            if self.is_enabled(net, t, marking):
                enabled.add(t)

        return enabled


# class Builder:
#     def __init__(self):
#         self.net = PetriNet()
#         self.place_prop = {}
#         self.trans_prop = {}
#         self.d_match = {}

#     def set_name(self, name: str):
#         self.name = name

#     def add_place(self, place: PetriNet.Place, prop: RegionModel):
#         place.properties

# class DataSPIN:

#     places_prop: Dict[str, PlaceProp]
#     transitions_prop: Dict[str, TransitionProp]

#     @dataclass
#     class PlaceProp:
#         region_id: str
#         label: str
#         duration: float
#         distribution: List[Tuple[float, str]]

#     @dataclass
#     class TransitionProp:
#         region_id: str
#         label: str
#         impacts: List[float]

#     def __init__(
#         self,
#         net: PetriNet,
#         props: Dict[str, RegionProp],
#         distribution_match: Dict[str, List[Tuple[float, str]]],
#     ):
#         self.net = net
#         self.prop = props

#         self.places_prop = dict()
#         for place in net.places:
#             id = place.name
#             raw = props[id]
#             d_match = distribution_match[id] if id in distribution_match else []
#             self.places_prop.update(
#                 {
#                     id: DataSPIN.PlaceProp(
#                         raw.region_id, raw.label, raw.duration, d_match
#                     )
#                 }
#             )

#         self.transitions_prop = dict()
#         for trans in net.transitions:
#             id = trans.name
#             raw = props[id]
#             self.transitions_prop.update(
#                 {id: DataSPIN.TransitionProp(raw.region_id, raw.label, raw.impacts)}
#             )

#     def get_region_id(self, id):
#         return self.prop[id].region_id

#     def get_duration(self, id):
#         if not self.is_place(id):
#             None

#         return self.places_prop[id].duration

#     def is_transition(self, id):
#         return id in self.transitions_prop

#     def is_place(self, id):
#         return id in self.places_prop

#     def from_region(region: RegionModel):
#         pass

#     def get_props(
#         self, id: str
#     ) -> Type[DataSPIN.PlaceProp] | Type[DataSPIN.TransitionProp]:
#         if self.is_place(id):
#             return self.places_prop[id]


#         return self.transitions_prop[id]
class PropertiesKeys(Enum):
    ENTRY_RID = "entry_rid"  # Entry Region ID
    EXIT_RID = "exit_rid"  # Exit Region ID
    LABEL = "label"
    TYPE = "type"
    DURATION = "duration"
    IMPACTS = "impacts"
    PROBABILITY = "probability"
    STOP = "stop"
