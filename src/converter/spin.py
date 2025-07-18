import logging

from pm4py.objects.petri_net.obj import Marking

from converter.validator import region_validator
from model.petri_net.time_spin import TimeMarking
from model.petri_net.wrapper import WrapperPetriNet, add_arc_from_to
from model.region import RegionModel
from utils.exceptions import ValidationError
from utils.net_utils import PropertiesKeys

logger = logging.getLogger(__name__)


def serial_generator(initial: int = 0):
    """Generates a unique ID for each call."""
    counter = initial
    while True:
        yield counter
        counter += 1


def get_place_prop(place: WrapperPetriNet.Place):
    return place.properties


def get_trans_prop(trans: WrapperPetriNet.Transition):
    return trans.properties


def create_place(place_id: str, region: RegionModel):
    place = WrapperPetriNet.Place(
        place_id,
    )

    place.properties.update(create_place_prop(region))

    return place


def create_place_prop(region: RegionModel):
    prop = {PropertiesKeys.ENTRY_RID: region.id, PropertiesKeys.EXIT_RID: None, PropertiesKeys.LABEL: region.label,
            PropertiesKeys.TYPE: region.type, PropertiesKeys.DURATION: region.duration,
            PropertiesKeys.IMPACTS: region.impacts}

    return prop


