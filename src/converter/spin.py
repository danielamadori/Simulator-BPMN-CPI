import logging

from pm4py.objects.petri_net.obj import Marking
from pm4py.objects.petri_net.utils.petri_utils import place_set_as_marking

from converter.validator import region_validator
from model.petri_net.time_spin import TimeMarking
from model.petri_net.wrapper import WrapperPetriNet
from model.region import RegionModel
from utils.exceptions import ValidationError
from utils.net_utils import PropertiesKeys, add_arc_from_to, collapse_places

logger = logging.getLogger(__name__)


def serial_generator(initial: int = 0):
    """Generates a unique ID for each call."""
    counter = initial
    while True:
        yield counter
        counter += 1


# SESE Methods
def create_entry_place(place_id: str, region: RegionModel):
    place = WrapperPetriNet.Place(place_id)

    place.entry_id = region.id
    place.exit_id = None
    place.region_label = region.label
    place.region_type = region.type
    place.duration = region.duration
    place.impacts = region.impacts

    return place


def create_entry_place_prop(region: RegionModel):
    prop = {PropertiesKeys.ENTRY_RID: region.id, PropertiesKeys.EXIT_RID: None, PropertiesKeys.LABEL: region.label,
            PropertiesKeys.TYPE: region.type, PropertiesKeys.DURATION: region.duration,
            PropertiesKeys.IMPACTS: region.impacts}

    return prop


def create_exit_place(place_id: str, region: RegionModel):
    place = create_entry_place(place_id, region)

    place.entry_id = None
    place.exit_id = region.id
    place.duration = 0
    place.impacts = None

    return place


def create_transition(trans_id: str, region: RegionModel, probability: float = 1, stop: bool = False):
    trans = WrapperPetriNet.Transition(trans_id, label=region.label)

    trans.region_id = region.id
    trans.region_label = region.label
    trans.region_type = region.type
    trans.probability = probability
    trans.stop = stop

    return trans


def from_region(region: RegionModel):
    if not region_validator(region):
        logger.error("Lancio eccezzione perchè i dati forniti non sono validi")
        raise ValidationError()
    else:
        logger.info("Validazione avvenuta con successo")

    net = WrapperPetriNet()
    id_generator = serial_generator()

    def rec(__region: RegionModel) -> tuple[
        WrapperPetriNet.Place, WrapperPetriNet.Place]:
        if __region.is_task():
            # Task
            # Entry Place

            entry_task_id = str(next(id_generator))
            entry_place = create_entry_place(entry_task_id, __region)
            net.places.add(entry_place)

            # Exit place
            exit_task_id = str(next(id_generator))
            exit_place = create_exit_place(exit_task_id, __region)

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

            entry_task_id = str(next(id_generator))
            entry_place = create_entry_place(entry_task_id, __region)
            net.places.add(entry_place)

            # Exit place
            exit_task_id = str(next(id_generator))
            exit_place = create_exit_place(exit_task_id, __region)
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
            first_place = None
            last_child = None

            for child in __region.children:
                child_entry, child_exit = rec(child)
                if first_place is None:
                    first_place = child_entry
                else:
                    collapse_places(net, last_child, child_entry)
                last_child = child_exit

            return first_place, last_child
        elif __region.is_choice() or __region.is_nature():
            # Nature or Choice

            entry_task_id = str(next(id_generator))
            entry_place = create_entry_place(entry_task_id, __region)
            net.places.add(entry_place)

            # Exit place
            exit_task_id = str(next(id_generator))
            exit_place = create_exit_place(exit_task_id, __region)
            net.places.add(exit_place)

            for i in range(len(__region.children)):
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
            # Loop
            entry_task_id = str(next(id_generator))
            entry_place = create_entry_place(entry_task_id, __region)
            net.places.add(entry_place)

            # Exit place
            exit_task_id = str(next(id_generator))
            exit_place = create_exit_place(exit_task_id, __region)
            net.places.add(exit_place)

            # Entry transition
            entry_trans_id = str(next(id_generator))
            entry_trans = create_transition(entry_trans_id, __region)
            entry_trans.label = "Entry " + region.label
            entry_trans.region_label = "Entry " + __region.label
            net.transitions.add(entry_trans)

            # Children region
            child_entry_place, child_exit_place = rec(__region.children[0])

            child_exit_place.visit_limit = __region.bound

            # Loop transition
            loop_trans_id = str(next(id_generator))
            loop_trans = create_transition(loop_trans_id, __region, probability=__region.distribution, stop=True)
            loop_trans.label = "Loop " + region.label
            loop_trans.region_label = "Loop " + __region.label
            net.transitions.add(loop_trans)

            # Exit transition
            exit_trans_id = str(next(id_generator))
            exit_trans = create_transition(exit_trans_id, __region, probability=1 - __region.distribution, stop=True)
            exit_trans.label = "Exit " + region.label
            exit_trans.region_label = "Exit " + __region.label
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

    raw_im = place_set_as_marking([entry_place])
    raw_fm = place_set_as_marking([exit_place])

    im = TimeMarking(raw_im)
    fm = TimeMarking(raw_fm)

    return net, im, fm
