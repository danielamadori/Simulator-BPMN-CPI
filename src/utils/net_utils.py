from typing import TypeVar

from pm4py import PetriNet

from src.model.time_spin import TimeMarking, PropertiesKeys
from src.model.types import P, T


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

    class Transition:

        @classmethod
        def get_region_id(cls, transition: T):
            return transition.properties.get(PropertiesKeys.ENTRY_RID)

        @classmethod
        def get_impacts(cls, transition: T):
            return transition.properties.get(PropertiesKeys.IMPACTS)

        @classmethod
        def get_probability(cls, transition: T):
            return transition.properties.get(PropertiesKeys.PROBABILITY)

        @classmethod
        def get_stop(cls, transition: T):
            return transition.properties.get(PropertiesKeys.STOP)
