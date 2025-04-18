from typing import override

from pm4py.objects.petri_net.obj import PetriNet
from pm4py.objects.petri_net.semantics import PetriNetSemantics

from model.time_spin import TimeMarking, DataSPIN


class NetSemantic:

    # def __init__(self, region: RegionModel):
    # WARNING: il dizionario ottenuto con getProps() va chiamato dopo la costruzione della rete (non modificare l'oridine di chiamate a funzioni)
    # rete di pm4py (base di lavoro)
    # self.net, self.marking, self.finalMarking = import_net_from_string(
    #     create_pnml_from_region(region, None)
    # )
    # # dizionario di proprietà della rete
    # self.properties: Dict[str, Prop] = getProps()
    @override
    def is_enabled(self, pn: DataSPIN, t: PetriNet.Transition, marking: TimeMarking):
        for arc in t.in_arcs:
            p = arc.source
            p_id = p.name
            d = pn.get_duration(p_id)
            token, age = marking.get_place_state(p_id)
            if token <= 0 or (token > 0 and age < d):
                return False

        return True

    @override
    def fire(self, net: DataSPIN, t: PetriNet.Transition, marking: TimeMarking):
        new_age = marking.age
        for arc in t.in_arcs:
            p = arc.source
            new_age[p.name] = 0

        m = PetriNetSemantics.fire(net, t, marking.marking)

        return TimeMarking(m, new_age)

    @override
    def execute(self, net: DataSPIN, t: PetriNet.Transition, marking: TimeMarking):
        if not self.is_enabled(t):
            return marking

        return self.fire(net, t, marking)

    @override
    def enabled_transitions(self, net: DataSPIN, marking: TimeMarking):
        enabled = set()
        for t in net.net.transitions:
            if self.is_enabled(net, t, marking):
                enabled.add(t)

        return enabled
