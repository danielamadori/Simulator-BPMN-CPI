from __future__ import annotations

from typing import Collection, Dict, Any

import pm4py
from typing_extensions import override

from utils.net_utils import PropertiesKeys


class WrapperPetriNet(pm4py.PetriNet):
    """
    Wrapper class for PetriNet to allow for custom properties.
    """

    class Place(pm4py.PetriNet.Place):
        """
        Custom Place class that can hold additional properties.
        """

        def __init__(self, name, in_arcs=None, out_arcs=None, properties=None):
            super().__init__(name=name, in_arcs=in_arcs, out_arcs=out_arcs, properties=properties)

            for arc in self.in_arcs:
                if not isinstance(arc, WrapperPetriNet.Arc):
                    raise TypeError("All in_arcs must be instances of WrapperPetriNet.Arc")

            for arc in self.out_arcs:
                if not isinstance(arc, WrapperPetriNet.Arc):
                    raise TypeError("All out_arcs must be instances of WrapperPetriNet.Arc")

            self.properties['custom'] = {}

        @override
        def __eq__(self, other):
            if not isinstance(other, WrapperPetriNet.Place):
                return False
            return other.name == self.name

        @override
        def __hash__(self):
            return hash(self.name)

        def set_custom_property(self, key, value):
            """
            Set a custom property for the Place.
            """
            self.custom_properties[key] = value

        def get_custom_property(self, key):
            """
            Get a custom property from the Place.
            """
            return self.custom_properties.get(key, None)

        def get_region_label(self):
            """
            Get the label of the region associated with this Place.
            """
            return self.get_custom_property(PropertiesKeys.LABEL)

        def set_region_label(self, label):
            """
            Set the label of the region associated with this Place.
            """
            self.set_custom_property(PropertiesKeys.LABEL, label)

        def get_type(self):
            """
            Get the type of the Place.
            """
            return self.get_custom_property(PropertiesKeys.TYPE)

        def set_type(self, type_value):
            """
            Set the type of the Place.
            """
            self.set_custom_property(PropertiesKeys.TYPE, type_value)

        def get_duration(self):
            """
            Get the duration associated with this Place.
            """
            return self.get_custom_property(PropertiesKeys.DURATION) or 0

        def set_duration(self, duration):
            """
            Set the duration associated with this Place.
            """
            self.custom_properties[PropertiesKeys.DURATION] = duration

        def get_entry_id(self):
            """
            Get the entry region ID associated with this Place.
            """
            return self.get_custom_property(PropertiesKeys.ENTRY_RID)

        def set_entry_id(self, entry_id):
            """
            Set the entry region ID associated with this Place.
            """
            self.set_custom_property(PropertiesKeys.ENTRY_RID, entry_id)

        def get_exit_id(self):
            """
            Get the exit region ID associated with this Place.
            """
            return self.get_custom_property(PropertiesKeys.EXIT_RID)

        def set_exit_id(self, exit_id):
            """
            Set the exit region ID associated with this Place.
            """
            self.set_custom_property(PropertiesKeys.EXIT_RID, exit_id)

        def get_impacts(self):
            """
            Get the impacts associated with this Place.
            """
            return self.get_custom_property(PropertiesKeys.IMPACTS)

        def set_impacts(self, impacts):
            """
            Set the impacts associated with this Place.
            """
            self.set_custom_property(PropertiesKeys.IMPACTS, impacts)

        def get_visit_limit(self):
            """
            Get the visit limit associated with this Place.
            """
            return self.get_custom_property(PropertiesKeys.VISIT_LIMIT)

        def set_visit_limit(self, visit_limit):
            """
            Set the visit limit associated with this Place if it's None.
            """
            if self.get_visit_limit() is None:
                self.set_custom_property(PropertiesKeys.VISIT_LIMIT, visit_limit)

        custom_properties = property(lambda self: self.properties['custom'])
        region_label = property(get_region_label, set_region_label)
        region_type = property(get_type, set_type)
        duration = property(get_duration, set_duration)
        entry_id = property(get_entry_id, set_entry_id)
        exit_id = property(get_exit_id, set_exit_id)
        impacts = property(get_impacts, set_impacts)
        visit_limit = property(get_visit_limit, set_visit_limit)

    class Transition(pm4py.PetriNet.Transition):
        """
        Custom Transition class that can hold additional properties.
        """

        def __init__(self, name, label=None, in_arcs=None, out_arcs=None, properties=None):
            super().__init__(name=name, label=label, in_arcs=in_arcs, out_arcs=out_arcs, properties=properties)
            for arc in self.in_arcs:
                if not isinstance(arc, WrapperPetriNet.Arc):
                    raise TypeError("All in_arcs must be instances of WrapperPetriNet.Arc")

            for arc in self.out_arcs:
                if not isinstance(arc, WrapperPetriNet.Arc):
                    raise TypeError("All out_arcs must be instances of WrapperPetriNet.Arc")

            self.properties['custom'] = {}

        @override
        def __eq__(self, other):
            if not isinstance(other, WrapperPetriNet.Transition):
                return False
            return other.name == self.name

        @override
        def __hash__(self):
            return hash(self.name)

        def set_custom_property(self, key, value):
            """
            Set a custom property for the Transition.
            """
            self.properties['custom'][key] = value

        def get_custom_property(self, key):
            """
            Get a custom property from the Transition.
            """
            return self.properties['custom'].get(key, None)

        def get_region_label(self):
            """
            Get the label of the region associated with this Transition.
            """
            return self.get_custom_property(PropertiesKeys.LABEL)

        def set_region_label(self, label):
            """
            Set the label of the region associated with this Transition.
            """
            self.set_custom_property(PropertiesKeys.LABEL, label)

        def get_region_type(self):
            """
            Get the type of the region associated with this Transition.
            """
            return self.get_custom_property(PropertiesKeys.TYPE)

        def set_region_type(self, type_value):
            """
            Set the type of the region associated with this Transition.
            """
            self.set_custom_property(PropertiesKeys.TYPE, type_value)

        def get_region_id(self):
            """
            Get the region ID associated with this Transition.
            """
            return self.get_custom_property(PropertiesKeys.ENTRY_RID)

        def set_region_id(self, region_id):
            """
            Set the region ID associated with this Transition.
            """
            self.set_custom_property(PropertiesKeys.ENTRY_RID, region_id)

        def get_probability(self):
            """
            Get the probability associated with this Transition.
            """
            return self.get_custom_property(PropertiesKeys.PROBABILITY)

        def set_probability(self, probability):
            """
            Set the probability associated with this Transition.
            """
            self.set_custom_property(PropertiesKeys.PROBABILITY, probability)

        def get_stop(self):
            """
            Get the stop condition associated with this Transition.
            """
            return self.get_custom_property(PropertiesKeys.STOP)

        def set_stop(self, stop_condition):
            """
            Set the stop condition associated with this Transition.
            """
            self.set_custom_property(PropertiesKeys.STOP, stop_condition)

        custom_properties = property(lambda self: self.properties['custom'])
        region_label = property(get_region_label, set_region_label)
        region_type = property(get_region_type, set_region_type)
        region_id = property(get_region_id, set_region_id)
        probability = property(get_probability, set_probability)
        stop = property(get_stop, set_stop)

    class Arc(pm4py.PetriNet.Arc):
        """
        Custom Arc class that can hold additional properties.
        """

        def __init__(self, source, target, weight=1, properties=None):
            super().__init__(source=source, target=target, weight=weight, properties=properties)

            if not isinstance(target, WrapperPetriNet.Transition | WrapperPetriNet.Place):
                raise TypeError("Target must be a Transition or Place instance")
            if not isinstance(source, WrapperPetriNet.Transition | WrapperPetriNet.Place):
                raise TypeError("Source must be a Transition or Place instance")

            self.properties['custom'] = {}

        @override
        def __hash__(self):
            return hash((self.source.name, self.target.name))

        def set_custom_property(self, key, value):
            """
            Set a custom property for the Arc.
            """
            self.custom_properties[key] = value

        def get_custom_property(self, key):
            """
            Get a custom property from the Arc.
            """
            return self.custom_properties.get(key, None)

        custom_properties = property(lambda self: self.properties['custom'])

    def __init__(self, name: str = None, places: Collection[Place] = None, transitions: Collection[Transition] = None,
                 arcs: Collection[Arc] = None, properties: Dict[str, Any] = None):
        super().__init__(name=name, places=places, transitions=transitions, arcs=arcs, properties=properties)
        self.__places: Collection[WrapperPetriNet.Place] = places if places is not None else set()
        self.__transitions: Collection[WrapperPetriNet.Transition] = transitions if transitions is not None else set()
        self.__arcs: Collection[WrapperPetriNet.Arc] = arcs if arcs is not None else set()
        self.__properties = properties if properties is not None else dict()

        for place in self.places:
            if not isinstance(place, WrapperPetriNet.Place):
                raise TypeError("All places must be instances of WrapperPetriNet.Place")

        for transition in self.transitions:
            if not isinstance(transition, WrapperPetriNet.Transition):
                raise TypeError("All transitions must be instances of WrapperPetriNet.Transition")

        for arc in self.arcs:
            if not isinstance(arc, WrapperPetriNet.Arc):
                raise TypeError("All arcs must be instances of WrapperPetriNet.Arc")

        self.properties['custom'] = {}

    @override
    def __eq__(self, other):
        if not isinstance(other, WrapperPetriNet):
            return False

        for place in self.places:
            if place not in other.places:
                return False

        for transition in self.transitions:
            if transition not in other.transitions:
                return False

        for arc in self.arcs:
            if arc not in other.arcs:
                return False

        return True

    def set_custom_property(self, key, value):
        """
        Set a custom property for the PetriNet.
        """
        self.custom_properties[key] = value

    def get_custom_property(self, key):
        """
        Get a custom property from the PetriNet.
        """
        return self.custom_properties.get(key, None)

    def __get_places(self) -> Collection[WrapperPetriNet.Place]:
        return self.__places

    def __get_transitions(self) -> Collection[WrapperPetriNet.Transition]:
        return self.__transitions

    def __get_arcs(self) -> Collection[WrapperPetriNet.Arc]:
        return self.__arcs

    def __get_properties(self) -> Dict[str, Any]:
        return self.__properties

    places = property(__get_places)
    transitions = property(__get_transitions)
    arcs = property(__get_arcs)
    properties = property(__get_properties)
    custom_properties = property(lambda self: self.properties['custom'])


