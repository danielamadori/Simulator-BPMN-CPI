from typing import Collection
from model.region import RegionModel
from model.snapshot import Snapshot
from model.time_spin import TimeMarking, TimeNetSematic
from strategy.execution import ClassicExecution
from converter.spin import from_region
from pm4py.objects.petri_net.obj import PetriNet, Marking


class Context:
    semantic: TimeNetSematic
    net: PetriNet
    inital_marking: TimeMarking
    final_marking: TimeMarking
    strategy: ClassicExecution

    def __init__(self, data: RegionModel):
        try:
            raw_petri_net, im, fm = from_region(data)
        except Exception as e:
            print(f"Errore: {e}")

        self.semantic = TimeNetSematic(raw_petri_net)
        self.net = raw_petri_net
        self.intial_marking = TimeMarking(im)
        self.final_marking = TimeMarking(fm)
        self.strategy = ClassicExecution(self.semantic)

    def execute(self, curr_marking: TimeMarking, choices: Collection[T] | None):
        new_marking, probability, impacts, delta = self.strategy.consume(
            self.net, curr_marking, self.final_marking, choices
        )
        return Snapshot(new_marking, probability, impacts, delta)

    def get_choices(self, marking: TimeMarking):
        return self.strategy.get_choices(self.net, marking)
