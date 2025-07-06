import logging
from typing import Dict, Generic

from pm4py.objects.petri_net.obj import Marking, PetriNet
from pm4py.objects.petri_net.semantics import PetriNetSemantics

from utils.net_utils import NetUtils
from .types import N, T, M

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
    __age: dict[PetriNet.Place, float]
    __keys: set[PetriNet.Place]

    def __init__(self, marking: Marking, age: Dict[PetriNet.Place, float] = None):
        if age is None:
            age = {}

        self.__marking = marking.copy()
        self.__age = age.copy()
        self.__keys = set(marking.keys())

        # Verifica che le chiavi di `marking` siano un superset delle chiavi di `age`
        if not self.__keys.issuperset(age.keys()):
            logger.error(
                "le chiavi di `marking` non sono un superset delle chiavi di `age`"
            )
            raise ValueError(f"Invalid keys in 'age': {age.keys() - self.__keys}")

        # Aggiungi le chiavi di default a `_age` se non sono presenti
        for x in self.__keys:
            if x not in self.__age:
                self.__age[x] = 0

    @property
    def marking(self) -> Marking:
        return (
            self.__marking.copy()
        )  # Restituisce una copia per mantenere l'immutabilità

    @property
    def age(self) -> Dict[PetriNet.Place, float]:
        return self.__age.copy()  # Restituisce una copia per mantenere l'immutabilità

    def keys(self) -> set[PetriNet.Place]:
        return self.__keys.copy()

    def add_time(self, time):
        """
        Aggiunge un tempo specificato a tutte le età dei posti nel marking.
        Ritorna una nuova istanza di TimeMarkign con le età aggiornate.
        """
        new_age = {k: v + time for k, v in self.__age.items() if self.__marking[k] > 0}
        return TimeMarking(self.marking, new_age)

    def __getitem__(self, key: str):
        # Se `key` è una stringa, cerca la corrispondenza tra le chiavi(place)
        if isinstance(key, str):
            for place in self.__keys:
                if place.name == key:
                    key = place

        for place in self.__keys:
            if place.name == key.name:
                return self.marking[place], self.age[place]

        raise KeyError(f"Invalid key: '{key}' does not exists.")

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
        result = {k: self[k] for k in self.keys()}
        return repr(result)

    def __str__(self):
        return repr(self)

    def __copy__(self):
        return TimeMarking(self.marking.copy(), self.age.copy())


class TimeNetSematic(Generic[N]):

    def is_enabled(self, net: N, transition: T, marking: M):
        for arc in transition.in_arcs:
            p = arc.source
            d = NetUtils.Place.get_duration(p)
            token, age = marking[p]
            if token < arc.weight or age < d:
                return False

        return True

    def fire(self, net: N, transition: T, marking: M):
        logger.debug(f"Sparo la transazione{transition.label}")
        new_age = marking.age
        for arc in transition.in_arcs:
            p = arc.source
            new_age[p] = 0

        c = PetriNetSemantics.fire(net, transition, marking.marking)
        m = Marking(c)

        return TimeMarking(m, new_age)

    def execute(self, net: N, transition: T, marking: M):
        logger.debug(f"Eseguo la transazione{transition.label}")
        if not self.is_enabled(net, transition, marking):
            return marking

        return self.fire(net, transition, marking)

    def enabled_transitions(self, net: N, marking: M):
        enabled = set()

        for t in net.transitions:
            logger.debug(f"Transizione{t.label} è abitilata")
            if self.is_enabled(net, t, marking):
                enabled.add(t)

        return enabled

# class Builder:
#     def __init__(self):
#         self.net = PetriNet()
#         self.place_prop = {}
#         self.trans_prop = {}
#         self.d_match = {}

#     def set_name(self, name: str):
#         self.name = name

#     def add_place(self, place: PetriNet.Place, prop: RegionModel):
#         place.properties

# class DataSPIN:

#     places_prop: Dict[str, PlaceProp]
#     transitions_prop: Dict[str, TransitionProp]

#     @dataclass
#     class PlaceProp:
#         region_id: str
#         label: str
#         duration: float
#         distribution: List[Tuple[float, str]]

#     @dataclass
#     class TransitionProp:
#         region_id: str
#         label: str
#         impacts: List[float]

#     def __init__(
#         self,
#         net: PetriNet,
#         props: Dict[str, RegionProp],
#         distribution_match: Dict[str, List[Tuple[float, str]]],
#     ):
#         self.net = net
#         self.prop = props

#         self.places_prop = dict()
#         for place in net.places:
#             id = place.name
#             raw = props[id]
#             d_match = distribution_match[id] if id in distribution_match else []
#             self.places_prop.update(
#                 {
#                     id: DataSPIN.PlaceProp(
#                         raw.region_id, raw.label, raw.duration, d_match
#                     )
#                 }
#             )

#         self.transitions_prop = dict()
#         for trans in net.transitions:
#             id = trans.name
#             raw = props[id]
#             self.transitions_prop.update(
#                 {id: DataSPIN.TransitionProp(raw.region_id, raw.label, raw.impacts)}
#             )

#     def get_region_id(self, id):
#         return self.prop[id].region_id

#     def get_duration(self, id):
#         if not self.is_place(id):
#             None

#         return self.places_prop[id].duration

#     def is_transition(self, id):
#         return id in self.transitions_prop

#     def is_place(self, id):
#         return id in self.places_prop

#     def from_region(region: RegionModel):
#         pass

#     def get_props(
#         self, id: str
#     ) -> Type[DataSPIN.PlaceProp] | Type[DataSPIN.TransitionProp]:
#         if self.is_place(id):
#             return self.places_prop[id]


#         return self.transitions_prop[id]
