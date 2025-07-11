from enum import Enum

from model.types import P, T, M


class NetUtils:

    @classmethod
    def get_label(cls, node: P | T):
        return node.properties.get(PropertiesKeys.LABEL)

    @classmethod
    def get_type(cls, node: P | T):
        return node.properties.get(PropertiesKeys.TYPE)

    class Place:

        @classmethod
        def get_duration(cls, node: P | T):
            return node.properties.get(PropertiesKeys.DURATION, 0)

        @classmethod
        def get_entry_id(cls, place: P):
            return place.properties.get(PropertiesKeys.ENTRY_RID)

        @classmethod
        def get_exit_id(cls, place: P):
            return place.properties.get(PropertiesKeys.EXIT_RID)

        @classmethod
        def get_impacts(cls, place: P):
            return place.properties.get(PropertiesKeys.IMPACTS)

    class Transition:

        @classmethod
        def get_region_id(cls, transition: T):
            return transition.properties.get(PropertiesKeys.ENTRY_RID)

        @classmethod
        def get_probability(cls, transition: T):
            return transition.properties.get(PropertiesKeys.PROBABILITY)

        @classmethod
        def get_stop(cls, transition: T):
            return transition.properties.get(PropertiesKeys.STOP)


class PropertiesKeys(Enum):
    ENTRY_RID = "entry_rid"  # Entry Region ID
    EXIT_RID = "exit_rid"  # Exit Region ID
    LABEL = "label"
    TYPE = "type"
    DURATION = "duration"
    IMPACTS = "impacts"
    PROBABILITY = "probability"
    STOP = "stop"


def get_all_choices(ctx, marking: M, choices: list[T] = None) -> list[T]:
    """
    Fills the choices with default transitions if they are not already present.
    If no default transitions are found, it returns the choices as is.
    :param ctx:
    :param marking:
    :param choices:
    :return:
    """
    if choices is None:
        choices = []

    choices = ctx.strategy.get_default_choices(ctx, marking, choices=choices)[:]
    choices_place = {list(t.in_arcs)[0].source for t in choices if t.in_arcs}

    for t in ctx.semantic.enabled_transitions(ctx.net, marking):
        place = list(t.in_arcs)[0].source
        if place not in choices_place:
            choices.append(t)
            choices_place.add(place)

    return list(choices)
