#  Copyright (c) 2025.

from __future__ import annotations

import logging
from typing import Iterator, TYPE_CHECKING

from anytree import Node, PreOrderIter, RenderTree, findall_by_attr, findall

from model.extree import ExecutionTreeNode
from model.status import ActivityState, propagate_status
from strategy.execution import add_impacts
from utils import logging_utils
from utils.net_utils import get_empty_impacts, is_final_marking
from model.extree.node import Snapshot

if TYPE_CHECKING:
	from model.types import SnapshotType, NodeType, ContextType, MarkingType, RegionModelType

logger = logging_utils.get_logger(__name__)


def serial_generator(initial: int = 1):
	"""Generates a unique serial number each time it is called."""
	n = initial
	while True:
		yield n
		n += 1





class ExecutionTree:
	"""
	ExTree is a tree structure for managing and traversing snapshots of Petri net markings.

	Attributes:
		current_node (Node): The current node in the tree.
		root (Node): The root node of the tree.
	"""
	__separator: str = '/'
	current_node: NodeType
	__root: NodeType
	__id_generator: Iterator[int]

	# Struttura Node: name[facoltativo],id,snapshot[oggetto di interesse]
	def __init__(self, root: SnapshotType | NodeType, generator: Iterator[int] = None):
		self.__id_generator = generator or serial_generator()
		if root is None:
			logger.error("Cannot initialize ExecutionTree with None root")
			raise ValueError("Root Snapshot can't be None")

		if isinstance(root, ExecutionTreeNode):
			self.__root = root
			self.current_node = root
			if generator is None:
				max_id = -1
				for node in PreOrderIter(root):
					max_id = max(max_id, int(node.id))

				self.__id_generator = serial_generator(max_id + 1)
			return

		_root = ExecutionTreeNode(name="Root", _id='0', snapshot=root)
		self.__root = _root
		self.current_node = _root

	@classmethod
	def from_context(cls, ctx: ContextType, region: "RegionModelType") -> ExecutionTree:
		places = ctx.net.places

		place = None
		for _p in places:
			if _p.impacts:
				place = _p
				break

		place_impacts = place.impacts
		impacts = [0] * len(place_impacts)


		status_by_region: dict[RegionModelType, ActivityState] = {}
		def build_status(r: RegionModelType):
			status_by_region[r] = ActivityState.WAITING
			if r.children:
				for child in r.children:
					build_status(child)
		build_status(region)

		regions: dict[int, RegionModelType] = {}
		def build_region_dict(r: RegionModelType):
			regions[r.id] = r
			if r.children:
				for child in r.children:
					build_region_dict(child)
		build_region_dict(region)

		# Initialize statuses from the initial marking so the first snapshot is meaningful.
		initial_marking = ctx.initial_marking
		for place in ctx.net.places:
			entry_id = getattr(place, "entry_id", None)
			if entry_id is not None:
				region_entry = regions.get(entry_id)
				if region_entry and initial_marking[place].token > 0:
					status_by_region[region_entry] = ActivityState.ACTIVE

			exit_id = getattr(place, "exit_id", None)
			if exit_id is not None:
				region_exit = regions.get(exit_id)
				if region_exit and region_exit.is_task():
					item = initial_marking[place]
					if item.token > 0 or item.visit_count > 0:
						status_by_region[region_exit] = ActivityState.COMPLETED

		propagate_status(region, status_by_region)
		status = {r.id: s for r, s in status_by_region.items()}

		extree = ExecutionTree(Snapshot(marking=ctx.initial_marking, probability=1, impacts=impacts, time=0, status=status, decisions=[], choices=[]))

		return extree

	@property
	def root(self):
		return self.__root

	def get_nodes(self):
		return list(PreOrderIter(self.__root))

	def exists(self, node: NodeType):
		return node in self

	def get_node_by_id(self, node_id: str):
		"""
		Restituisce il nodo con l'ID specificato.
		"""
		result = findall_by_attr(self.root, name='id', value=node_id)
		return list(result)[0] if len(list(result)) == 1 else None

	# Costruzione dell'albero
	def add_snapshot(self, ctx: ContextType, snapshot: SnapshotType, set_as_current: bool = True):
		parent = self.current_node
		logger.debug("Adding snapshot to ExecutionTree")

		# Final marking check
		if is_final_marking(ctx, self.current_node.snapshot.marking):
			logger.debug(f"Snapshot {self.current_node.id} is final. Skipping...")
			return self.current_node

		# If exists a node with the same marking under the current parent, return that node
		for node in self:
			if node.parent == parent and node.snapshot.marking == snapshot.marking:
				logger.debug("Snapshot already exists under current parent. Returning existing node.")
				if set_as_current:
					self.set_current(node)

				return node

		parent_probability = parent.snapshot.probability if parent is not None else 1
		parent_impacts = parent.snapshot.impacts if parent is not None else get_empty_impacts(ctx.net)
		parent_time = parent.snapshot.execution_time if parent is not None else 0

		_id = next(self.__id_generator)

		cumulative_snapshot = Snapshot(marking=snapshot.marking, probability=parent_probability * snapshot.probability,
										   impacts=add_impacts(parent_impacts, snapshot.impacts),
										   time=parent_time + snapshot.execution_time,
										   status=snapshot.status,
										   decisions=snapshot.decisions,
										   choices=snapshot.choices
										   )#TODO Daniel

		child_node = ExecutionTreeNode(name=str(_id), _id=str(_id), snapshot=cumulative_snapshot, parent=parent)

		if set_as_current:
			self.set_current(child_node)

		logger.debug(f"Added new snapshot node with ID {child_node.id} under parent ID {parent.id if parent else 'None'}")

		return child_node

	def set_current(self, node: NodeType | str):
		logger.debug(f"Setting current node to {node}")
		if isinstance(node, str):
			node = self.get_node_by_id(node)

		if node is None or node not in self:
			logger.warning("Node not found in the tree. Skipping...")
			return False

		self.current_node = self.get_node_by_id(node.id)
		logger.debug(f"Current node set to {node}")
		return True

	# Visualizzazione Albero
	def print_tree(self):
		for pre, fill, node in RenderTree(self.__root):
			if self.current_node.id == node.id:
				print(f"X{pre}{node.name}X")
			else:
				print(f"{pre}{node.name}")

	def search_nodes_by_marking(self, marking: MarkingType) -> list[NodeType]:
		"""
		Search for nodes that match the given marking in the execution tree.
		:param marking: The marking to search for. Can be partial or complete.
		:return: The list of nodes with the matching marking.
		"""

		def check_marking(node: NodeType):
			valid = True
			__marking = node.snapshot.marking
			for key in __marking.keys() | marking.keys():
				token, age, _ = marking[key]
				other_token, other_age, _ = __marking[key]
				if token != other_token or age != other_age:
					valid = False
					break

			if valid:
				logger.debug(f"Node {node.id} matches. {marking} ~= {node.snapshot.marking}")

			return valid

		return list(findall(self.root, check_marking))

	def __repr__(self):
		return self.print_tree()

	def __str__(self):
		return repr(self)

	def __iter__(self):
		return PreOrderIter(self.__root)

	def __contains__(self, item):
		if not isinstance(item, ExecutionTreeNode):
			return False

		for node in self:
			if is_equal(node, item):
				return True

		return False

	def __len__(self):
		nodes = self.get_nodes()
		return len(nodes)


def is_equal(node1: NodeType, node2: NodeType) -> bool:
	if node1.parent != node2.parent:
		return False
	if node1.snapshot.marking != node2.snapshot.marking:
		return False

	return True
