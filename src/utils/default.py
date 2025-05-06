from pm4py import PetriNet

from model.region import RegionModel


class Defaults:

    @staticmethod
    def choice_child(region: RegionModel, _id: str):
        pass

    @staticmethod
    def nature_child(net: PetriNet, p_id: str):
        pass
