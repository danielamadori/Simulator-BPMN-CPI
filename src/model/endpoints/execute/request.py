from __future__ import annotations
from typing import Tuple, Any, TYPE_CHECKING, TypeAlias
import pm4py
import pydantic
from anytree import Node
from pm4py.objects.petri_net.utils.petri_utils import get_transition_by_name
from pydantic import model_validator, BaseModel, ConfigDict, Field

from model.extree import ExecutionTree
from model.petri_net.time_spin import TimeMarking
from model.petri_net.wrapper import WrapperPetriNet
from utils import logging_utils
from utils.net_utils import add_arc_from_to, get_place_by_name
from model.extree.node import Snapshot, ExecutionTreeNode

if TYPE_CHECKING:
	from model.types import TransitionType, MarkingType, ExTreeType

logger = logging_utils.get_logger(__name__)

MarkingModel: TypeAlias = dict[str, dict[str, Any]]


def model_to_marking(petri_net_obj: PetriNetModel, marking_model: MarkingModel):
	logger.debug("Creating marking from model: %s", marking_model)
	im = pm4py.Marking()
	age = {}
	visit_count = {}
	net = petri_net_obj

	for place_name in marking_model:
		place_prop = marking_model[place_name]
		place = get_place_by_name(net, place_name)      # Works even if typing is not correct
		if not place:
			logger.error("Could not find place %s", place_name)
			raise ValueError(f"Place '{place_name}' not found in the Petri net.")
		im[place] = int(place_prop.get('token', 0))
		age[place] = place_prop.get('age', 0.0)
		visit_count[place] = place_prop.get('visit_count', 0)

	return TimeMarking(im, age, visit_count)


class PetriNetModel(pydantic.BaseModel):
	"""
	Represents a Petri net structure.
	"""

	class TransitionModel(BaseModel):
		"""
		Represents a transition in a Petri net.
		"""
		id: str | int
		label: str | None = None
		region_id: str | int = None
		region_type: RegionType = None
		probability: float = 1
		stop: bool = False

	class PlaceModel(BaseModel):
		""" Represents a place in a Petri net.
		"""
		id: str | int
		label: str | None = None
		region_type: RegionType = None
		entry_region_id: str | int | None = None
		exit_region_id: str | int | None = None
		duration: float = 0.0
		impacts: list[float] | None = None
		visit_limit: int | None = None

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
	initial_marking: MarkingModel
	final_marking: MarkingModel

	model_config = ConfigDict(use_enum_values=True)


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
			marking: MarkingModel
			probability: float
			impacts: list[float]
			execution_time: float
			#TODO Daniel add parameters
			status:dict
			decisions:list
			choices:list

		name: str
		id: str
		snapshot: SnapshotModel
		children: list['ExecutionTreeModel.NodeModel'] = Field(default_factory=list)

	root: NodeModel
	current_node: str

	model_config = ConfigDict(use_enum_values=True)

from pydantic import field_validator
from model.region import RegionModel, RegionType

