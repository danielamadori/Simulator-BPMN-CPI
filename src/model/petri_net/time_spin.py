from __future__ import annotations

import copy
import logging
from collections import namedtuple
from typing import TYPE_CHECKING

from pm4py.objects.petri_net.obj import Marking, PetriNet
from pm4py.objects.petri_net.semantics import PetriNetSemantics

from model.petri_net.wrapper import WrapperPetriNet
from model.region import RegionType

if TYPE_CHECKING:
    from model.types import PlaceType, MarkingType, PetriNetType, TransitionType

logger = logging.getLogger(__name__)

MarkingItem = namedtuple("MarkingItem", ['token', 'age', 'visit_count'])


class TimeMarking:
    __keys: set[PlaceType]
    __tokens: Marking
    __age: dict[PlaceType, float]
    __visit_count: dict[PlaceType, int]

    def __init__(self, marking: Marking, age: dict[PlaceType, float] | None = None,
                 visit_count: dict[PlaceType, int] | None = None):
        super().__init__()
        if age is None:
            age = {}
        if visit_count is None:
            visit_count = {}

        # Set data
        self.__tokens = Marking()
        self.__age = dict()
        self.__visit_count = dict()

        # Populate data
        for key in marking:
            if marking[key] > 0:
                self.__tokens[key] = marking[key]

        for place in age:
            self.__age[place] = age[place]

        for place in visit_count:
            self.__visit_count[place] = visit_count[place]

    def __getitem__(self, key: str | PlaceType) -> MarkingItem:
        # Se `key` è una stringa, cerca la corrispondenza tra le chiavi(place) usando l'id
        if isinstance(key, str):
            for place in self.keys():
                if place.name == key:
                    key = place

        if isinstance(key, PetriNet.Place) and not isinstance(key, WrapperPetriNet.Place):
            raise TypeError("Key must be a WrapperPetriNet.Place or a string representing the place name.")

        token = self.__tokens.get(key, 0)
        age = self.__age.get(key, 0.0)
        visit_count = self.__visit_count.get(key, 0)
        return MarkingItem(token=token, age=age, visit_count=visit_count)

    def __eq__(self, other):
        if not isinstance(other, TimeMarking):
            return False

        for key in self.keys() | other.keys():
            if self[key] != other[key]:
                return False

        return True

    def __repr__(self):
        result = {key: self[key] for key in self.keys()}
        return repr(result)

    def __str__(self):
        return repr(self)

    def __copy__(self):
        return TimeMarking(self.__tokens, self.__age, self.__visit_count)

    def __deepcopy__(self, memodict=None):
        return TimeMarking(self.tokens, self.age, self.visit_count)

    def __iter__(self):
        return iter(self.keys())

    @property
    def tokens(self) -> Marking:
        m = Marking()

        for key in self.__tokens:
            m[key] = self[key].token

        return m  # Restituisce una copia per mantenere l'immutabilità

    @property
    def age(self) -> dict[PlaceType, float]:
        return copy.copy(self.__age)  # Restituisce una copia per mantenere l'immutabilità

    @property
    def visit_count(self) -> dict[PlaceType, int]:
        return copy.copy(self.__visit_count)

    def keys(self) -> set[PlaceType]:
        return self.__tokens.keys() | self.__age.keys() | self.__visit_count.keys()

    def add_time(self, time: float):
        """
        Aggiunge un tempo specificato a tutte le età dei posti nel marking.
        Ritorna una nuova istanza di TimeMarkign con le età aggiornate.
        """
        new_age = self.age
        for key in self.__tokens:
            token, age, _ = self[key]
            if token > 0:
                new_age[key] = age + time

        return TimeMarking(self.tokens, age=new_age, visit_count=self.visit_count)

    def increase_visit_count(self, places: PlaceType | list[PlaceType]):
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

        return TimeMarking(marking=self.tokens, age=self.age, visit_count=new_visit_count)


class TimeNetSematic:

    def is_enabled(self, net: PetriNetType, transition: TransitionType, marking: MarkingType) -> bool:
        for arc in transition.in_arcs:
            input_place: WrapperPetriNet.Place = arc.source
            duration = input_place.duration
            token, age, _ = marking[input_place]
            if token < arc.weight or age < duration:
                return False
            if (transition.stop
                    and input_place.visit_limit is not None
                    and input_place.visit_limit <= marking[input_place].visit_count
                    and transition.region_type == RegionType.LOOP
                    and transition.label.startswith("Loop")):
                return False

        return True

    def fire(self, net: PetriNetType, transition: TransitionType, marking: MarkingType) -> MarkingType:
        logger.debug(f"Sparo la transazione{transition.label}")
        new_age = marking.age
        new_visit_count = marking.visit_count
        for arc in transition.in_arcs:
            input_place = arc.source
            new_age[input_place] = 0
            new_visit_count[input_place] = new_visit_count.get(input_place, 0) + 1

        tokens = PetriNetSemantics.fire(net, transition, marking.tokens)
        new_marking = Marking(tokens)

        return TimeMarking(new_marking, new_age, new_visit_count)

    def execute(self, net: PetriNetType, transition: TransitionType, marking: MarkingType) -> MarkingType:
        logger.debug(f"Eseguo la transazione{transition.label}")
        if not self.is_enabled(net, transition, marking):
            return marking

        return self.fire(net, transition, marking)

    def enabled_transitions(self, net: PetriNetType, marking: MarkingType) -> set[TransitionType]:
        enabled = set()

        for t in net.transitions:
            logger.debug(f"Transizione{t.label} è abitilata")
            if self.is_enabled(net, t, marking):
                enabled.add(t)

        return enabled
