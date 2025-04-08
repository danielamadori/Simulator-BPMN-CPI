from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Type

from pm4py.objects.petri_net.obj import PetriNet

from converter.spin import Prop
from model.region import RegionModel


class DataSPIN:

    places_prop: List[PlaceProp]
    transitions_prop: List[TransitionProp]

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

    def __init__(
        self,
        net: PetriNet,
        props: Dict[str, Prop],
        distribution_match: Dict[str, List[Tuple[float, str]]],
    ):
        self.net = net
        self.prop = props

        self.places_prop = dict()
        for place in net.places:
            id = place.name
            raw = props[id]
            d_match = distribution_match[id] if id in distribution_match else []
            self.places_prop.update(
                {
                    id: DataSPIN.PlaceProp(
                        raw.region_id, raw.label, raw.duration, 0, d_match
                    )
                }
            )

        self.transitions_prop = dict()
        for trans in net.transitions:
            id = trans.name
            raw = props[id]
            self.transitions_prop.update(
                {id: DataSPIN.TransitionProp(raw.region_id, raw.label, raw.impacts)}
            )

    def get_region_id(self, id):
        return self.prop[id].region_id

    def is_transition(self, id):
        return id in self.transitions_prop

    def is_place(self, id):
        return id in self.places_prop

    def from_region(region: RegionModel):
        pass

    def get_props(
        self, id: str
    ) -> Type[DataSPIN.PlaceProp] | Type[DataSPIN.TransitionProp]:
        if self.is_place(id):
            return self.places_prop[id]

        return self.transitions_prop[id]
