import logging
from typing import List

from pm4py.objects.petri_net.obj import Marking

from converter.validator import region_validator
from model.petri_net.wrapper import WrapperPetriNet, add_arc_from_to
from model.region import RegionModel, RegionType
from model.petri_net.time_spin import TimeMarking
from utils.exceptions import ValidationError
from utils.net_utils import PropertiesKeys

logger = logging.getLogger(__name__)


# # id
# class IDGenerator:
#     counter = 0
#
#     @classmethod
#     def next_id(cls):
#         cls.counter += 1
#         return f"{cls.counter}"

def serial_generator():
    """Generates a unique ID for each call."""
    counter = 0
    while True:
        yield counter
        counter += 1


class RegionProp:
    def __init__(
            self,
            region_id: str,
            label: str | None,
            duration: float,
            impacts: List[float] | None,
            _type: RegionType,
            distribution: List[float] | None,
    ):
        self.region_id = region_id
        self.label = label
        self.duration = duration
        self.impacts = impacts
        self.type = _type
        self.distribution = distribution


def get_place_prop(place: WrapperPetriNet.Place):
    return place.properties


def get_trans_prop(trans: WrapperPetriNet.Transition):
    return trans.properties


def create_place(place_id: str, region: RegionModel):
    place = WrapperPetriNet.Place(
        place_id,
    )

    place.properties.update(create_prop(region))

    return place


def create_prop(region: RegionModel):
    prop = {PropertiesKeys.ENTRY_RID: region.id, PropertiesKeys.EXIT_RID: None, PropertiesKeys.LABEL: region.label,
            PropertiesKeys.TYPE: region.type, PropertiesKeys.DURATION: region.duration,
            PropertiesKeys.IMPACTS: region.impacts}

    return prop


def create_transition(
        trans_id: str, region: RegionModel, probability: float = 1, stop: bool = False
):
    trans = WrapperPetriNet.Transition(trans_id, label=region.label)

    trans.properties[PropertiesKeys.ENTRY_RID] = region.id
    trans.properties[PropertiesKeys.EXIT_RID] = None
    trans.properties[PropertiesKeys.LABEL] = region.label
    trans.properties[PropertiesKeys.TYPE] = region.type
    trans.properties[PropertiesKeys.PROBABILITY] = probability
    trans.properties[PropertiesKeys.STOP] = stop

    return trans


