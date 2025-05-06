from typing import Collection
import uuid
from model.extree import ExTree
from model.region import RegionModel
from model.snapshot import Snapshot
from model.time_spin import TimeMarking, TimeNetSematic
from model.types import T
from strategy.execution import ClassicExecution
from converter.spin import from_region
from pm4py.objects.petri_net.obj import PetriNet

from utils.net_utils import NetUtils


class NetContext:
    id: str
    semantic: TimeNetSematic
    net: PetriNet
    inital_marking: TimeMarking
    final_marking: TimeMarking
    strategy: ClassicExecution
    # init_tree: ExTree

    # def __init__(self, data: RegionModel):
    #     try:
    #         raw_petri_net, im, fm = from_region(data)
    #     except Exception as e:
    #         print(f"Errore: {e}")

    #     self.semantic = TimeNetSematic(raw_petri_net)
    #     self.net = raw_petri_net
    #     self.intial_marking = TimeMarking(im)
    #     self.final_marking = TimeMarking(fm)
    #     self.strategy = ClassicExecution(self.semantic)
    #     self.init_tree = ExTree(Snapshot(self.inital_marking, 1, None, 0))

    def __init__(self, region, net, im, fm, strategy, id=None):
        self.id = id or str(uuid.uuid4())
        self.region = region
        self.net = net
        self.im = im
        self.fm = fm
        self.strategy = strategy

    @classmethod
    def from_region(cls, region, strategy=ClassicExecution()):
        net, im, fm = from_region(region)

        return NetContext(region, net, im, fm, strategy)

    def generate_execution_tree(self):
        impacts = [0] * len(NetUtils.Place.get_impacts(list(self.im.keys())[0]))
        return ExTree(Snapshot(self.im, 1, impacts, 0))

    # set default
    def execute(self, tree: ExTree, choices: Collection[T] | None):
        """
        TODO:Scegliere i default ed eseguire la consume
        """
        new_marking, probability, impacts, delta = self.strategy.consume(
            self.net, tree.current_node.snapshot, self.final_marking, choices
        )
        return ExTree(Snapshot(new_marking, probability, impacts, delta))

    def get_choices(self, tree: ExTree):
        return self.strategy.get_choices(self.net, tree.current_node.snapshot)

    def __eq__(self, value):
        return isinstance(value, NetContext) and value.id == self.id
