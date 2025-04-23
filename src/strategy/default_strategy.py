from abc import ABC, abstractmethod
from typing import Dict, List, TypeVar

from pm4py.objects.petri_net.obj import PetriNet
from pm4py.objects.petri_net.semantics import ClassicSemantics

from model.time_spin import NetUtils, TimeMarking, TimeNetSematic

N = TypeVar("N", bound=PetriNet)
T = TypeVar("T", bound=PetriNet.Transition)
P = TypeVar("P", bound=PetriNet.Place)
M = TypeVar("M", bound=TimeMarking)


class StrategyInterface(ABC):

    @abstractmethod
    def consume(self, net: N, marking: M, choices: List[T] | None = None):
        pass

    @abstractmethod
    def get_choices(self, net: N, marking: M):
        pass

    @abstractmethod
    def saturate(self, net: N, marking: M, choices: List[T]):
        pass


class ClassicStrategy(StrategyInterface):

    def __init__(self, semantic=None):
        self.semantic = semantic if semantic else TimeNetSematic()

    def get_stoppable_active_transitions(self, net, marking):
        enabled_transitions = self.semantic.enabled_transitions(net, marking)
        # Filtro per transizoni con stop attivo
        enabled_transitions = filter(
            lambda x: NetUtils.Transition.get_stop(x), enabled_transitions
        )

        return set(enabled_transitions)

    def get_choices(self, net: N, marking: M) -> Dict[P, List[T]]:
        enabled_transitions = self.get_stoppable_active_transitions(net, marking)

        groups = {}
        for t in enabled_transitions:
            parent = list(t.in_arcs)[0].source
            if groups.get(parent) is None:
                groups.update({parent: []})

            groups[parent].append(t)

        return groups

    def saturate(self, net, marking):
        if self.semantic.enabled_transitions():
            return marking

        raw_semantic = ClassicSemantics()
        saturable_trans = raw_semantic.enabled_transitions(net, marking)

        k = {}
        for t in saturable_trans:
            _max = 0
            for arc in t.in_arcs:
                parent_place = arc.source
                curr_delta = (
                    NetUtils.Place.get_duration(parent_place)
                    - marking.age[parent_place]
                )
                _max = max(curr_delta, _max)

            k.update({t: _max})

        min_delta = min(k.values())

        new_age = {}
        for p in marking.marking:
            token, age = marking[p]
            if token == 0:
                continue
            new_age[p] = age + min_delta

        return TimeMarking(marking.marking, new_age)

    def consume(self, net, marking, choices):
        """
        Assumiamo che choices contenga l'insieme sincronizzato massimale di transizioni per il marking
        """
        saturated_marking = self.saturate(net, marking)

        raw_semantic = ClassicSemantics()
        all_active_transition = raw_semantic.enabled_transitions()
        active_and_stoppable_transition = self.get_stoppable_active_transitions(
            net, saturated_marking
        )
        # Aggiunto tutte le transizioni eseguibili senza stop
        for el in all_active_transition - active_and_stoppable_transition:
            choices.append(el)

        # Set default per scelte non specificate
        for at in active_and_stoppable_transition:
            if not at in choices:
                pass
