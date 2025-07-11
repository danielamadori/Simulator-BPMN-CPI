from typing import TypeVar, TYPE_CHECKING

from model.petri_net.wrapper import PetriNet

if TYPE_CHECKING:
    pass

N = TypeVar("N", bound=PetriNet)
T = TypeVar("T", bound=PetriNet.Transition)
P = TypeVar("P", bound=PetriNet.Place)
M = TypeVar("M", bound="TimeMarking")