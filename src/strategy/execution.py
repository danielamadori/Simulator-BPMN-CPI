from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from typing import Dict, List, TypeVar, Collection

from pm4py.objects.petri_net.obj import PetriNet
from pm4py.objects.petri_net.semantics import ClassicSemantics

from model.time_spin import NetUtils, TimeMarking, TimeNetSematic
from utils.net_utils import PropertiesKeys
from model.types import N, T, P, M


class ExecutionInterface(ABC):

    @abstractmethod
    def consume(self, net: N, marking: M, choices: Collection[T] | None = None):
        pass

    @abstractmethod
    def get_choices(self, net: N, marking: M):
        pass

    @abstractmethod
    def saturate(self, net: N, marking: M):
        pass


class ClassicExecution(ExecutionInterface):

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

    def consume(self, net: N, marking: M, fm: M, choices: Collection[T] | None = None):
        """
        Assumiamo che choices contenga l'insieme sincronizzato massimale di transizioni con stop per il marking
        """
        # check final_marking (fine esecuzione della rete)
        if marking.marking == fm.marking:
            return marking, 1, 0, 0

        # Default
        tm = marking
        probability = 1
        _time = 0
        trans_iter = iter(net.places)
        first_place = next(trans_iter)
        impacts = [0] * len(NetUtils.Place.get_impacts(first_place))

        # saturazione
        active_stop_trans = self.get_stoppable_active_transitions()
        while active_stop_trans.intersection(choices) == active_stop_trans:
            tm, delta = self.saturate(net, tm)
            for t in self.semantic.enabled_transitions(net, tm):
                tm = self.semantic.fire(net, t, marking)
                # Calcolo probabilità
                probability *= NetUtils.Transition.get_probability(t) or 1
                # Calcolo Impatti
                parent = list(t.in_arcs)[0].source
                parent_impacts = NetUtils.Place.get_impacts(parent) or []
                for i in len(parent_impacts):
                    impacts[i] += parent_impacts[i]

            _time += delta

        return tm, probability, impacts, _time
