import uuid
from anytree import Node, PreOrderIter, RenderTree
from .snapshot import Snapshot


class ExTree:
    current_node_id: str
    root: Node

    # Struttura Node: name[facoltativo],id,snapshot[oggetto di interesse]
    def __init__(self, root: Snapshot):
        self.root = Node(name="Root", id=str(uuid.uuid4()), snapshot=root)
        self.current_node_id = self.root.id

    def find_by_id(self, node_id: str):
        for node in PreOrderIter(self.root):
            if node.id == node_id:
                return node
        return None

    # Costruzione dell'albero
    def add_node(self, snapshot: Snapshot):
        parent = self.find_by_id(self.current_node_id)
        if not parent:
            raise ValueError(f"Nessun nodo trovato con id: {self.current_node_id}")

        child_node = Node(
            name=str(snapshot), id=str(uuid.uuid4()), snapshot=snapshot, parent=parent
        )
        self.current_node_id = child_node.id

    # Visualizzazione Albero
    def print_tree(self):
        for pre, fill, node in RenderTree(self.root):
            if self.current_node_id == node.id:
                print("X" + f"{pre}{node.name}" + "X")
            else:
                print(f"{pre}{node.name}")

    def __repr__(self):
        return self.print_tree()

    def __str__(self):
        return repr(self)
