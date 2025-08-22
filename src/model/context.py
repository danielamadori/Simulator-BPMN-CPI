from __future__ import annotations

from typing import TYPE_CHECKING

from converter.spin import from_region
from model.petri_net.time_spin import TimeNetSematic
from strategy.execution import ClassicExecution

if TYPE_CHECKING:
    from model.types import RegionModelType, SemanticType, PetriNetType, MarkingType


# id
class IDGenerator:
    counter = 0

    @classmethod
    def next_id(cls):
        cls.counter += 1
        return f"{cls.counter}"


class NetContext:
    _id: str
    region: RegionModelType
    semantic: SemanticType
    net: PetriNetType
    initial_marking: MarkingType
    final_marking: MarkingType
    strategy: object

    def __init__(self, region: RegionModelType, net: PetriNetType, im: MarkingType, fm: MarkingType,
                 strategy: object = None, _id: str = None, semantic: SemanticType = None):
        self._id = _id or IDGenerator.next_id()
        self.semantic = semantic or TimeNetSematic()
        self.region = region
        self.net = net
        self.initial_marking = im
        self.final_marking = fm
        self.strategy = strategy or ClassicExecution()

    @classmethod
    def from_region(cls, region: RegionModelType, strategy: object = None):
        net, im, fm = from_region(region)

        return NetContext(region, net, im, fm, strategy)

    def __eq__(self, other):
        return isinstance(other, NetContext) and other._id == self._id
