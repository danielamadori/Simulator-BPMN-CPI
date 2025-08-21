from typing import TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from model.petri_net.wrapper import WrapperPetriNet
    from model.petri_net.time_spin import TimeMarking

N = TypeVar("N", bound="WrapperPetriNet")
T = TypeVar("T", bound="WrapperPetriNet.Transition")
P = TypeVar("P", bound="WrapperPetriNet.Place")
M = TypeVar("M", bound="TimeMarking")
