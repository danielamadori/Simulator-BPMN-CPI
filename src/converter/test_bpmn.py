from __future__ import annotations
from pydantic import BaseModel
from typing import List, Dict, Set, Tuple
from enum import Enum
import uuid


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
        self.incoming: List[Flow] = []
        self.outgoing: List[Flow] = []

    def add_incoming(self, flow: Flow):
        self.incoming.append(flow)

    def add_outgoing(self, flow: Flow):
        self.outgoing.append(flow)

    def __repr__(self):
        dict_to_list = list(self.properties.items())
        attributes = [f'{x[0]}="{x[1]}"' for x in dict_to_list]
        result = f"<{self.name} {" ".join(attributes)}>"

        incoming_tag = [
            f"<bpmn:incoming>{flow.id}</bpmn:incoming>" for flow in self.incoming
        ]
        outgoing_tag = [
            f"<bpmn:outgoing>{flow.id}</bpmn:outgoing>" for flow in self.outgoing
        ]

        result += "\n".join(incoming_tag) + "\n"
        result += "\n".join(outgoing_tag) + "\n"

        result += f"</{self.name}>"

        return result

    def __str__(self):
        return repr(self)


class Flow:

    def __init__(self, id, srcId, targetId):
        self.id = id
        self.srcId = srcId
        self.targetId = targetId

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f'<bpmn:sequenceFlow id="{self.id}" name="" sourceRef="{self.srcId}" targetRef="{self.targetId}" />'

    def __str__(self):
        return repr(self)

    def get_id(self):
        return self.id


dizzionario: Dict[str, IOTag] = {}
flows: Set[Flow] = set()


def region_to_bpmn(region: Region, process_id: int = uuid.uuid4().int) -> str:
    """
    Ritorna la conversione della regione come stringa ne formato XML seguendo lo standard BPMN 2.0

    Args:
        region (Region): regione da dover convertire in bpmn
        process_id (int, optional): id del tag di processo. Default to uuid4.

    Returns:
        str: stringa della regione convertita
    """

    # Intestazione BPMN 2.0 XML
    result = '<?xml version="1.0" encoding="utf-8"?><bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:omgdc="http://www.omg.org/spec/DD/20100524/DC" xmlns:omgdi="http://www.omg.org/spec/DD/20100524/DI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" targetNamespace="http://www.signavio.com/bpmn20" typeLanguage="http://www.w3.org/2001/XMLSchema" expressionLanguage="http://www.w3.org/1999/XPath">'

    # Descrizione del processo BPMN
    result += f'<bpmn:process id="{process_id}" isClosed="false" isExecutable="false" processType="None">'
    tags, flows = get_inner_process_tags(region)
    result += "".join([str(tag) for tag in tags])
    result += "".join([str(flow) for flow in flows])
    result += "</bpmn:process>"

    result += "</bpmn:definitions>"

    return result


# isInterrupting, name, parallelMultiple
def get_inner_process_tags(region: Region) -> Tuple[List[IOTag], List[Flow]]:
    """
    Metodo wrapper per la funzione _translate(region).
    Vengono creati il tag di inizio, il tag di fine e i flow per collegare i tag delle varie regioni.
    Ritorna una tupla di due liste, dove nella prima sono presenti tutti i tag creati durante la conversione,
    mentre nella seconda tutti i flow creati durante la conversione.

    Args:
        region: regione da convertire

    Returns:
        (list[IOTag], list[Flow]): tag e flow creati
    """

    start_properties = {
        "id": "start",
        "isInterrupting": "false",
        "name": "startEvent",
        "parallelMultiple": "false",
    }
    end_properties = {
        "id": "end",
        "name": "endEvent",
    }

    start_event = IOTag("bpmn:startEvent", start_properties)
    end_event = IOTag("bpmn:endEvent", end_properties)

    dizzionario[start_properties["id"]] = start_event
    dizzionario[end_properties["id"]] = end_event

    # Start Event viene eseguito nel ciclo
    prev_id = start_properties["id"]
    for child in region.children:
        entry, exit = _translate(child)
        flow_exit = Flow(f"ex_flow_{prev_id}", prev_id, entry)
        dizzionario[prev_id].add_outgoing(flow_exit)
        dizzionario[entry].add_incoming(flow_exit)
        flows.add(flow_exit)

        prev_id = exit

    # End Event
    tmp_flow = Flow(f"ex_flow_{prev_id}", prev_id, end_event)
    flows.add(tmp_flow)
    dizzionario[prev_id].add_outgoing(tmp_flow)
    dizzionario[end_properties["id"]].add_incoming(tmp_flow)

    return (list(dizzionario.values()), list(flows))


def _translate(region: Region | Task) -> Tuple[int, int]:
    """
    Serve per convertire le regioni in file XML utilizzanod il formato BPMN 2.0
    Visita ricorsivamnete l'albero aggiungendo i vari tag a dizzionario
    e creando i flow che collegano le regioni aggiungendole al set flows.
    Ritorna una tupla con due id. Il primo indica l'id del primo tag della regione,
    mentre il secondo indica l'id dell'ultimo tag della regione.

    Args:
        region (Region | Task): regione da convertire

    Returns:
        (int, int): id entrata e id di uscita
    """

    if isinstance(region, Task):
        # Creiamo il tag e ritorniamo l'id
        # Aggiungo il tag associato all'id nel dizionario
        entry_properties = {"id": region.id, "name": region.label}
        tag = IOTag("bpmn:task", properties=entry_properties)
        dizzionario[region.id] = tag
        return (region.id, region.id)

    # type(json) == Region

    if region.type == RegionType.SEQUENTIAL:
        prev_id = None
        first_entry = None
        for child in region.children:
            entry, exit = _translate(child)
            if not first_entry:
                first_entry = entry
            if prev_id:
                flow_exit = Flow(f"ex_flow_{prev_id}", prev_id, entry)
                dizzionario[prev_id].add_outgoing(flow_exit)
                dizzionario[entry].add_incoming(flow_exit)
                flows.add(flow_exit)

            prev_id = exit

        return (first_entry, prev_id)

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
        entry, exit = _translate(child)
        entry_flow = Flow(f"{entry_tag_id}_to_{entry}", entry_tag_id, entry)
        exit_flow = Flow(f"{exit}_to_{exit_tag_id}", exit, exit_tag_id)

        flows.add(entry_flow)
        flows.add(exit_flow)

        dizzionario[entry_tag_id].add_outgoing(entry_flow)
        dizzionario[entry].add_incoming(entry_flow)
        dizzionario[exit].add_outgoing(exit_flow)
        dizzionario[exit_tag_id].add_incoming(exit_flow)

    return (entry_tag_id, exit_tag_id)
