from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from typing import Dict, List, TypeVar, Collection

from pm4py.objects.petri_net.obj import PetriNet
from pm4py.objects.petri_net.semantics import ClassicSemantics

from model.time_spin import NetUtils, TimeMarking, TimeNetSematic
from utils.net_utils import PropertiesKeys

N = TypeVar("N", bound=PetriNet)
T = TypeVar("T", bound=PetriNet.Transition)
P = TypeVar("P", bound=PetriNet.Place)
M = TypeVar("M", bound=TimeMarking)


class StrategyInterface(ABC):

    @abstractmethod
    def consume(self, net: N, marking: M, choices: Collection[T] | None = None):
        pass

    @abstractmethod
    def get_choices(self, net: N, marking: M):
        pass

    @abstractmethod
    def saturate(self, net: N, marking: M):
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
        if self.semantic.enabled_transitions(net, marking):
            return marking, 0

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

        return TimeMarking(marking.marking, new_age), min_delta

    def consume(self, net: N, marking: M, choices: Collection[T] | None = None):
        """
        Assumiamo che choices contenga l'insieme sincronizzato massimale di transizioni per il marking
        """
        saturated_marking, time_passed = self.saturate(net, marking)

        raw_semantic = ClassicSemantics()
        all_active_transition = raw_semantic.enabled_transitions(net, saturated_marking)
        active_and_stoppable_transition = self.get_stoppable_active_transitions(
            net, saturated_marking
        )

        all_choices = set(copy.deepcopy(choices))
        # Aggiunto tutte le transizioni eseguibili senza stop
        for el in all_active_transition - active_and_stoppable_transition:
            all_choices.add(el)

        _m = copy.deepcopy(saturated_marking)
        len_impacts = len(NetUtils.Place.get_impacts(list(_m.keys())[0]))

        total_impacts = [0] * len_impacts
        for c in all_choices:
            _m = self.semantic.fire(net, c, _m)
            curr_impact = NetUtils.Place.get_impacts(list(c.in_arcs)[0].source)
            if curr_impact is None:
                continue
            for i in range(len_impacts):
                total_impacts[i] += curr_impact[i]


