from typing import Tuple

import pm4py
import pydantic
from anytree import Node
from pm4py import PetriNet
from pydantic import model_validator, BaseModel

from model.extree import ExTree
from model.region import RegionModel, RegionType
from model.snapshot import Snapshot
from model.time_spin import TimeMarking, get_place_by_name
from utils.net_utils import PropertiesKeys

# Marking
type Marking = dict[str, dict[str, float]]


def model_to_marking(petri_net_obj, marking_model: Marking):
    im = pm4py.Marking()
    age = {}
    net = petri_net_obj
    for place_name in marking_model:
        place_prop = marking_model[place_name]
        place = get_place_by_name(net, place_name)
        if not place:
            raise ValueError(f"Place '{place_name}' not found in the Petri net.")
        im[place] = int(place_prop.get('token', 0))
        age[place] = place_prop.get('age', 0.0)
    return TimeMarking(im, age)


# PetriNetModel
class PetriNetModel(pydantic.BaseModel):
    """
    Represents a Petri net structure.
    """

    class TransitionModel(BaseModel):
        """
        Represents a transition in a Petri net.
        """
        id: str
        label: str | None = None
        region_id: str = None
        region_type: RegionType = None
        probability: float = 1
        stop: bool = False

    class PlaceModel(BaseModel):
        """ Represents a place in a Petri net.
        """
        id: str
        label: str | None = None
        region_type: RegionType = None
        entry_region_id: str | None = None
        exit_region_id: str | None = None
        duration: float = 0.0
        impacts: list[float] | None = None

    class ArcModel(BaseModel):
        """
        Represents an arc in a Petri net.
        """
        source: str
        target: str
        weight: int | None = None

    name: str = ""
    transitions: list[TransitionModel]
    places: list[PlaceModel]
    arcs: list[ArcModel]
    initial_marking: Marking
    final_marking: Marking

    class Config:
        allow_mutation = False
        frozen = True
        use_enum_values = True


# ExecutionTreeModel
class ExecutionTreeModel(pydantic.BaseModel):
    """
    Represents an execution tree structure.
    """

    class NodeModel(BaseModel):
        """
        Represents a node in the execution tree.
        """

        class SnapshotModel(BaseModel):
            """
            Represents a snapshot of the execution state.
            """
            marking: Marking
            probability: float
            impacts: list[float]
            execution_time: float

        name: str
        id: str
        snapshot: SnapshotModel
        children: list['ExecutionTreeModel.NodeModel'] = []

    root: NodeModel
    current_node: str

    class Config:
        allow_mutation = False
        frozen = True
        use_enum_values = True


