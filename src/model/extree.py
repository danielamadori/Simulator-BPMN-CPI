import itertools
import logging

from anytree import Node, PreOrderIter, RenderTree

from utils.net_utils import NetUtils
from .context import NetContext
from .snapshot import Snapshot
from .types import T

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
        return ExTree(Snapshot(ctx.initial_marking, 1, impacts, 0))

    def get_nodes(self):
        return list(PreOrderIter(self.__root))

    def exists(self, node: Node):
        return node in self

    # Costruzione dell'albero
    def add_snapshot(self, ctx, snapshot: Snapshot, set_as_current: bool = True):
        parent = self.current_node
        for node in self:
            if node.parent == parent and node.snapshot.marking == snapshot.marking:
                return node

        idx = add_exec_inorder(ctx, self, snapshot)
        _id = parent.name + ExTree.__separator + idx
        child_node = Node(
            name=str(_id), id=str(_id), snapshot=snapshot, parent=parent
        )

        if set_as_current:
            self.current_node = child_node

        return child_node

    def set_current(self, node: Node):
        if node not in self:
            return False

        self.current_node = node
        return True

    # Visualizzazione Albero
    def print_tree(self):
        for pre, fill, node in RenderTree(self.__root):
            if self.current_node.id == node._id:
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


def add_exec_inorder(ctx, tree: ExTree, new_snapshot):
    sorted_child = get_current_sorted_child(ctx, tree.current_node.snapshot.marking)
    idx_child = sorted_child.index(new_snapshot.marking)
    tree.add_snapshot(new_snapshot)

    return idx_child


def get_current_sorted_child(ctx: NetContext, marking) -> list[T]:
    net = ctx.net
    curr_time_marking = marking
    exec_strategy = ctx.strategy

    choices = exec_strategy.get_choices(net, curr_time_marking)
    m = [choices[choice] for choice in choices]
    perms = itertools.product(*m)
    key_to_time_marking = {}

    for perm in perms:
        temp, *_ = exec_strategy.consume(net, curr_time_marking, perm)
        key_of_time_marking = []
        for k in sorted(temp.keys()):
            token, age = temp[k]
            if token == 0:
                key_of_time_marking.append(-1)
            else:
                key_of_time_marking.append(age)

        key_to_time_marking.update({tuple(key_of_time_marking): temp})

    children = []
    for key_row in sorted(list(key_to_time_marking.keys())):
        children.append(key_to_time_marking[key_row])

    return children
