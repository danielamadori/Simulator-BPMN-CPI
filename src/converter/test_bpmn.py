from __future__ import annotations
from pydantic import BaseModel
from typing import List, Dict, Set
from enum import Enum


class RegionType(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    NATURE = "nature"
    CHOICE = "choice"
    TASK = "task"


class Task(BaseModel):
    id: str
    type: RegionType
    label: str
    impacts: List[float]
    duration: float


class Region(BaseModel):
    id: str
    type: RegionType
    label: str | None = None
    children: List[Region | Task]
    distribution: List[float] | None = None


class IOTag:

    def __init__(self, name, properties):
        self.name = name
        self.properties = properties
        self.incoming = []
        self.outgoing = []

    def add_incoming(self, flow):
        self.incoming.append(flow)

    def add_outgoing(self, flow):
        self.outgoing.append(flow)

    def __repr__(self):
        result = f"<bpmn:"
        return result


class Flow:

    def __init__(self, id, srcId, targetId):
        self.id = id
        self.srcId = srcId
        self.targetId = targetId

    def __hash__(self):
        return self.id

    def get_id(self):
        return self.id


dizzionario: Dict[str, IOTag] = {}
flows: Set[Flow] = set()


def translate(region: Region | Task):
    if isinstance(region, Task):
        # Creiamo il tag e ritorniamo l'id
        # Aggiungo il tag associato all'id nel dizionario
        entry_properties = {"id": region.id, "name": region.label}
        tag = IOTag(name=region.type, properties=entry_properties)
        dizzionario[region.id] = tag
        return [region.id, region.id]

    # type(json) == Region

    if region.type == RegionType.SEQUENTIAL:
        prev_id = None
        first_entry = None
        for child in region.children:
            entry, exit = translate(child)
            if not first_entry:
                first_entry = entry
            if prev_id:
                flow_exit = Flow(f"ex_flow_{prev_id}", prev_id, entry)
                dizzionario[prev_id].add_outgoing(flow_exit)
                dizzionario[entry].add_incoming(flow_exit)
                flows.add(flow_exit)

            prev_id = exit

        return [first_entry, prev_id]

    # choice, nature, parallel
    name = (
        "bpmn:exclusiveGateway"
        if region.type in [RegionType.NATURE, RegionType.CHOICE]
        else "bpmn:parallelGateway"
    )

    entry_tag_id = f"entry_{region.id}"
    exit_tag_id = f"exit_{region.id}"

    entry_properties = {
        "id": entry_tag_id,
        "name": region.label or "",
        "gatewayDirection": "Diverging",
    }

    exit_properties = {
        "id": exit_tag_id,
        "name": region.label or "",
        "gatewayDirection": "Converging",
    }

    entry_tag = IOTag(name=name, properties=entry_properties)
    exit_tag = IOTag(name=name, properties=exit_properties)
    dizzionario[entry_tag_id] = entry_tag
    dizzionario[exit_tag_id] = exit_tag

    for child in region.children:
        entry, exit = translate(child)
        entry_flow = Flow(f"{entry_tag_id}_to_{entry}", entry_tag_id, entry)
        exit_flow = Flow(f"{exit}_to_{exit_tag_id}", exit, exit_tag_id)

        flows.add(entry_flow)
        flows.add(exit_flow)

        dizzionario[entry_tag_id].add_outgoing(entry_flow)
        dizzionario[entry].add_incoming(entry_flow)
        dizzionario[exit].add_outgoing(exit_flow)
        dizzionario[exit_tag_id].add_incoming(exit_flow)

    return [entry_tag_id, exit_tag_id]
