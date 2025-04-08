from typing import Dict
from pm4py.objects.petri_net.importer.variants.pnml import import_net_from_string
from pm4py.objects.petri_net.data_petri_nets.semantics import DataPetriNetSemantics
from converter.spin import Prop, getProps, create_pnml_from_region
from model.region import RegionModel

class Controller:
    
    def __init__(self, region:RegionModel):
        # WARNING: il dizionario ottenuto con getProps() va chiamato dopo la costruzione della rete (non modificare l'oridine di chiamate a funzioni)
        #rete di pm4py (base di lavoro)
        self.net,self.marking,self.finalMarking = import_net_from_string(create_pnml_from_region(region,None))
        #dizionario di proprietà della rete
        self.properties:Dict[str, Prop] = getProps()

    def enabled_transitions(self):
        return DataPetriNetSemantics.enabled_transitions(self.net,self.marking)

    def execute(self):
        #set di transizioni da controllare
        enabled_transitions = enabled_transitions(self)

        DataPetriNetSemantics.execute(...)
