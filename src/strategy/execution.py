from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Collection, Set, TypeVar


from model.time_spin import NetUtils, TimeMarking
from model.types import N, T, P, M
from utils.default import Defaults

ContextType = TypeVar("ContextType", bound="NetContext")


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

    def get_stoppable_active_transitions(self, ctx: ContextType, marking: M) -> Set[T]:
        enabled_transitions = ctx.semantic.enabled_transitions(ctx.net, marking)
        # Filtro per transizoni con stop attivo
        enabled_transitions = filter(
            lambda x: NetUtils.Transition.get_stop(x), enabled_transitions
        )

        return set(enabled_transitions)

    def get_choices(self, ctx: ContextType, marking: M):
        return self.__get_choices(ctx, marking)

    def __get_choices(self, ctx: ContextType, marking: M) -> Dict[P, List[T]]:
        enabled_transitions = self.get_stoppable_active_transitions(ctx, marking)

        groups = {}
        for t in enabled_transitions:
            parent = list(t.in_arcs)[0].source
            if groups.get(parent) is None:
                groups.update({parent: []})

            groups[parent].append(t)

        return groups

    def saturate(self, ctx: ContextType, marking: M) -> tuple[M, float]:
        net = ctx.net
        if len(ctx.semantic.enabled_transitions(net, marking)) > 0:
            return marking, 0

        # Get current place with tokens
        current_places = list(filter(lambda x: marking.marking[x] > 0, marking.keys()))
        min_delta = float("inf")
        for p in current_places:
            # Get the duration of the place
            duration = NetUtils.Place.get_duration(p)
            min_delta = min(min_delta, duration - marking.age[p])

        if min_delta == float("inf"):
            # No places with tokens, return the current marking and 0 delta
            return marking, 0

        # Return the current marking with updated ages
        return marking.add_time(min_delta), min_delta



        # raw_semantic = ctx.semantic
        # _saturable_trans = raw_semantic.enabled_transitions(net, marking.marking)
        # saturable_trans = [t for t in net.transitions if t in _saturable_trans]
        # k = {}
        # for t in saturable_trans:
        #     _max = 0
        #     for arc in t.in_arcs:
        #         parent_place = arc.source
        #         curr_delta = (
        #                 NetUtils.Place.get_duration(parent_place)
        #                 - marking.age[parent_place]
        #         )
        #         _max = max(curr_delta, _max)
        #
        #     k.update({t: _max})
        # min_delta = min(k.values())
        #
        # new_age = {}
        # for p in marking.marking:
        #     token, age = marking[p]
        #     if token == 0:
        #         continue
        #     new_age[p] = age + min_delta

        # return TimeMarking(marking.marking, new_age), min_delta

    def consume(self, ctx: ContextType, marking: M, choices: Collection[T] | None = None):
        """
        TODO:Scegliere i default ed eseguire la consume
        """
        if not choices:
            choices = []
        else:
            choices = list(choices)

        all_choices = self.get_choices(ctx, marking)
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
            ctx, marking, choices
        )

        return new_marking, probability, impacts, delta

    def __consume(self, ctx: ContextType, marking: M, choices: Collection[T] | None = None) -> tuple[
        TimeMarking, int, list[int], float]:
        net = ctx.net
        new_marking, delta = self.saturate(ctx, marking)
        probability = 1
        sem = ctx.semantic
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
                ctx, new_marking, choices
            )
            for i in range(len(next_i)):
                impacts[i] += next_i[i]

            return new_marking, next_p * probability, impacts, delta + next_delta