def from_region(region: RegionModel):
    if not region_validator(region):
        logger.error("Lancio eccezzione perchè i dati forniti non sono validi")
        raise ValidationError()
    else:
        logger.info("Validazione avvenuta con successo")

    net = WrapperPetriNet()
    id_generator = serial_generator()
    def rec(region: RegionModel, source: WrapperPetriNet.Place | None = None):
        if region.is_task():
            # Task
            # Entry Place
            logger.debug(f"Task\tRegion: {region.id}")
            if not source:
                entry_task_id = str(next(id_generator))
                entry_place = create_place(entry_task_id, region)
                net.places.add(entry_place)
            else:
                entry_place = source
                _tmp_id = source.properties[PropertiesKeys.EXIT_RID]
                entry_place.properties.update(create_prop(region))
                entry_place.properties.update({PropertiesKeys.EXIT_RID: _tmp_id})

            # Exit place
            exit_task_id = str(next(id_generator))
            exit_place = create_place(exit_task_id, region)
            exit_place.properties.update(
                {
                    PropertiesKeys.ENTRY_RID: None,
                    PropertiesKeys.EXIT_RID: exit_place.properties[
                        PropertiesKeys.ENTRY_RID
                    ],
                    PropertiesKeys.DURATION: 0,
                    PropertiesKeys.IMPACTS: None,
                }
            )
            net.places.add(exit_place)

            # Transition
            trans_id = str(next(id_generator))
            trans = create_transition(trans_id, region)
            net.transitions.add(trans)

            # Arcs
            add_arc_from_to(entry_place, trans, net)
            add_arc_from_to(trans, exit_place, net)

            return entry_place, exit_place

        elif region.is_parallel():
            # Parallel Gateway
            # Entry Place
            logger.debug(f"Parallel\tRegion: {region.id}")
            if not source:
                entry_task_id = str(next(id_generator))
                entry_place = create_place(entry_task_id, region)
                net.places.add(entry_place)
            else:
                entry_place = source
                _tmp_id = source.properties[PropertiesKeys.EXIT_RID]
                entry_place.properties.update(create_prop(region))
                entry_place.properties.update({PropertiesKeys.EXIT_RID: _tmp_id})

            # Exit place
            exit_task_id = str(next(id_generator))
            exit_place = create_place(exit_task_id, region)
            exit_place.properties.update(
                {
                    PropertiesKeys.ENTRY_RID: None,
                    PropertiesKeys.EXIT_RID: exit_place.properties[
                        PropertiesKeys.ENTRY_RID
                    ],
                    PropertiesKeys.DURATION: 0,
                }
            )
            net.places.add(exit_place)

            # Entry transition
            entry_trans_id = str(next(id_generator))
            entry_trans = create_transition(entry_trans_id, region)
            net.transitions.add(entry_trans)

            # Exit Transition
            exit_trans_id = str(next(id_generator))
            exit_trans = create_transition(exit_trans_id, region)
            net.transitions.add(exit_trans)

            # Add entry and exit arc
            add_arc_from_to(entry_place, entry_trans, net)
            add_arc_from_to(exit_trans, exit_place, net)

            for child in region.children:
                child_entry, child_exit = rec(child)
                add_arc_from_to(entry_trans, child_entry, net)
                add_arc_from_to(child_exit, exit_trans, net)

            return entry_place, exit_place
        elif region.is_sequential():
            logger.debug(f"Sequential\tRegion: {region.id}")
            if not source:
                entry_task_id = str(next(id_generator))
                entry_place = create_place(entry_task_id, region)
                net.places.add(entry_place)
            else:
                entry_place = source
                _tmp_id = source.properties[PropertiesKeys.EXIT_RID]
                entry_place.properties.update(create_prop(region))
                entry_place.properties.update({PropertiesKeys.EXIT_RID: _tmp_id})

            prev_child = entry_place

            for child in region.children:
                child_entry, child_exit = rec(child, prev_child)
                prev_child = child_exit

            return entry_place, prev_child
        elif region.is_choice() or region.is_nature():
            logger.debug(f"Nature or Choice\tRegion: {region.id}")
            # Nature or Choice
            if not source:
                entry_task_id = str(next(id_generator))
                entry_place = create_place(entry_task_id, region)
                net.places.add(entry_place)
            else:
                entry_place = source
                _tmp_id = source.properties[PropertiesKeys.EXIT_RID]
                entry_place.properties.update(create_prop(region))
                entry_place.properties.update({PropertiesKeys.EXIT_RID: _tmp_id})

            # Exit place
            exit_task_id = str(next(id_generator))
            exit_place = create_place(exit_task_id, region)
            exit_place.properties.update(
                {
                    PropertiesKeys.ENTRY_RID: None,
                    PropertiesKeys.EXIT_RID: exit_place.properties[
                        PropertiesKeys.ENTRY_RID
                    ],
                    PropertiesKeys.DURATION: 0,
                }
            )
            net.places.add(exit_place)

            for i in range(len(region.children)):
                logger.debug(
                    f"Region: {region.id}\tChild: {region.children[i].id}[{i}]"
                )

                child = region.children[i]
                child_entry, child_exit = rec(child)

                # Entry transition for a child
                entry_child_trans_id = str(next(id_generator))
                entry_child_trans = create_transition(
                    entry_child_trans_id,
                    region,
                    probability=(
                        1 if not region.distribution else region.distribution[i]
                    ),
                    stop=True,
                )
                net.transitions.add(entry_child_trans)

                # Exit transition for a child
                exit_child_trans_id = str(next(id_generator))
                exit_child_trans = create_transition(
                    exit_child_trans_id,
                    region,
                    1,
                )
                net.transitions.add(exit_child_trans)

                add_arc_from_to(entry_place, entry_child_trans, net)
                add_arc_from_to(entry_child_trans, child_entry, net)
                add_arc_from_to(child_exit, exit_child_trans, net)
                add_arc_from_to(exit_child_trans, exit_place, net)

            return entry_place, exit_place
        elif region.is_loop():
            logger.debug(f"Loop\tRegion: {region.id}")
            # Loop
            if not source:
                entry_task_id = str(next(id_generator))
                entry_place = create_place(entry_task_id, region)
                net.places.add(entry_place)
            else:
                entry_place = source
                _tmp_id = source.properties[PropertiesKeys.EXIT_RID]
                entry_place.properties.update(create_prop(region))
                entry_place.properties.update({PropertiesKeys.EXIT_RID: _tmp_id})

            # Exit place
            exit_task_id = str(next(id_generator))
            exit_place = create_place(exit_task_id, region)
            exit_place.properties.update(
                {
                    PropertiesKeys.ENTRY_RID: None,
                    PropertiesKeys.EXIT_RID: exit_place.properties[
                        PropertiesKeys.ENTRY_RID
                    ],
                    PropertiesKeys.DURATION: 0,
                }
            )
            net.places.add(exit_place)

            # Entry transition
            entry_trans_id = str(next(id_generator))
            entry_trans = create_transition(entry_trans_id, region)
            # entry_trans.label = "Entry " + region.label
            entry_trans.properties[PropertiesKeys.LABEL] = "Entry " + region.label
            net.transitions.add(entry_trans)

            # Children region
            child_entry_place, child_exit_place = rec(region.children[0])

            # Loop transition
            loop_trans_id = str(next(id_generator))
            loop_trans = create_transition(loop_trans_id, region, probability=region.distribution, stop=True)
            # loop_trans.label = "Loop " + region.label
            loop_trans.properties[PropertiesKeys.LABEL] = "Loop " + region.label
            net.transitions.add(loop_trans)

            # Exit transition
            exit_trans_id = str(next(id_generator))
            exit_trans = create_transition(exit_trans_id, region, probability=1-region.distribution, stop=True)
            # exit_trans.label = "Exit " + region.label
            exit_trans.properties[PropertiesKeys.LABEL] = "Exit " + region.label
            net.transitions.add(exit_trans)

            # Add arcs
            add_arc_from_to(entry_place, entry_trans, net)
            add_arc_from_to(entry_trans, child_entry_place, net)
            add_arc_from_to(child_exit_place, loop_trans, net)
            add_arc_from_to(loop_trans, child_entry_place, net)
            add_arc_from_to(child_exit_place, exit_trans, net)
            add_arc_from_to(exit_trans, exit_place, net)

            return entry_place, exit_place




    entry_place, exit_place = rec(region)

    raw_im = Marking()
    raw_fm = Marking()
    for place in net.places:
        raw_im[place] = 0 if place.name != entry_place.name else 1
        raw_fm[place] = 0 if place.name != exit_place.name else 1

    im = TimeMarking(raw_im)
    fm = TimeMarking(raw_fm)

    return net, im, fm

