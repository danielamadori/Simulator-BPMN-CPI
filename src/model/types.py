from __future__ import annotations

from typing import TypeVar

from model.context import NetContext
from model.extree import ExecutionTree
from model.extree.node import Snapshot, ExecutionTreeNode
from model.petri_net.time_spin import TimeMarking, MarkingItem
from model.petri_net.time_spin import TimeNetSematic
from model.petri_net.wrapper import WrapperPetriNet
from model.region import RegionModel

# Context Types
ContextType = TypeVar('ContextType', bound=NetContext)

# Region Model Types
RegionModelType = TypeVar("RegionModelType", bound=RegionModel)

# Petri Net Types
PetriNetType = TypeVar("PetriNetType", bound=WrapperPetriNet)
TransitionType = TypeVar("TransitionType", bound=WrapperPetriNet.Transition)
PlaceType = TypeVar("PlaceType", bound=WrapperPetriNet.Place)
ArcType = TypeVar("ArcType", bound=WrapperPetriNet.Arc)
MarkingType = TypeVar("MarkingType", bound=TimeMarking)

SemanticType = TypeVar("SemanticType", bound=TimeNetSematic)

# Marking Item Type
MarkingItemType = TypeVar("MarkingItemType", bound=MarkingItem)

# Execution Tree Types
ExTreeType = TypeVar("ExTreeType", bound=ExecutionTree)
SnapshotType = TypeVar("SnapshotType", bound=Snapshot)
NodeType = TypeVar("NodeType", bound=ExecutionTreeNode)
