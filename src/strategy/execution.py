from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Collection, Set

from pm4py.objects.petri_net.semantics import ClassicSemantics

from model.extree import ExTree
from model.snapshot import Snapshot
from model.time_spin import NetUtils, TimeMarking, TimeNetSematic
from model.types import N, T, P, M
from strategy.context import NetContext
from utils.default import Defaults


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

    def get_stoppable_active_transitions(self, net, marking) -> Set[T]:
        enabled_transitions = self.semantic.enabled_transitions(net, marking)
        print(f"ENABLED: {enabled_transitions}")
        # Filtro per transizoni con stop attivo
        enabled_transitions = filter(
            lambda x: NetUtils.Transition.get_stop(x), enabled_transitions
        )

        return set(enabled_transitions)

    def get_choices(self, ctx: NetContext, tree: ExTree):
        return self.__get_choices(ctx.net, tree.current_node.snapshot.marking)

    def __get_choices(self, net: N, marking: M) -> Dict[P, List[T]]:
        enabled_transitions = self.get_stoppable_active_transitions(net, marking)

        groups = {}
        for t in enabled_transitions:
            parent = list(t.in_arcs)[0].source
            if groups.get(parent) is None:
                groups.update({parent: []})

            groups[parent].append(t)

        return groups

    def saturate(self, net, marking) -> tuple[M, float]:
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

    def consume(self, ctx: NetContext, tree: ExTree, choices: Collection[T] | None = None):
        """
                TODO:Scegliere i default ed eseguire la consume
                """
        if not choices:
            choices = []
        else:
            choices = list(choices)

        all_choices = self.__get_choices(tree)
        place_choosen = {p: None for p in all_choices.keys()}
        for t in choices:
            parent = list(t.in_arcs)[0].source
            if parent not in all_choices:
                continue
            if place_choosen[parent]:
                raise ValueError(f"{place_choosen[parent]} and {parent} can't be both choosen")

            place_choosen[parent] = t

        for p in place_choosen:
            if place_choosen[p]:
                continue
            default_choice = Defaults.get_default_by_region(ctx.region, NetUtils.Place.get_entry_id(p))
            if not default_choice:
                continue

            for arc in p.out_arcs:
                t = arc.target
                next_p = list(t.out_arcs)[0].target
                if NetUtils.Place.get_entry_id(next_p) == default_choice.id:
                    choices.append(t)
                    break

        new_marking, probability, impacts, delta = self.__consume(
            ctx.net, tree.current_node.snapshot.marking, choices
        )

        tree.add_snapshot(Snapshot(new_marking, probability, impacts, delta))

        return tree

    def __consume(self, net: N, marking: M, choices: Collection[T] | None = None) -> tuple[
        TimeMarking, int, list[int], float]:
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
            new_marking, next_p, next_i, next_delta = self.__consume(
                net, new_marking, choices
            )
            for i in range(len(next_i)):
                impacts[i] += next_i[i]

            return new_marking, next_p * probability, impacts, delta + next_delta