#
# # dizionario delle properties
# properties: Dict[str, RegionProp] = {}
# distribution_match: Dict[str, List[Tuple[float, str]]] = {}
#
# places = set()
# transitions = set()
# arcs = set()
#
#
# def create_pnml_from_region(region: RegionModel):
#     header = '<?xml version="1.0" encoding="ISO-8859-1"?><pnml><net id="net1" type="http://www.pnml.org/version-2009/grammar/pnmlcoremodel"><name><text>Petri net</text></name><page id="n0">'
#
#     initial_tag_id = uuid4()
#     body = create_place_tag(initial_tag_id, region)
#     _body, exit_id = from_json(region, initial_tag_id)
#     body += _body
#
#     footer = "</page><finalmarkings><marking>"
#
#     for id in places:
#         footer += (
#             f'<place idref="{id}"><text>{0 if id != exit_id else 1}</text></place>'
#         )
#
#     footer += "</marking></finalmarkings></net></pnml>"
#
#     return header + body + footer
#
#
# def create_place_tag(id, region, label="", isInitial=False):
#     initialMarking = ""
#     if isInitial:
#         initialMarking = "<initialMarking><text>1</text></initialMarking>"
#
#     places.add(id)
#     saveProp(id, region)
#     return f'<place id="{id}"><name><text>{label or ""}</text></name>{initialMarking}</place>'
#
#
# def create_transition_tag(id, region, label=""):
#     label = f"{id} LABEL"
#
#     saveProp(id, region)
#     return f'<transition id="{id}"><name><text>{label or ""}</text></name></transition>'
#
#
# def create_arc_tag(id, source_id, target_id, label=""):
#     return f'<arc id="{id}" source="{source_id}" target="{target_id}"><name><text>{label or ""}</text></name></arc>'
#
#
# def create_task_tag(source_id, task: RegionModel):
#     entry_id = source_id
#     exit_id = f"{task.id}_exit"
#     trans_id = task.id
#
#     entry_place = ""
#     if not entry_id:
#         entry_place = create_place_tag(entry_id, task, task.label)
#     # places.add(entry_place)
#
#     arc1 = create_arc_tag(uuid4(), entry_id, trans_id)
#     # arcs.add(arc1)
#
#     trans = create_transition_tag(trans_id, task, task.label)
#     # transitions.add(trans)
#
#     arc2 = create_arc_tag(uuid4(), trans_id, exit_id)
#
#     exit_place = create_place_tag(exit_id, task, task.label)
#     # places.add(exit_place)
#
#     return [entry_place + arc1 + trans + arc2 + exit_place, exit_id]
#
#
# def from_json(region: RegionModel, source_id=None):
#
#     if region.is_task():
#         source_id = source_id or f"{region.id}_entry"
#         tag, exit_place_id = create_task_tag(source_id, region)
#
#         return [tag, exit_place_id]
#     elif region.is_sequential():
#         tag = ""
#         prev_exit_id = source_id
#         first_entry_id = source_id
#
#         for child in region.children:
#             _tag, child_exit_id = from_json(child, source_id)
#             tag += _tag
#             if not first_entry_id:
#                 first_entry_id = f"{region.id}_entry"
#                 prev_exit_id = child_exit_id
#                 continue
#
#             tag += create_arc_tag(uuid4(), prev_exit_id, first_entry_id)
#             prev_exit_id = child_exit_id
#             source_id = prev_exit_id
#
#         return [tag, prev_exit_id]
#     elif region.is_parallel():
#         tag = ""
#
#         # Place di entrata
#         if not source_id:
#             source_id = f"{region.id}_entry"
#             tag += create_place_tag(source_id, region)
#
#         _tag, exit_id = create_parallel_tag(region, source_id)
#         return [tag + _tag, exit_id]
#     else:
#         tag = ""
#
#         if not source_id:
#             source_id = f"{region.id}_entry"
#             tag += create_place_tag(source_id, region)
#
#         _tag, exit_id = create_split(region, source_id)
#         tag += _tag
#
#         return [tag, exit_id]
#
#
# def add_distribution_match(place: str, p: float, sid: str):
#     if distribution_match.get(place) == None:
#         distribution_match.update({place: []})
#
#     distribution_match.get(place).append((p, sid))
#
#
# def create_split(region: RegionModel, source_id):
#     tag = ""
#     exit_id = f"{region.id}_exit"
#     tag += create_place_tag(exit_id, region)
#
#     for i in range(len(region.children)):
#         child = region.children[i]
#
#         child_source_id = f"{child.id}_entry"
#         tag += create_place_tag(child_source_id, region)
#
#         trans_entry_child_id = f"{region.id}_child{child.id}"
#         tag += create_transition_tag(trans_entry_child_id, region)
#
#         tag += create_arc_tag(uuid4(), source_id, trans_entry_child_id)
#         tag += create_arc_tag(uuid4(), trans_entry_child_id, child_source_id)
#
#         if region.is_nature():
#             add_distribution_match(
#                 source_id, region.distribution[i], trans_entry_child_id
#             )
#         else:
#             add_distribution_match(source_id, 1 if i == 0 else 0, trans_entry_child_id)
#
#         _tag, child_exit_id = from_json(child, child_source_id)
#         tag += _tag
#
#         trans_exit_child_id = uuid4()
#         tag += create_transition_tag(trans_exit_child_id, region)
#
#         tag += create_arc_tag(uuid4(), child_exit_id, trans_exit_child_id)
#         tag += create_arc_tag(uuid4(), trans_exit_child_id, exit_id)
#
#     return [tag, exit_id]
#
#
# def create_parallel_tag(region, source_id):
#     tag = ""
#     # Transizione in entrata
#     entry_trans_id = region.id
#     tag += create_transition_tag(region.id, region)
#
#     # Arco che collega place e transizione in entrata
#     tag += create_arc_tag(uuid4(), source_id, entry_trans_id)
#
#     # Place di uscita dlla regione
#     exit_place_id = f"{region.id}_exit"
#     tag += create_place_tag(exit_place_id, region)
#
#     # Transizione in uscita
#     exit_trans_id = uuid4()
#     tag += create_transition_tag(exit_trans_id, region)
#
#     # Arco che collega la transizione di uscita e il place di uscita
#     tag += create_arc_tag(uuid4(), exit_trans_id, exit_place_id)
#
#     for child in region.children:
#         source_child_id = f"{child.id}_entry"
#
#         tag += create_place_tag(source_child_id, region)
#         tag += create_arc_tag(uuid4(), entry_trans_id, source_child_id)
#
#         _tag, child_exit_id = from_json(child, source_child_id)
#         tag += _tag
#
#         tag += create_arc_tag(uuid4(), child_exit_id, exit_trans_id)
#
#     return [tag, exit_place_id]
#
#
# def saveProp(component_id: str, region: RegionModel):
#
#     properties.update(
#         {
#             str(component_id): RegionProp(
#                 region.id,
#                 region.label,
#                 region.duration,
#                 region.impacts,
#                 region.type,
#                 region.distribution,
#             )
#         }
#     )
#
#
# def getProps() -> Tuple[Dict[str, RegionProp], Dict[str, List[Tuple[float, str]]]]:
#     return properties, distribution_match