class ExecuteRequest(pydantic.BaseModel):
	"""
	Represents a request to execute a command with optional parameters.
	"""
	bpmn: RegionModel
	petri_net: PetriNetModel | None = None
	execution_tree: ExecutionTreeModel | None = None
	choices: list[str] | None = None

	model_config = ConfigDict(use_enum_values=True)

	@field_validator("bpmn", mode="before")

	@classmethod
	def _coerce_bpmn_parse_tree_to_regionmodel(cls, v):
		if isinstance(v, RegionModel):
			return v

		if not isinstance(v, dict):
			raise TypeError("bpmn must be a dict or RegionModel.")

		if "id" not in v or "type" not in v:
			raise TypeError("bpmn dict must be a parse-tree node with keys 'id' and 'type'.")

		type_map = {
			"sequential": RegionType.SEQUENTIAL,
			"parallel":   RegionType.PARALLEL,
			"nature":     RegionType.NATURE,
			"choice":     RegionType.CHOICE,
			"task":       RegionType.TASK,
			"loop":       RegionType.LOOP,
		}

		def normalize_duration(value, node_id):
			from numbers import Number
			if isinstance(value, Number):
				return float(value)
			if isinstance(value, list):
				if len(value) == 2:
					return float(value[1])
				if len(value) == 1:
					return float(value[0])
				raise TypeError(f"Invalid duration list length for node {node_id}: {len(value)}")
			raise TypeError(f"Invalid duration type for node {node_id}: {type(value)}")

		def normalize_node(node: dict) -> dict:
			node = dict(node)
			node_id = node.get("id")
			node_type = node.get("type")

			if isinstance(node_type, str):
				t_lower = node_type.lower()
				if t_lower in type_map:
					node["type"] = type_map[t_lower]
				else:
					print(f"[VALIDATOR] unknown type: {node_type}")
					raise TypeError(f"Unknown region type '{node_type}' in node {node_id}")

			if "duration" in node:
				node["duration"] = normalize_duration(node["duration"], node_id)

			if "children" in node and isinstance(node["children"], list):
				node["children"] = [normalize_node(c) for c in node["children"]]
			return node

		normalized = normalize_node(v)
		result = RegionModel.model_validate(normalized)
		return result


	@model_validator(mode='after')
	def check_execution(self):
		checks = [
			self.petri_net is not None,
			self.execution_tree is not None
		]
		if not all(checks) and any(checks):
			logger.error("Provided data are not enough: petri_net=%s, execution_tree=%s", self.petri_net is not None, self.execution_tree is not None)
			raise ValueError("If one of 'petri_net' or 'execution_tree', all must be provided.")

		if not all(checks) and self.choices is not None:
			logger.error("Choices provided without petri_net and execution_tree.")
			raise ValueError("If 'choices' is provided, 'petri_net' and 'execution_tree' must also be provided.")

		return self

	def to_object(self) -> Tuple[RegionModel, WrapperPetriNet, TimeMarking, TimeMarking, ExecutionTree, list[TransitionType]]:
		"""
		Converts the ExecuteRequest to its component objects.
		"""
		region_model = self.bpmn
		petri_net_model = self.petri_net
		execution_tree_model = self.execution_tree

		if not isinstance(region_model, RegionModel):
			logger.exception("Not valid region_model in request")
			raise TypeError("Expected 'bpmn' to be of type 'RegionModel'.")

		if petri_net_model is not None and not isinstance(petri_net_model, PetriNetModel):
			logger.exception("Not valid petri_net_model in request")
			raise TypeError("Expected 'petri_net' to be of type 'PetriNetModel'.")

		if execution_tree_model is not None and not isinstance(execution_tree_model, ExecutionTreeModel):
			logger.exception("Not valid execution_tree_model in request")
			raise TypeError("Expected 'execution_tree' to be of type 'ExecutionTreeModel'.")

		return self.bpmn, self.petri_net_obj, self.initial_marking, self.final_marking, self.execution_tree_obj, self.choices_obj

	@property
	def petri_net_obj(self):
		"""
		Converts the PetriNetModel to a PetriNet object.
		"""
		logger.debug("Converting PetriNet request to PetriNet model")
		if self.petri_net is None:
			logger.debug("No Petri net provided. Skipping conversion...")
			return None

		petri_net = WrapperPetriNet(name=self.petri_net.name)

		transitions = {}
		for transition in self.petri_net.transitions:
			logger.debug("Converting transition %s", transition)
			net_transition = WrapperPetriNet.Transition(name=transition.id, label=transition.label)
			net_transition.region_id = transition.region_id
			net_transition.region_type = transition.region_type
			net_transition.region_label = transition.label
			net_transition.probability = transition.probability
			net_transition.stop = transition.stop

			transitions[transition.id] = net_transition
			petri_net.transitions.add(net_transition)
			logger.debug("Transition added: %s", net_transition)

		places = {}
		for place in self.petri_net.places:
			logger.debug("Converting place %s", place)
			net_place = WrapperPetriNet.Place(name=place.id)
			net_place.entry_id = place.entry_region_id
			net_place.exit_id = place.exit_region_id
			net_place.region_type = place.region_type
			net_place.region_label = place.label
			net_place.duration = place.duration
			net_place.impacts = place.impacts
			net_place.visit_limit = place.visit_limit

			places[place.id] = net_place
			petri_net.places.add(net_place)
			logger.debug("Place added: %s", net_place)

		for arc in self.petri_net.arcs:
			logger.debug("Converting arc %s", arc)
			source = None
			if arc.source in places:
				source = places[arc.source]
			elif arc.source in transitions:
				source = transitions[arc.source]

			target = None
			if arc.target in places:
				target = places[arc.target]
			elif arc.target in transitions:
				target = transitions[arc.target]

			add_arc_from_to(source, target, petri_net)


		return petri_net

	@property
	def initial_marking(self) -> MarkingType | None:
		"""
		Converts the initial marking to a TimeMarking object.
		"""
		if not self.petri_net:
			logger.debug("No petri net provided, skipping initial marking conversion.")
			return None

		if not self.petri_net.initial_marking:
			logger.error("No initial marking provided in the petri net. Trying to infer it from net")
			return None

		return model_to_marking(self.petri_net_obj, self.petri_net.initial_marking)

	@property
	def final_marking(self) -> MarkingType | None:
		"""
		Converts the final marking to a TimeMarking object.
		"""
		if not self.petri_net:
			logger.debug("No petri net provided, skipping final marking conversion.")
			return None
		if not self.petri_net.final_marking:
			logger.warning("No final marking provided, trying to infer it from net.")
			return None

		return model_to_marking(self.petri_net_obj, self.petri_net.final_marking)

	@property
	def execution_tree_obj(self) -> ExTreeType | None:
		"""
		Converts the ExecutionTreeModel to an ExTree object.
		"""
		if self.execution_tree is None:
			logger.debug("No execution tree provided, skipping conversion.")
			return None

		logger.debug("Converting execution tree to an ExTree model")

		def convert_node(node: ExecutionTreeModel.NodeModel, parent: ExecutionTreeNode | None = None) -> Node:
			logger.debug("Converting node %s, parent %s", node.name, parent.name if parent else None)

			current_node = ExecutionTreeNode(
				name=node.name,
				_id=node.id,
				snapshot=Snapshot(#TODO Daniel
					marking=model_to_marking(self.petri_net_obj, node.snapshot.marking),
					probability=node.snapshot.probability,
					impacts=node.snapshot.impacts,
					time=node.snapshot.execution_time,
					status=node.snapshot.status,
					decisions=node.snapshot.decisions,
					choices=node.snapshot.choices
				),
				parent=parent
			)

			if node.children is None or len(node.children) == 0:
				return current_node

			for child in node.children:
				convert_node(child, parent=current_node)

			return current_node

		root = convert_node(self.execution_tree.root)

		ex_tree = ExecutionTree(root)

		if not ex_tree.set_current(self.execution_tree.current_node):
			logger.error(f"Failed to set current execution tree. Current node id: {self.execution_tree.current_node} not found.")
			raise ValueError("Current node not found in the execution tree.")

		return ex_tree

	@property
	def choices_obj(self) -> list[TransitionType] | None:
		"""
		Returns the choices as a list of strings.
		"""
		if not self.petri_net:
			logger.debug("No petri net provided, skipping choices conversion.")
			return None
		logger.debug("Converting choices to a Choices model")

		if not self.choices:
			return []

		transitions = []
		for choice in self.choices:
			t = get_transition_by_name(self.petri_net_obj, choice)
			if not t:
				logger.warning("Choice '%s' not found in the Petri net transitions.", choice)
				continue
			transitions.append(t)

		return transitions
