from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from typing import Dict, List, Collection

from pm4py.objects.petri_net.semantics import ClassicSemantics

from model.time_spin import NetUtils, TimeMarking, TimeNetSematic
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
        self.raw_semantic = ClassicSemantics()

    def get_stoppable_active_transitions(self, net, marking):
        enabled_transitions = self.semantic.enabled_transitions(net, marking)
        print(f"ENABLED: {enabled_transitions}")
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
        if len(self.semantic.enabled_transitions(net, marking)) > 0:
            return marking, 0

        raw_semantic = self.raw_semantic
        _saturable_trans = raw_semantic.enabled_transitions(net, marking.marking)
        saturable_trans = [t for t in net.transitions if t in _saturable_trans]
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

    def consume(
        self,
        net: N,
        marking: M,
        fm: M,
        choices: Collection[T] | None = None,
    ):
        """
        Assumiamo che choices contenga l'insieme sincronizzato massimale di transizioni con stop per il marking
        """
        return self._consume(net, marking, choices)
        # default
        # probability = 1
        # _time = 0
        # for p in net.places:
        #     if NetUtils.Place.get_impacts(p):
        #         first_place = p
        #         break
        # impacts = [0] * len(NetUtils.Place.get_impacts(first_place))

        # # saturo
        # if marking != fm:
        #     tm, delta = self.saturate(net, marking)

        # # check final_marking (fine esecuzione della rete)
        # if marking.marking == fm.marking:
        #     return marking, 1, impacts, 0

        # active_stop_trans = self.get_stoppable_active_transitions(net, marking)

        # # caso base
        # if choices is None:
        #     choices = []

        # bho = True
        # for t in self.get_stoppable_active_transitions(net, marking):
        #     if t not in choices:
        #         bho = False

        # if len(active_stop_trans) != 0 and not bho:
        #     print("BASE CASE\n")
        #     return marking, probability, impacts, _time

        # # esecuzione
        # for t in self.semantic.enabled_transitions(net, tm):
        #     if NetUtils.Transition.get_stop(t) and t not in choices:
        #         continue
        #     tm = self.semantic.fire(net, t, marking)
        #     print(f"FIRE OF {t}\n")
        #     # Calcolo probabilità
        #     probability *= NetUtils.Transition.get_probability(t) or 1.0

        #     # Calcolo Impatti
        #     parent = list(t.in_arcs)[0].source
        #     parent_impacts = NetUtils.Place.get_impacts(parent) or []
        #     for i in range(len(parent_impacts)):
        #         impacts[i] += parent_impacts[i]
        #     _time += delta
        #     print("RECURSIVE CALL\n")

        # new_marking, p, new_impacts, new_time = self.consume(net, tm, fm, choices)

        # for i in range(len(new_impacts)):
        #     impacts[i] += new_impacts[i]

        # return new_marking, probability * p, impacts, _time + new_time

        # Default
        # tm = marking
        # probability = 1
        # _time = 0
        # first_place = None
        # for p in net.places:
        #     if NetUtils.Place.get_impacts(p):
        #         first_place = p
        #         break
        # impacts = [0] * len(NetUtils.Place.get_impacts(first_place))

        # saturazione
        # active_stop_trans = self.get_stoppable_active_transitions(net, tm)
        # coutn = 100
        # while active_stop_trans.intersection(choices) == choices and coutn > 0:
        #     coutn -= 1
        #     print("ENTRAAAA")
        #     # print(f"ITER: {active_stop_trans}")
        #     # print(f"CHOICES: {choices}")
        #     # print(f"INTERSECTION: {active_stop_trans.intersection(choices)}")
        #     # print(f" remake= {active_stop_trans}")
        #     tm, delta = self.saturate(net, tm)
        #     for t in self.semantic.enabled_transitions(net, tm):
        #         tm = self.semantic.fire(net, t, marking)
        #         # Calcolo probabilità
        #         probability *= NetUtils.Transition.get_probability(t) or 1
        #         # Calcolo Impatti
        #         parent = list(t.in_arcs)[0].source
        #         parent_impacts = NetUtils.Place.get_impacts(parent) or []
        #         for i in range(len(parent_impacts)):
        #             impacts[i] += parent_impacts[i]

        #     _time += delta
        #     active_stop_trans = self.get_stoppable_active_transitions(net, tm)

        # return tm, probability, impacts, _time

    def _consume(self, net, marking, choices):
        new_marking, delta = self.saturate(net, marking)
        probability = 1
        sem = self.semantic
        for p in net.places:
            if NetUtils.Place.get_impacts(p):
                first_place = p
                break
        impacts = [0] * len(NetUtils.Place.get_impacts(first_place))

        for t in sem.enabled_transitions(net, marking):
            if not NetUtils.Transition.get_stop(t) or t in choices:
                new_marking = sem.fire(net, t, new_marking)
                probability *= NetUtils.Transition.get_probability(t)

                parent = list(t.in_arcs)[0].source
                parent_impacts = NetUtils.Place.get_impacts(parent) or []
                for i in range(len(parent_impacts)):
                    impacts[i] += parent_impacts[i]

        if new_marking == marking:
            return new_marking, probability, impacts, delta
        else:
            new_marking, next_p, next_i, next_delta = self._consume(
                net, new_marking, choices
            )
            for i in range(len(next_i)):
                impacts[i] += next_i[i]

            return new_marking, next_p * probability, impacts, delta + next_delta
