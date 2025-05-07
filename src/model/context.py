from typing import Collection, Dict, List
import uuid
from model.extree import ExTree
from model.region import RegionModel
from model.snapshot import Snapshot
from model.time_spin import TimeMarking, TimeNetSematic
from model.types import T, P
from strategy.execution import ClassicExecution
from converter.spin import from_region
from pm4py.objects.petri_net.obj import PetriNet

from utils.default import Defaults
from utils.net_utils import NetUtils


class NetContext:
    _id: str
    semantic: TimeNetSematic
    net: PetriNet
    initial_marking: TimeMarking
    final_marking: TimeMarking
    strategy: ClassicExecution

    def __init__(self, region, net, im, fm, strategy, id=None):
        self._id = id or str(uuid.uuid4())
        self.region = region
        self.net = net
        self.im = im
        self.fm = fm
        self.strategy = strategy

    @classmethod
    def from_region(cls, region, strategy=ClassicExecution()):
        net, im, fm = from_region(region)

        return NetContext(region, net, im, fm, strategy)

    def __eq__(self, value):
        return isinstance(value, NetContext) and value._id == self._id
