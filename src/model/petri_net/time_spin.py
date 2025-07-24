import copy
import logging
from collections import defaultdict
from typing import Dict

from pm4py.objects.petri_net.obj import Marking
from pm4py.objects.petri_net.semantics import PetriNetSemantics

from model.petri_net.wrapper import WrapperPetriNet
from model.region import RegionType
from utils.net_utils import NetUtils

logger = logging.getLogger(__name__)


def get_place_by_name(net, place_name):
    """
    Trova un posto nel Petri net per nome.
    """
    for place in net.places:
        if place.name == place_name:
            return place
    return None


class TimeMarking:
    __marking: Marking
    __keys: set[WrapperPetriNet.Place]

    def __init__(self, marking: Marking, age: Dict[WrapperPetriNet.Place, float] | None = None,
                 visit_count: dict[WrapperPetriNet.Place, int] | None = None):

        if age is None:
            age = {}
        if visit_count is None:
            visit_count = {}

        # Set marking
        self.__marking = copy.copy(marking)
        self.__keys = set(marking.keys())

        # Set data
        self.__age = defaultdict(float)
        self.__visit_count = defaultdict(int)
        for place in self.__keys:
            if place in age or place.name in age:
                self.__age[place] = age[place]

            if place in visit_count or place.name in visit_count:
                self.__visit_count[place] = visit_count[place]

    @property
    def tokens(self) -> Marking:
        return copy.copy(self.__marking)  # Restituisce una copia per mantenere l'immutabilità

    @property
    def age(self) -> Dict[WrapperPetriNet.Place, float]:
        return copy.copy(self.__age)  # Restituisce una copia per mantenere l'immutabilità

    @property
    def visit_count(self) -> Dict[WrapperPetriNet.Place, int]:
        return copy.copy(self.__visit_count)

    def keys(self) -> set[WrapperPetriNet.Place]:
        return copy.copy(self.__keys)

    def add_time(self, time):
        """
        Aggiunge un tempo specificato a tutte le età dei posti nel marking.
        Ritorna una nuova istanza di TimeMarkign con le età aggiornate.
        """
        new_age = {}
        for key in self.__keys:
            token, age = self[key]["token"], self[key]["age"]
            if token > 0:
                new_age[key] = age + time

        copy_visit_count = copy.copy(self.__visit_count)
        return TimeMarking(self.tokens, age=new_age, visit_count=copy_visit_count)

    def increase_visit_count(self, places: WrapperPetriNet.Place | list[WrapperPetriNet.Place]):
        """
        Incrementa il contatore di visita per i posti specificati.
        Ritorna una nuova istanza di TimeMarking con i contatori aggiornati.
        """
        if isinstance(places, WrapperPetriNet.Place):
            places = [places]

        new_visit_count = copy.copy(self.__visit_count)
        for place in places:
            if place not in self:
                continue
            if place in new_visit_count:
                new_visit_count[place] += 1
            else:
                new_visit_count[place] = 1

        return TimeMarking(self.tokens, age=self.age, visit_count=new_visit_count)

    def __getitem__(self, key: str | WrapperPetriNet.Place):
        # Se `key` è una stringa, cerca la corrispondenza tra le chiavi(place)
        if isinstance(key, str):
            for place in self.__keys:
                if place.name == key:
                    key = place

        for place in self.__keys:
            if place.name == key.name:
                return {
                    "token": self.__marking[place],
                    "age": self.__age.get(place, 0),
                    "visit_count": self.__visit_count.get(place, 0)
                }

        return {
            "token": 0,
            "age": 0,
            "visit_count": 0
        }

    def __contains__(self, el):
        # Se `el` è una stringa, cerca la corrispondenza tra le chiavi(place)
        if isinstance(el, str):
            for place in self.__keys:
                if place.name == el:
                    el = place

        return el in self.__keys

    def __eq__(self, other):
        if not isinstance(other, TimeMarking):
            return False

        if self.keys() != other.keys():
            return False

        for key in self.__keys:
            if self[key] != other[key]:
                return False

        return True

    def __repr__(self):
        result = {key: self[key] for key in self.keys()}
        return repr(result)

    def __str__(self):
        return repr(self)

    def __copy__(self):
        return TimeMarking(copy.copy(self.tokens), copy.copy(self.age), copy.copy(self.__visit_count))

    def __deepcopy__(self, memo):
        return self.__copy__()


class TimeNetSematic:

    def is_enabled(self, net: WrapperPetriNet, transition: WrapperPetriNet.Transition, marking: TimeMarking) -> bool:
        for arc in transition.in_arcs:
            input_place = arc.source
            duration = NetUtils.Place.get_duration(input_place)
            token, age = marking[input_place]["token"], marking[input_place]["age"]
            if token < arc.weight or age < duration:
                return False
            if (NetUtils.Transition.get_stop(transition)
                    and NetUtils.Place.get_visit_limit(input_place) is not None
                    and NetUtils.Place.get_visit_limit(input_place) <= marking[input_place]["visit_count"]
                    and NetUtils.get_type(transition) == RegionType.LOOP
                    and transition.label.startswith("Loop")):
                return False

        return True

    def fire(self, net: WrapperPetriNet, transition: WrapperPetriNet.Transition, marking: TimeMarking) -> TimeMarking:
        logger.debug(f"Sparo la transazione{transition.label}")
        new_age = marking.age
        new_visit_count = marking.visit_count
        for arc in transition.in_arcs:
            input_place = arc.source
            new_age[input_place] = 0
            new_visit_count[input_place] += 1

        tokens = PetriNetSemantics.fire(net, transition, marking.tokens)
        new_marking = Marking(tokens)

        return TimeMarking(new_marking, new_age, new_visit_count)

    def execute(self, net: WrapperPetriNet, transition: WrapperPetriNet.Transition,
                marking: TimeMarking) -> TimeMarking:
        logger.debug(f"Eseguo la transazione{transition.label}")
        if not self.is_enabled(net, transition, marking):
            return marking

        return self.fire(net, transition, marking)

    def enabled_transitions(self, net: WrapperPetriNet, marking: TimeMarking) -> set[WrapperPetriNet.Transition]:
        enabled = set()

        for t in net.transitions:
            logger.debug(f"Transizione{t.label} è abitilata")
            if self.is_enabled(net, t, marking):
                enabled.add(t)

        return enabled
