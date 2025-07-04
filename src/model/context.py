from pm4py.objects.petri_net.obj import PetriNet

from converter.spin import from_region
from model.region import RegionModel
from model.time_spin import TimeMarking, TimeNetSematic
from strategy.execution import ExecutionInterface, ClassicExecution


# id
class IDGenerator:
    counter = 0

    @classmethod
    def next_id(cls):
        cls.counter += 1
        return f"{cls.counter}"


class NetContext:
    _id: str
    region: RegionModel
    semantic: TimeNetSematic
    net: PetriNet
    initial_marking: TimeMarking
    final_marking: TimeMarking
    strategy: ExecutionInterface

    def __init__(self, region, net, im, fm, strategy=None, _id=None, semantic=None):
        self._id = _id or IDGenerator.next_id()
        self.semantic = semantic or TimeNetSematic()
        self.region = region
        self.net = net
        self.initial_marking = im
        self.final_marking = fm
        self.strategy = strategy or ClassicExecution()

    @classmethod
    def from_region(cls, region, strategy=ClassicExecution()):
        net, im, fm = from_region(region)

        return NetContext(region, net, im, fm, strategy)

    def __eq__(self, value):
        return isinstance(value, NetContext) and value._id == self._id
