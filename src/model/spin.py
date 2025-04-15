# from __future__ import annotations

# from dataclasses import dataclass
# from typing import Dict, List, Tuple, Type

# from pm4py.objects.petri_net.obj import PetriNet, Marking
# from pm4py.objects.petri_net.utils.petri_utils import add_place, add_arc_from_to, add_transition

# from converter.spin import RegionProp
# from model.region import RegionModel


# class DataMarking:

#     def __init__(self, marking: Marking, age: Dict[str, float]):
#         self.marking = marking
#         self.age = age

#     def __get_marking(self):
#         return self.marking.copy()

#     def __get_age(self):
#         return self.age.copy()

#     def get_place_state(self, p_id: str) -> Tuple[int, int]:
#         return (self.marking[p_id], self.age[p_id])

#     marking: Marking = property(fget=__get_marking, fset=None, fdel=None)
#     age: Dict[str, float] = property(fget=__get_age, fset=None, fdel=None)


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
