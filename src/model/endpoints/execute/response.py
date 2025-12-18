from __future__ import annotations

from typing import TYPE_CHECKING

from anytree.exporter import DictExporter
from pydantic import BaseModel

from model.endpoints.execute.request import PetriNetModel, ExecutionTreeModel
from model.region import RegionModel
from utils import logging_utils

if TYPE_CHECKING:
    from model.types import RegionModelType, PetriNetType, MarkingType, ExTreeType, SnapshotType

logger = logging_utils.get_logger(__name__)


class ExecuteResponse(BaseModel):
    """
    Represents the response structure for an execution request.
    """
    bpmn: RegionModel
    petri_net: PetriNetModel
    petri_net_dot: str | None = None
    execution_tree: ExecutionTreeModel


def create_response(region: RegionModelType, petri_net: PetriNetType, im: MarkingType, fm: MarkingType,
                    extree: ExTreeType) -> ExecuteResponse:
    """
    Creates a response object containing the BPMN region, Petri net model, and execution tree.
    """
    logger.debug("Creating response")
    petri_net_model = petri_net_to_model(petri_net, im, fm)
    execution_tree_model = extree_to_model(extree)

    return ExecuteResponse(bpmn=region, petri_net=petri_net_model,
                           petri_net_dot=petri_net_to_dot(petri_net, extree.current_node.snapshot.marking, fm.tokens),
                           execution_tree=execution_tree_model)


def petri_net_to_model(petri_net: PetriNetType, im: MarkingType, fm: MarkingType) -> PetriNetModel:
    logger.debug("Creating petri net response model")
    transitions = []
    for t in petri_net.transitions:
        obj = PetriNetModel.TransitionModel(id=t.name,
                                            label=t.region_label,
                                            region_id=t.region_id,
                                            region_type=t.region_type,
                                            probability=t.probability,
                                            stop=t.stop
                                            )
        transitions.append(obj)

    places = []
    for p in petri_net.places:
        obj = PetriNetModel.PlaceModel(id=p.name,
                                       label=p.region_label,
                                       region_type=p.region_type,
                                       entry_region_id=p.entry_id,
                                       exit_region_id=p.exit_id,
                                       duration=p.duration,
                                       impacts=p.impacts,
                                       visit_limit=p.visit_limit)
        places.append(obj)

    arcs = []
    for a in petri_net.arcs:
        obj = PetriNetModel.ArcModel(source=a.source.name, target=a.target.name, weight=a.weight)
        arcs.append(obj)

    model_im = marking_to_model(im)
    model_fm = marking_to_model(fm)

    return PetriNetModel(name=petri_net.name, transitions=transitions, places=places, arcs=arcs,
                         initial_marking=model_im, final_marking=model_fm)


def petri_net_to_dot(petri_net: PetriNetType, im: MarkingType, fm: MarkingType) -> str:
    """
    Converts a Petri net to its DOT representation.
    """
    logger.debug("Converting Petri net model to DOT representation")

    from pm4py.visualization.petri_net import visualizer as pn_visualizer

    marking = {}
    for place in im.keys():
        token, age, visit_count = im[place]
        marking[place] = (token, age, visit_count)
    gviz = pn_visualizer.apply(petri_net, marking, fm)
    try:
        dot_string = gviz.pipe(format="dot").decode()
    except Exception as exc:  # pragma: no cover - fallback for environments without Graphviz binaries
        logger.warning("Falling back to raw DOT source: %s", exc)
        dot_string = getattr(gviz, "source", "")

    return dot_string


def marking_to_model(marking: MarkingType) -> dict[str, dict[str, float]]:
    """
    Converts a marking to a model representation.
    """
    logger.debug("Converting marking to model representation")
    result = {}
    for place in marking.keys():
        result[place.name] = {
            "token": marking[place].token,
            "age": marking[place].age,
            "visit_count": marking[place].visit_count
        }
    return result


def extree_to_model(extree: ExTreeType) -> ExecutionTreeModel:
    """
    Converts an execution tree to a model representation.
    """
    logger.debug("Converting execution tree to model representation")
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


def snapshot_to_model(snapshot: SnapshotType) -> ExecutionTreeModel.NodeModel.SnapshotModel:
    """
    Converts a snapshot to a model representation.
    """
    logger.debug("Converting snapshot to model representation")
    return ExecutionTreeModel.NodeModel.SnapshotModel(marking=marking_to_model(snapshot.marking),
                                                      probability=snapshot.probability,
                                                      impacts=snapshot.impacts,
                                                      execution_time=snapshot.execution_time,
                                                      status=snapshot.status,
                                                      decisions=snapshot.decisions,
                                                      choices=snapshot.choices
                                                      )
