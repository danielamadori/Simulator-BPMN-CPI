from typing import TypeVar, TYPE_CHECKING

from model.petri_net.wrapper import WrapperPetriNet

if TYPE_CHECKING:
    pass

N = TypeVar("N", bound=WrapperPetriNet)
T = TypeVar("T", bound=WrapperPetriNet.Transition)
P = TypeVar("P", bound=WrapperPetriNet.Place)
M = TypeVar("M", bound="TimeMarking")