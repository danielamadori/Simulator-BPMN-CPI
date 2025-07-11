import itertools
import logging
from copy import copy

from anytree import Node, PreOrderIter, RenderTree, findall_by_attr

from utils.net_utils import NetUtils
from .context import NetContext
from .snapshot import Snapshot
from .types import T, M

logger = logging.getLogger(__name__)

def serial_generator():
    """Generates a unique serial number each time it is called."""
    n = 0
    while True:
        yield n
        n += 1

id_generator = serial_generator()

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
    def add_snapshot(self, ctx, snapshot: Snapshot, user_choices: list[T], set_as_current: bool = True):
        parent = self.current_node
        for node in self:
            if node.parent == parent and node.snapshot.marking == snapshot.marking:
                return node

        # idx = get_sorted_id(ctx, self.current_node.snapshot.marking, user_choices)
        # _id = "{}{}{}".format(parent.name, ExTree.__separator, idx)

        _id = next(id_generator)

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


def get_sorted_id(ctx, current_marking: M, choices: list[T]):
    """
    Returns the index of the new marking in the sorted list of children of the current node.
    This function assumes that the children are sorted based on the active places name in marking.
    :param ctx:
    :param current_marking:
    :param choices:
    :return:
    """
    sorted_child = get_current_sorted_children(ctx, current_marking)

    # Fire the choices to get the new marking
    new_marking = copy(current_marking)
    for t in choices:
        new_marking = ctx.semantic.fire(ctx.net, t, new_marking)

    idx_child = sorted_child.index(new_marking)

    if idx_child == -1:
        raise ValueError("The new snapshot can't be reached from the current node")

    return idx_child


def get_current_sorted_children(ctx: NetContext, marking) -> list[M]:
    """
    Returns the sorted list of children for the current node based on the current marking.
    The children are sorted based on the active places name in the marking.
    :param ctx:
    :param marking:
    :return:
    """
    curr_time_marking = marking

    # transition_permutations = itertools.permutations(ctx.semantic.enabled_transitions(ctx.net, marking))
    transition_group_by_in_place = itertools.groupby(ctx.semantic.enabled_transitions(ctx.net, marking), key=lambda t: list(t.in_arcs)[0].source)
    transition_groups = [tuple(group) for key, group in transition_group_by_in_place]
    transition_combinations = list(itertools.product(*transition_groups))
    key_to_time_marking = {}

    # For each combination of transitions, we fire them and get the new marking
    for combination in transition_combinations:
        key_of_time_marking = [t.name for t in combination if t is not None]
        key_of_time_marking.sort()

        # Fire all transitions in the combination to get the new marking
        temp = copy(curr_time_marking)
        for t in combination:
            if t is not None:
                temp = ctx.semantic.execute(ctx.net, t, temp)

        key_to_time_marking.update({tuple(key_of_time_marking): temp})

    children = []
    for key_row in sorted(list(key_to_time_marking.keys())):
        children.append(key_to_time_marking[key_row])

    return children
