from typing import TypeVar, TYPE_CHECKING

from pm4py import PetriNet

if TYPE_CHECKING:
    from src.model.time_spin import TimeMarking

N = TypeVar("N", bound=PetriNet)
T = TypeVar("T", bound=PetriNet.Transition)
P = TypeVar("P", bound=PetriNet.Place)
M = TypeVar("M", bound="TimeMarking")