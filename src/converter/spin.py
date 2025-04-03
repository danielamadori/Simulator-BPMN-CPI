from typing import Type
from pm4py.objects.petri_net.obj import PetriNet
from model.region import RegionModel, RegionType
from uuid import uuid4
from collections import Counter

places = set()
transitions = set()
arcs = set()


def create_pnml_from_region(region: RegionModel):
    header = '<?xml version="1.0" encoding="ISO-8859-1"?><pnml><net id="net1" type="http://www.pnml.org/version-2009/grammar/pnmlcoremodel"><name><text>Petri net</text></name><page id="n0">'

    initial_tag_id = uuid4()
    body = create_place_tag(initial_tag_id)
    _body, exit_id = from_json(region, initial_tag_id)
    body += _body

    footer = "</page><finalmarkings><marking>"

    for id in places:
        footer += (
            f'<place idref="{id}"><text>{0 if id != exit_id else 1}</text></place>'
        )

    footer += "</marking></finalmarkings></net></pnml>"

    return header + body + footer


def create_place_tag(id, label="", isInitial=False):
    initialMarking = ""
    if isInitial:
        initialMarking = "<initialMarking><text>1</text></initialMarking>"

    places.add(id)
    return f'<place id="{id}"><name><text>{label or ""}</text></name>{initialMarking}</place>'


def create_transition_tag(id, label=""):
    label = f"{id} LABEL"
    return f'<transition id="{id}"><name><text>{label or ""}</text></name></transition>'


def create_arc_tag(id, source_id, target_id, label=""):
    return f'<arc id="{id}" source="{source_id}" target="{target_id}"><name><text>{label or ""}</text></name></arc>'


def create_task_tag(source_id, task: RegionModel):
    entry_id = source_id
    exit_id = f"{task.id}_exit"
    trans_id = task.id

    entry_place = ""
    if not entry_id:
        entry_place = create_place_tag(entry_id, task.label)
    # places.add(entry_place)

    arc1 = create_arc_tag(uuid4(), entry_id, trans_id)
    # arcs.add(arc1)

    trans = create_transition_tag(trans_id, task.label)
    # transitions.add(trans)

    arc2 = create_arc_tag(uuid4(), trans_id, exit_id)

    exit_place = create_place_tag(exit_id, task.label)
    # places.add(exit_place)

    return [entry_place + arc1 + trans + arc2 + exit_place, exit_id]


def from_json(region: RegionModel, source_id=None):
    if region.type == RegionType.TASK:
        source_id = source_id or f"{region.id}_entry"
        tag, exit_place_id = create_task_tag(source_id, region)

        return [tag, exit_place_id]
    elif region.type == RegionType.SEQUENTIAL:
        tag = ""
        prev_exit_id = source_id
        first_entry_id = source_id

        for child in region.children:
            _tag, child_exit_id = from_json(child, source_id)
            tag += _tag
            if not first_entry_id:
                first_entry_id = f"{region.id}_entry"
                prev_exit_id = child_exit_id
                continue

            tag += create_arc_tag(uuid4(), prev_exit_id, first_entry_id)
            prev_exit_id = child_exit_id
            source_id = prev_exit_id

        return [tag, prev_exit_id]
    elif region.type == RegionType.PARALLEL:
        tag = ""

        # Place di entrata
        if not source_id:
            source_id = f"{region.id}_entry"
            tag += create_place_tag(source_id)

        _tag, exit_id = create_parallel_tag(region, source_id)
        return [tag + _tag, exit_id]
    else:
        tag = ""

        if not source_id:
            source_id = f"{region.id}_entry"
            tag += create_place_tag(source_id)

        _tag, exit_id = create_split(region, source_id)
        tag += _tag

        return [tag, exit_id]


def create_split(region, source_id):
    tag = ""
    exit_id = f"{region.id}_exit"
    tag += create_place_tag(exit_id)

    for i in range(len(region.children)):
        child = region.children[i]

        child_source_id = f"{child.id}_entry"
        tag += create_place_tag(child_source_id)

        trans_entry_child_id = f"{region.id}_child{child.id}"
        tag += create_transition_tag(trans_entry_child_id)

        tag += create_arc_tag(uuid4(), source_id, trans_entry_child_id)
        tag += create_arc_tag(uuid4(), trans_entry_child_id, child_source_id)

        _tag, child_exit_id = from_json(child, child_source_id)
        tag += _tag

        trans_exit_child_id = uuid4()
        tag += create_transition_tag(trans_exit_child_id)

        tag += create_arc_tag(uuid4(), child_exit_id, trans_exit_child_id)
        tag += create_arc_tag(uuid4(), trans_exit_child_id, exit_id)

    return [tag, exit_id]


def create_parallel_tag(region, source_id):
    tag = ""
    # Transizione in entrata
    entry_trans_id = region.id
    tag += create_transition_tag(region.id)

    # Arco che collega place e transizione in entrata
    tag += create_arc_tag(uuid4(), source_id, entry_trans_id)

    # Place di uscita dlla regione
    exit_place_id = f"{region.id}_exit"
    tag += create_place_tag(exit_place_id)

    # Transizione in uscita
    exit_trans_id = uuid4()
    tag += create_transition_tag(exit_trans_id)

    # Arco che collega la transizione di uscita e il place di uscita
    tag += create_arc_tag(uuid4(), exit_trans_id, exit_place_id)

    for child in region.children:
        source_child_id = f"{child.id}_entry"

        tag += create_place_tag(source_child_id)
        tag += create_arc_tag(uuid4(), entry_trans_id, source_child_id)

        _tag, child_exit_id = from_json(child, source_child_id)
        tag += _tag

        tag += create_arc_tag(uuid4(), child_exit_id, exit_trans_id)

    return [tag, exit_place_id]


class TimeBasedSPIN:

    def __init__(self, pn: Type[PetriNet], info: dict):
        self.pn = pn

        for t in pn.__get_transitions():
            id = t.name
