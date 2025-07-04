import itertools
import logging

from anytree import Node, PreOrderIter, RenderTree, findall_by_attr

from utils.net_utils import NetUtils
from .context import NetContext
from .snapshot import Snapshot
from .types import T, M

logger = logging.getLogger(__name__)


class ExTree:
    __separator = '/'
    current_node: Node
    __root: Node

    # Struttura Node: name[facoltativo],id,snapshot[oggetto di interesse]
    def __init__(self, root: Snapshot):
        logger.info("Inizializzazione ExTree")
        if root is None:
            logger.error("Lo Snapshot Root è None")
            raise ValueError("Root Snapshot can't be None")

        _root = Node(name="Root", id='-1', snapshot=root)
        self.__root = _root
        self.current_node = _root

    @classmethod
    def from_context(cls, ctx):
        places = ctx.initial_marking.keys()

        place = None
        for _p in places:
            if NetUtils.Place.get_impacts(_p):
                place = _p
                break

        place_impacts = NetUtils.Place.get_impacts(place)
        impacts = [0] * len(place_impacts)

        extree = ExTree(Snapshot(marking=ctx.initial_marking, probability=1, impacts=impacts, time=0))

        return extree

    @property
    def root(self):
        return self.__root

    def get_nodes(self):
        return list(PreOrderIter(self.__root))

    def exists(self, node: Node):
        return node in self

    def get_node_by_id(self, node_id: str):
        """
        Restituisce il nodo con l'ID specificato.
        """
        result = findall_by_attr(self.root, name='id', value=node_id)
        return list(result)[0] if len(list(result)) == 1 else None

    # Costruzione dell'albero
    def add_snapshot(self, ctx, snapshot: Snapshot, set_as_current: bool = True):
        parent = self.current_node
        for node in self:
            if node.parent == parent and node.snapshot.marking == snapshot.marking:
                return node

        idx = get_sorted_id(ctx, self.current_node.snapshot.marking, snapshot.marking)
        _id = "{}{}{}".format(parent.name, ExTree.__separator, idx)

        child_node = Node(
            name=str(_id), id=str(_id), snapshot=snapshot, parent=parent
        )

        if set_as_current:
            self.current_node = child_node

        return child_node

    def set_current(self, node: Node | str):
        if isinstance(node, str):
            node = self.get_node_by_id(node)

        if node is None or node not in self:
            return False

        self.current_node = node
        return True

    # Visualizzazione Albero
    def print_tree(self):
        for pre, fill, node in RenderTree(self.__root):
            if self.current_node.id == node.id:
                print("X" + f"{pre}{node.name}" + "X")
            else:
                print(f"{pre}{node.name}")

    def __repr__(self):
        return self.print_tree()

    def __str__(self):
        return repr(self)

    def __iter__(self):
        return PreOrderIter(self.__root)

    def __contains__(self, item):
        if not isinstance(item, Node):
            return False

        for node in self:
            if is_equal(node, item):
                return True

        return False

    def __len__(self):
        nodes = self.get_nodes()
        return len(nodes)


def is_equal(node1: Node, node2: Node):
    if node1.parent != node2.parent:
        return False
    if node1.snapshot.marking != node2.snapshot.marking:
        return False

    return True


def get_sorted_id(ctx, current_marking, new_marking):
    sorted_child = get_current_sorted_children(ctx, current_marking)
    idx_child = sorted_child.index(new_marking)

    if idx_child == -1:
        raise ValueError("The new snapshot can't be reached from the current node")

    return idx_child


def get_current_sorted_children(ctx: NetContext, marking) -> list[M]:
    curr_time_marking = marking
    exec_strategy = ctx.strategy

    choices = exec_strategy.get_choices(ctx, curr_time_marking)
    transition_groups = list(choices.values())
    transition_combinations = list(itertools.product(*transition_groups))
    key_to_time_marking = {}

    for combination in transition_combinations:
        key_of_time_marking = [t.name for t in combination if t is not None]
        temp, *_ = exec_strategy.consume(ctx, curr_time_marking, combination)
        key_to_time_marking.update({tuple(key_of_time_marking): temp})

    children = []
    for key_row in sorted(list(key_to_time_marking.keys())):
        children.append(key_to_time_marking[key_row])

    return children
