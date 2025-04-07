from converter.spin import Prop
from pm4py.objects.petri_net.obj import PetriNet
from typing import Dict, List, Tuple, Type    
from __future__ import annotations

from model.region import RegionModel
from dataclasses import dataclass

class DataSPIN:

    @dataclass
    class PlaceProp:
        region_id: str
        label: str
        duration: float
        age: float
        distribution: List[Tuple[float, str]]

    @dataclass
    class TransitionProp:
        region_id: str
        label: str
        impacts: List[float]

    def __init__(self, net: PetriNet, props: Dict[str,Prop], distribution_match: Dict[str,List[Tuple[float,str]]]):
        self.net = net
        self.prop = props

        self.places = dict()
        for place in net.places:
            id = place.name
            raw = props[id]
            d_match = distribution_match[id]
            self.places[id] = DataSPIN.PlaceProp(raw.region_id, raw.label, raw.duration, 0, d_match)

        self.transitions = dict()
        for trans in net.transitions:
            id = trans.name
            raw = props[id]
            self.transitions[id] = DataSPIN.TransitionProp(raw.region_id, raw.label, raw.impacts)

    def get_region_id(self, id):
        return self.prop[id].region_id
    
    def is_transition(self, id):
        return id in self.transitions
    
    def is_place(self, id):
        return id in self.places
    
    def from_region(region: RegionModel):
        pass

    def get_props(self, id: str) -> Type[DataSPIN.PlaceProp] | Type[DataSPIN.TransitionProp]:
        if self.is_place(id):
            return self.places[id]
        
        return self.transitions[id]