from anytree.exporter import DictExporter
from pm4py import PetriNet
from pydantic import BaseModel

from model.endpoints.execute.request import PetriNetModel, ExecutionTreeModel
from model.extree import ExTree
from model.region import RegionModel
from model.snapshot import Snapshot
from model.time_spin import TimeMarking
from utils.net_utils import NetUtils


class ExecuteResponse(BaseModel):
    """
    Represents the response structure for an execution request.
    """
    bpmn: RegionModel
    petri_net: PetriNetModel
    petri_net_dot: str | None = None
    execution_tree: ExecutionTreeModel


def create_response(region: RegionModel, petri_net: PetriNet, im: TimeMarking, fm: TimeMarking, extree: ExTree) -> ExecuteResponse:
    """
    Creates a response object containing the BPMN region, Petri net model, and execution tree.
    """
    petri_net_model = petri_net_to_model(petri_net, im, fm)
    execution_tree_model = extree_to_model(extree)

    return ExecuteResponse(bpmn=region, petri_net=petri_net_model, petri_net_dot=petri_net_to_dot(petri_net, im, fm),execution_tree=execution_tree_model)

def petri_net_to_model(petri_net: PetriNet, im, fm) -> PetriNetModel:
    transitions = []
    for t in petri_net.transitions:
        obj = PetriNetModel.TransitionModel(id=t.name,
                                            label=NetUtils.get_label(t),
                                            region_id=NetUtils.Transition.get_region_id(t),
                                            region_type=NetUtils.get_type(t),
                                            probability=NetUtils.Transition.get_probability(t),
                                            stop=NetUtils.Transition.get_stop(t)
                                            )
        transitions.append(obj)

    places = []
    for p in petri_net.places:
        obj = PetriNetModel.PlaceModel(id=p.name,
                                       label=NetUtils.get_label(p),
                                       region_type=NetUtils.get_type(p),
                                       entry_region_id=NetUtils.Place.get_entry_id(p),
                                       exit_region_id=NetUtils.Place.get_exit_id(p),
                                       duration=NetUtils.Place.get_duration(p),
                                       impacts=NetUtils.Place.get_impacts(p))
        places.append(obj)

    arcs = []
    for a in petri_net.arcs:
        obj = PetriNetModel.ArcModel(source=a.source.name, target=a.target.name, weight=a.weight)
        arcs.append(obj)

    model_im = marking_to_model(im)
    model_fm = marking_to_model(fm)

    return PetriNetModel(name=petri_net.name, transitions=transitions, places=places, arcs=arcs, initial_marking=model_im, final_marking=model_fm)

def petri_net_to_dot(petri_net: PetriNet, im, fm) -> str:
    """
    Converts a Petri net to its DOT representation.
    """
    from pm4py.visualization.petri_net import visualizer as pn_visualizer
    gviz = pn_visualizer.apply(petri_net, im, fm)
    dot_string = gviz.pipe(format="dot").decode()

    return dot_string

def marking_to_model(marking: TimeMarking) -> dict[str, dict[str, float]]:
    """
    Converts a marking to a model representation.
    """
    return {place.name: {"token": marking.marking.get(place, 0), "age": marking.age.get(place, 0.0)} for place in marking.keys()}

def extree_to_model(extree: ExTree) -> ExecutionTreeModel:
    """
    Converts an execution tree to a model representation.
    """
    def attriter(attrs):
        result = []
        for k, v in attrs:
            if k == 'snapshot':
                result.append((k, snapshot_to_model(v)))
            else:
                result.append((k, v))

        return result

    exporter = DictExporter(attriter=attriter)
    nodes_dict = exporter.export(extree.root)
    current_node = extree.current_node.id
    root = ExecutionTreeModel.NodeModel.model_validate(nodes_dict)

    return ExecutionTreeModel(root=root, current_node=current_node)


def snapshot_to_model(snapshot: Snapshot) -> ExecutionTreeModel.NodeModel.SnapshotModel:
        """
        Converts a snapshot to a model representation.
        """
        return ExecutionTreeModel.NodeModel.SnapshotModel(marking=marking_to_model(snapshot.marking),
                                                          probability=snapshot.probability,
                                                          impacts=snapshot.impacts,
                                                          execution_time=snapshot.execution_time)