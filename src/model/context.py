from __future__ import annotations

from typing import TYPE_CHECKING

from converter.spin import from_region
from model.petri_net.time_spin import TimeNetSematic
from strategy import default_strategy

if TYPE_CHECKING:
    from strategy.base import StrategyProto
    from model.types import RegionModelType, SemanticType, PetriNetType, MarkingType


# id
class IDGenerator:
    counter = 0

    @classmethod
    def next_id(cls):
        cls.counter += 1
        return f"{cls.counter}"


class NetContext:
    """
    Used to encapsulate BPMN+CPI region, Petri net, initial marking, final marking, and execution strategy.

    Attributes:
        _id (str): Unique identifier for the net context.
        region (RegionModelType): The BPMN+CPI region model.
        semantic (SemanticType): The semantics associated with the Petri net.
        net (PetriNetType): The Petri net model.
        initial_marking (MarkingType): The initial marking of the Petri net.
        final_marking (MarkingType): The final marking of the Petri net.
        strategy (object): The execution strategy for the Petri net.
    """

    _id: str
    region: RegionModelType
    semantic: SemanticType
    net: PetriNetType
    initial_marking: MarkingType
    final_marking: MarkingType
    strategy: StrategyProto

    def __init__(self, region: RegionModelType, net: PetriNetType, im: MarkingType, fm: MarkingType,
                 strategy: object = None, _id: str = None, semantic: SemanticType = None):
        self._id = _id or IDGenerator.next_id()
        self.semantic = semantic or TimeNetSematic()
        self.region = region
        self.net = net
        self.initial_marking = im
        self.final_marking = fm
        self.strategy = strategy or default_strategy

    @classmethod
    def from_region(cls, region: RegionModelType, strategy: object = None):
        net, im, fm = from_region(region)

        return NetContext(region, net, im, fm, strategy)

    def __eq__(self, other):
        return isinstance(other, NetContext) and other._id == self._id