# ExecuteRequest
class ExecuteRequest(pydantic.BaseModel):
    """
    Represents a request to execute a command with optional parameters.
    """
    bpmn: RegionModel
    petri_net: PetriNetModel | None = None
    execution_tree: ExecutionTreeModel | None = None
    choices: list[str] | None = None

    class Config:
        allow_mutation = False
        frozen = True
        use_enum_values = True

    @model_validator(mode='after')
    def check_execution(self):
        checks = [
            self.petri_net is not None,
            self.execution_tree is not None,
            self.choices is not None
        ]
        if not all(checks) and any(checks):
            raise ValueError("If one of 'petri_net', 'execution_tree', or 'choices' is provided, all must be provided.")

        return self

    def to_object(self) -> Tuple[RegionModel, PetriNet, TimeMarking, TimeMarking, ExTree, list[str]]:
        """
        Converts the ExecuteRequest to its component objects.
        """
        region_model = self.bpmn
        petri_net_model = self.petri_net
        execution_tree_model = self.execution_tree

        if not isinstance(region_model, RegionModel):
            raise TypeError("Expected 'bpmn' to be of type 'RegionModel'.")

        if petri_net_model is not None and not isinstance(petri_net_model, PetriNetModel):
            raise TypeError("Expected 'petri_net' to be of type 'PetriNetModel'.")

        if execution_tree_model is not None and not isinstance(execution_tree_model, ExecutionTreeModel):
            raise TypeError("Expected 'execution_tree' to be of type 'ExecutionTreeModel'.")

        return self.bpmn, self.petri_net_obj, self.initial_marking, self.final_marking, self.execution_tree_obj, self.choices

    @property
    def petri_net_obj(self):
        """
        Converts the PetriNetModel to a PetriNet object.
        """
        if self.petri_net is None:
            return None

        transitions = {}
        for transition in self.petri_net.transitions:
            prop = {
                PropertiesKeys.LABEL: transition.label,
                PropertiesKeys.TYPE: transition.region_type,
                PropertiesKeys.STOP: transition.stop,
                PropertiesKeys.ENTRY_RID: transition.region_id,
                PropertiesKeys.PROBABILITY: transition.probability
            }
            transitions[transition.id] = PetriNet.Transition(
                name=transition.id,
                label=transition.label,
                properties=prop
            )

        places = {}
        for place in self.petri_net.places:
            prop = {
                PropertiesKeys.LABEL: place.label,
                PropertiesKeys.TYPE: place.region_type,
                PropertiesKeys.ENTRY_RID: place.entry_region_id,
                PropertiesKeys.EXIT_RID: place.exit_region_id,
                PropertiesKeys.DURATION: place.duration,
                PropertiesKeys.IMPACTS: place.impacts
            }
            places[place.id] = PetriNet.Place(
                name=place.id,
                properties=prop
            )

        arcs = []
        places_keys = set(places.keys())
        transitions_keys = set(transitions.keys())

        for arc in self.petri_net.arcs:
            source = None
            if arc.source in places_keys:
                source = places[arc.source]
            elif arc.source in transitions_keys:
                source = transitions[arc.source]

            target = None
            if arc.target in places_keys:
                target = places[arc.target]
            elif arc.target in transitions_keys:
                target = transitions[arc.target]

            arcs.append(PetriNet.Arc(
                source=source,
                target=target,
                weight=arc.weight or 1
            ))

        petri_net = PetriNet(
            name=self.petri_net.name,
            transitions=list(transitions.values()),
            places=list(places.values()),
            arcs=arcs
        )

        return petri_net

    @property
    def initial_marking(self) -> TimeMarking | None:
        """
        Converts the initial marking to a TimeMarking object.
        """
        if not self.petri_net or not self.petri_net.initial_marking:
            return None

        return model_to_marking(self.petri_net_obj, self.petri_net.initial_marking)

    @property
    def final_marking(self) -> TimeMarking | None:
        """
        Converts the final marking to a TimeMarking object.
        """
        if not self.petri_net or not self.petri_net.final_marking:
            return None

        return model_to_marking(self.petri_net_obj, self.petri_net.final_marking)


    @property
    def execution_tree_obj(self) -> ExTree | None:
        """
        Converts the ExecutionTreeModel to an ExTree object.
        """
        if self.execution_tree is None:
            return None

        root_snapshot = Snapshot(
            marking=model_to_marking(self.petri_net_obj, self.execution_tree.root.snapshot.marking),
            probability=self.execution_tree.root.snapshot.probability,
            impacts=self.execution_tree.root.snapshot.impacts,
            time=self.execution_tree.root.snapshot.execution_time
        )

        ex_tree = ExTree(root_snapshot)

        # Populate the execution tree with nodes
        def add_nodes(node_model, parent_node):
            for child in node_model.children:
                snapshot = Snapshot(
                    marking=model_to_marking(self.petri_net_obj, child.snapshot.marking),
                    probability=child.snapshot.probability,
                    impacts=child.snapshot.impacts,
                    time=child.snapshot.execution_time
                )
                child_node = Node(name=child.name, id=child.id, snapshot=snapshot, parent=parent_node)
                child_node.name = child.name
                child_node.id = child.id
                child_node.parent = parent_node
                add_nodes(child, child_node)

        root_node = Node(name=self.execution_tree.root.name, id=self.execution_tree.root.id, snapshot=root_snapshot,
                         parent=None)
        add_nodes(self.execution_tree.root, root_node)

        return ex_tree