def create_transition(trans_id: str, region: RegionModel, probability: float = 1, stop: bool = False):
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

    def rec(__region: RegionModel, source: WrapperPetriNet.Place | None = None):
        if __region.is_task():
            # Task
            # Entry Place
            logger.debug(f"Task\tRegion: {__region.id}")
            if not source:
                entry_task_id = str(next(id_generator))
                entry_place = create_place(entry_task_id, __region)
                net.places.add(entry_place)
            else:
                entry_place = source
                _tmp_id = source.properties[PropertiesKeys.EXIT_RID]
                entry_place.properties.update(create_place_prop(__region))
                entry_place.properties.update({PropertiesKeys.EXIT_RID: _tmp_id})

            # Exit place
            exit_task_id = str(next(id_generator))
            exit_place = create_place(exit_task_id, __region)
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
            trans = create_transition(trans_id, __region)
            net.transitions.add(trans)

            # Arcs
            add_arc_from_to(entry_place, trans, net)
            add_arc_from_to(trans, exit_place, net)

            return entry_place, exit_place

        elif __region.is_parallel():
            # Parallel Gateway
            # Entry Place
            logger.debug(f"Parallel\tRegion: {__region.id}")
            if not source:
                entry_task_id = str(next(id_generator))
                entry_place = create_place(entry_task_id, __region)
                net.places.add(entry_place)
            else:
                entry_place = source
                _tmp_id = source.properties[PropertiesKeys.EXIT_RID]
                entry_place.properties.update(create_place_prop(__region))
                entry_place.properties.update({PropertiesKeys.EXIT_RID: _tmp_id})

            # Exit place
            exit_task_id = str(next(id_generator))
            exit_place = create_place(exit_task_id, __region)
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
            entry_trans = create_transition(entry_trans_id, __region)
            net.transitions.add(entry_trans)

            # Exit Transition
            exit_trans_id = str(next(id_generator))
            exit_trans = create_transition(exit_trans_id, __region)
            net.transitions.add(exit_trans)

            # Add entry and exit arc
            add_arc_from_to(entry_place, entry_trans, net)
            add_arc_from_to(exit_trans, exit_place, net)

            for child in __region.children:
                child_entry, child_exit = rec(child)
                add_arc_from_to(entry_trans, child_entry, net)
                add_arc_from_to(child_exit, exit_trans, net)

            return entry_place, exit_place
        elif __region.is_sequential():
            logger.debug(f"Sequential\tRegion: {__region.id}")
            if not source:
                entry_task_id = str(next(id_generator))
                entry_place = create_place(entry_task_id, __region)
                net.places.add(entry_place)
            else:
                entry_place = source
                _tmp_id = source.properties[PropertiesKeys.EXIT_RID]
                entry_place.properties.update(create_place_prop(__region))
                entry_place.properties.update({PropertiesKeys.EXIT_RID: _tmp_id})

            prev_child = entry_place

            for child in __region.children:
                child_entry, child_exit = rec(child, prev_child)
                prev_child = child_exit

            return entry_place, prev_child
        elif __region.is_choice() or __region.is_nature():
            logger.debug(f"Nature or Choice\tRegion: {__region.id}")
            # Nature or Choice
            if not source:
                entry_task_id = str(next(id_generator))
                entry_place = create_place(entry_task_id, __region)
                net.places.add(entry_place)
            else:
                entry_place = source
                _tmp_id = source.properties[PropertiesKeys.EXIT_RID]
                entry_place.properties.update(create_place_prop(__region))
                entry_place.properties.update({PropertiesKeys.EXIT_RID: _tmp_id})

            # Exit place
            exit_task_id = str(next(id_generator))
            exit_place = create_place(exit_task_id, __region)
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

            for i in range(len(__region.children)):
                logger.debug(
                    f"Region: {__region.id}\tChild: {__region.children[i].id}[{i}]"
                )

                child = __region.children[i]
                child_entry, child_exit = rec(child)

                # Entry transition for a child
                entry_child_trans_id = str(next(id_generator))
                entry_child_trans = create_transition(
                    entry_child_trans_id,
                    __region,
                    probability=(
                        1 if not __region.distribution else __region.distribution[i]
                    ),
                    stop=True,
                )
                net.transitions.add(entry_child_trans)

                # Exit transition for a child
                exit_child_trans_id = str(next(id_generator))
                exit_child_trans = create_transition(
                    exit_child_trans_id,
                    __region,
                    1,
                )
                net.transitions.add(exit_child_trans)

                add_arc_from_to(entry_place, entry_child_trans, net)
                add_arc_from_to(entry_child_trans, child_entry, net)
                add_arc_from_to(child_exit, exit_child_trans, net)
                add_arc_from_to(exit_child_trans, exit_place, net)

            return entry_place, exit_place
        elif __region.is_loop():
            logger.debug(f"Loop\tRegion: {__region.id}")
            # Loop
            if not source:
                entry_task_id = str(next(id_generator))
                entry_place = create_place(entry_task_id, __region)
                net.places.add(entry_place)
            else:
                entry_place = source
                _tmp_id = source.properties[PropertiesKeys.EXIT_RID]
                entry_place.properties.update(create_place_prop(__region))
                entry_place.properties.update({PropertiesKeys.EXIT_RID: _tmp_id})

            # Exit place
            exit_task_id = str(next(id_generator))
            exit_place = create_place(exit_task_id, __region)
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
            entry_trans = create_transition(entry_trans_id, __region)
            entry_trans.label = "Entry " + region.label
            entry_trans.properties[PropertiesKeys.LABEL] = "Entry " + __region.label
            net.transitions.add(entry_trans)

            # Children region
            child_entry_place, child_exit_place = rec(__region.children[0])

            child_exit_place.properties.update({PropertiesKeys.VISIT_LIMIT: __region.bound})

            # Loop transition
            loop_trans_id = str(next(id_generator))
            loop_trans = create_transition(loop_trans_id, __region, probability=__region.distribution, stop=True)
            loop_trans.label = "Loop " + region.label
            loop_trans.properties[PropertiesKeys.LABEL] = "Loop " + __region.label
            net.transitions.add(loop_trans)

            # Exit transition
            exit_trans_id = str(next(id_generator))
            exit_trans = create_transition(exit_trans_id, __region, probability=1 - __region.distribution, stop=True)
            exit_trans.label = "Exit " + region.label
            exit_trans.properties[PropertiesKeys.LABEL] = "Exit " + __region.label
            net.transitions.add(exit_trans)

            # Add arcs
            add_arc_from_to(entry_place, entry_trans, net)
            add_arc_from_to(entry_trans, child_entry_place, net)
            add_arc_from_to(child_exit_place, loop_trans, net)
            add_arc_from_to(loop_trans, child_entry_place, net)
            add_arc_from_to(child_exit_place, exit_trans, net)
            add_arc_from_to(exit_trans, exit_place, net)

            return entry_place, exit_place

        raise ValueError(f"Unknown region type for region id {__region.id}: {__region.type}")

    entry_place, exit_place = rec(region)

    raw_im = Marking()
    raw_fm = Marking()
    for place in net.places:
        raw_im[place] = 0 if place.name != entry_place.name else 1
        raw_fm[place] = 0 if place.name != exit_place.name else 1

    im = TimeMarking(raw_im)
    fm = TimeMarking(raw_fm)

    return net, im, fm
