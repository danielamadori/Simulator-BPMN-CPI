import pm4py
from typing_extensions import override


class WrapperPetriNet(pm4py.PetriNet):
    """
    Wrapper class for PetriNet to allow for custom properties.
    """

    class Place(pm4py.PetriNet.Place):
        """
        Custom Place class that can hold additional properties.
        """

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.custom_properties = {}

        @override
        def __eq__(self, other):
            if not isinstance(other, WrapperPetriNet.Place):
                return False
            return other.name == self.name

        @override
        def __hash__(self):
            return hash(self.name)

        def set_property(self, key, value):
            """
            Set a custom property for the Place.
            """
            self.custom_properties[key] = value

        def get_property(self, key):
            """
            Get a custom property from the Place.
            """
            return self.custom_properties.get(key, None)

    class Transition(pm4py.PetriNet.Transition):
        """
        Custom Transition class that can hold additional properties.
        """

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.custom_properties = {}

        @override
        def __eq__(self, other):
            if not isinstance(other, WrapperPetriNet.Transition):
                return False
            return other.name == self.name

        @override
        def __hash__(self):
            return hash(self.name)

        def set_property(self, key, value):
            """
            Set a custom property for the Transition.
            """
            self.custom_properties[key] = value

        def get_property(self, key):
            """
            Get a custom property from the Transition.
            """
            return self.custom_properties.get(key, None)

    class Arc(pm4py.PetriNet.Arc):
        """
        Custom Arc class that can hold additional properties.
        """

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.custom_properties = {}

        @override
        def __hash__(self):
            return hash((self.source.name, self.target.name))

        def set_property(self, key, value):
            """
            Set a custom property for the Arc.
            """
            self.custom_properties[key] = value

        def get_property(self, key):
            """
            Get a custom property from the Arc.
            """
            return self.custom_properties.get(key, None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_properties = {}

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

    def set_property(self, key, value):
        """
        Set a custom property for the PetriNet.
        """
        self.custom_properties[key] = value

    def get_property(self, key):
        """
        Get a custom property from the PetriNet.
        """
        return self.custom_properties.get(key, None)


def add_arc_from_to(fr, to, net, weight=1, type=None) -> WrapperPetriNet.Arc:
    """
    Function used instead of pm4py.objects.petri_net.utils.petri_utils.add_arc_from_to to add wrapped arc.

    :param fr: transition/place from
    :param to:  transition/place to
    :param net: net to use
    :param weight: weight associated to the arc
    :param type: type of arc. Possible values: None
    :return: arc attached to petri net
    """
    a = WrapperPetriNet.Arc(fr, to, weight)

    net.arcs.add(a)
    fr.out_arcs.add(a)
    to.in_arcs.add(a)
    return a