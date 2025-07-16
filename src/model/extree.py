import logging
from typing import Iterator

from anytree import Node, PreOrderIter, RenderTree, findall_by_attr

from utils.net_utils import NetUtils
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
        for node in self:
            if node.parent == parent and node.snapshot.marking == snapshot.marking:
                return node

        _id = next(self.__id_generator)

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

        self.current_node = self.get_node_by_id(node.id)
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
