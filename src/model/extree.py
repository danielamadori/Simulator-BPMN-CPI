import logging
from typing import Iterator

from anytree import Node, PreOrderIter, RenderTree, findall_by_attr, findall

from strategy.execution import add_impacts
from utils.net_utils import NetUtils, get_default_impacts, is_final_marking
from .petri_net.time_spin import TimeMarking
from .snapshot import Snapshot

logger = logging.getLogger(__name__)


def serial_generator(initial: int = 1):
    """Generates a unique serial number each time it is called."""
    n = initial
    while True:
        yield n
        n += 1


class ExTree:
    """
    ExTree is a tree structure for managing and traversing snapshots of Petri net markings.

    Attributes:
        current_node (Node): The current node in the tree.
        __root (Node): The root node of the tree.
        __id_generator (Iterator[int]): Iterator for generating unique node IDs.
    """
    __separator = '/'
    current_node: Node
    __root: Node
    __id_generator: Iterator[int]

    # Struttura Node: name[facoltativo],id,snapshot[oggetto di interesse]
    def __init__(self, root: Snapshot | Node, generator: Iterator[int] = None):
        self.__id_generator = generator or serial_generator()
        logger.info("Inizializzazione ExTree")
        if root is None:
            logger.error("Lo Snapshot Root è None")
            raise ValueError("Root Snapshot can't be None")

        if isinstance(root, Node):
            self.__root = root
            self.current_node = root
            if generator is None:
                max_id = -1
                for node in PreOrderIter(root):
                    max_id = max(max_id, int(node.id))

                self.__id_generator = serial_generator(max_id + 1)
            return

        _root = Node(name="Root", id='0', snapshot=root)
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

        # Final marking check
        if is_final_marking(ctx, self.current_node.snapshot.marking):
            return self.current_node

        # If exists a node with the same marking under the current parent, return that node
        for node in self:
            if node.parent == parent and node.snapshot.marking == snapshot.marking:
                return node

        parent_probability = parent.snapshot.probability if parent is not None else 1
        parent_impacts = parent.snapshot.impacts if parent is not None else get_default_impacts(ctx.net)
        parent_time = parent.snapshot.execution_time if parent is not None else 0

        _id = next(self.__id_generator)

        cumulative_snapshot = Snapshot(marking=snapshot.marking, probability=parent_probability * snapshot.probability,
                                       impacts=add_impacts(parent_impacts, snapshot.impacts),
                                       time=parent_time + snapshot.execution_time)

        child_node = Node(name=str(_id), id=str(_id), snapshot=cumulative_snapshot, parent=parent)

        if set_as_current:
            self.current_node = child_node

        return child_node

    def set_current(self, node: Node | str):
        if isinstance(node, str):
            node = self.get_node_by_id(node)

        if node is None or node not in self:
            return False

        self.current_node = self.get_node_by_id(node.id)
        return True

    # Visualizzazione Albero
    def print_tree(self):
        for pre, fill, node in RenderTree(self.__root):
            if self.current_node.id == node.id:
                print("X" + f"{pre}{node.name}" + "X")
            else:
                print(f"{pre}{node.name}")

    def search_nodes_by_marking(self, marking: TimeMarking) -> list[Node]:
        """
        Search for nodes that match the given marking in the execution tree.
        :param marking: The marking to search for. Can be partial or complete.
        :return: The list of nodes with the matching marking.
        """

        def check_marking(node: Node):
            valid = True
            __marking = node.snapshot.marking
            for key in __marking.keys() | marking.keys():
                token, age, _ = marking[key]['token'], marking[key]['age'], marking[key]['time']
                other_token, other_age, _ = __marking[key]['token'], __marking[key]['age'], __marking[key]['time']
                if token != other_token or age != other_age:
                    valid = False
                    break

            return valid

        return list(findall(self.root, check_marking))

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
