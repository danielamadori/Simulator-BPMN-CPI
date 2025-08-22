from __future__ import annotations

from collections import namedtuple
from typing import TypeVar

# from model.petri_net.wrapper import WrapperPetriNet
# from model.petri_net.time_spin import TimeMarking

# Petri Net Types
N = TypeVar("N", bound="WrapperPetriNet")
T = TypeVar("T", bound="WrapperPetriNet.Transition")
P = TypeVar("P", bound="WrapperPetriNet.Place")
M = TypeVar("M", bound="TimeMarking")

# Marking Item Type
MarkingItem = namedtuple("MarkingItem", ['token','age','visit_count'])