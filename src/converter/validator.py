from model.region import RegionModel, RegionType
import math
import logging

logger = logging.getLogger(__name__)


def region_validator(region: RegionModel):

    def explore(_r: RegionModel, expected_impact_length: int = None):
        logger.debug(f"Esploro la Region: {_r.label} id:{_r.id}")
        # controlli per tutti i tipi di regione
        if not _r.id or not isinstance(_r.type, RegionType):
            logger.error(
                f"Id o tipo della regione {region.label} id:{region.id} è None o vuota"
            )
            return False, None

        if _r.duration is None or _r.duration < 0:
            logger.error(
                f"Regione {region.label} id:{region.id} ha durata {region.duration} (< 0 o None)"
            )
            return False, None

        # controllo la regione in base al suo tipo
        status, expected_impact_length = __switch_case(_r, expected_impact_length)

        logger.debug(f"Expected_Value:{expected_impact_length}")

        if status is False:
            return False, None

        # se ho dei children
        if _r.children:
            val = expected_impact_length
            for child in _r.children:
                # se il child o i children di child non sono validi
                st, val = explore(child, val)
                if not st:
                    return False, None

        return True, expected_impact_length

    return explore(region, expected_impact_length=None)[0]


def __switch_case(region: RegionModel, expected_impact_length: int = None):
    # funzione che mappa una chiamata a funzione in base al tipo della region
    switch = {
        RegionType.SEQUENTIAL: __sequential_validator,
        RegionType.TASK: __task_validator,
        RegionType.PARALLEL: __parallel_validator,
        RegionType.CHOICE: __choice_validator,
        RegionType.NATURE: __nature_validator,
        RegionType.LOOP: __loop_validator
    }

    validator_fn = switch.get(region.type)

    if not validator_fn:
        print(
            f"Tipo regione non supportato: {region.type} nella regione {region.label} di id: {region.id}"
        )
        return False, None

    return validator_fn(region, expected_impact_length)


def __sequential_validator(region: RegionModel, expected_impact_length: int = None):
    logger.debug("Validatore Sequenziale")
    # per essere sequenziale deve almeno avere 2 children
    if not region.children or len(region.children) < 2:
        logger.error(
            f"Regione Sequenziale {region.label} di id:{region.id} ha meno di 2 children: {len(region.children or [])}"
        )
        return False, None

    # non devo avere impatti
    if region.impacts:
        logger.error(
            f"Regione Sequenziale {region.label} di id:{region.id} ha impatti: {region.impacts}"
        )
        return False, None

    # non devo avere distribuzioni di probabilità
    if region.distribution:
        logger.error(
            f"Regione Sequenziale {region.label} di id:{region.id} ha distribuzione di probabilità: {region.distribution}"
        )
        return False, None

    # durata???

    return True, expected_impact_length


def __task_validator(region: RegionModel, expected_impact_length: int = None):
    logger.debug("Validatore Task")
    logger.debug(f"I meiei impatti sono: {region.impacts}")
    logger.debug(f"expected_impact_length = {expected_impact_length}")

    if not region.impacts:
        logger.error(
            f"Regione Task {region.label} di id:{region.id} non ha impatti: {region.impacts}"
        )
        return False, expected_impact_length

    for impact in region.impacts:
        if impact < 0:
            logger.error(
                f"Regione Task {region.label} di id:{region.id} ha impatti negativi: {region.impacts}"
            )
            return False, expected_impact_length

    if expected_impact_length is None:
        expected_impact_length = len(region.impacts)
        logger.debug(
            f"Set della lunghezza degli impatti da {region.label} di id: {region.id} fa set a {expected_impact_length}"
        )
    elif len(region.impacts) != expected_impact_length:
        logger.error(
            f"Regione Task {region.label} di id:{region.id} ha una lunghezza di impacts diversa ({len(region.impacts or [])} vs {expected_impact_length})"
        )
        return False, expected_impact_length

    if region.children:
        logger.error(
            f"Regione Task {region.label} di id:{region.id} ha figli: {region.children}"
        )
        return False, expected_impact_length

    if region.distribution:
        logger.error(
            f"Regione Task {region.label} di id:{region.id} ha distribuzione di probabilità: {region.distribution}"
        )
        return False, expected_impact_length

    return True, expected_impact_length


def __parallel_validator(region: RegionModel, expected_impact_length: int = None):
    logger.debug("Validatore Parallelo")
    # devo avere almeno 2 children
    if not region.children or len(region.children) < 2:
        logger.error(
            f"Regione Parallela {region.label} di id:{region.id} non ha almeno 2 children: {len(region.children or [])}"
        )
        return False, None

    # non devo avere impatti
    if region.impacts:
        logger.error(
            f"Regione Parallela {region.label} di id:{region.id} ha impatti: {region.impacts}"
        )
        return False, None

    # non devo avere distribuzioni di probabilità
    if region.distribution:
        logger.error(
            f"Regione Parallela {region.label} di id:{region.id} ha distribuzione: {region.distribution}"
        )
        return False, None

    # durata??

    return True, expected_impact_length


def __nature_validator(region: RegionModel, expected_impact_length: int = None):
    logger.debug("Validatore Natura")
    # devo avere almeno 2 children
    if not region.children or len(region.children) < 2:
        logger.error(
            f"Regione Natura {region.label} di id:{region.id} non ha almeno 2 figli: {len(region.children or [])}"
        )
        return False, None

    if not region.distribution and not isinstance(region.distribution, list):
        logger.error(
            f"Regione Scelta {region.label} di id:{region.id} non ha distribuzione di probabilità: {region.distribution}"
        )
        return False, None

    # devo avere la distribuzione di probabilità e  len(prob) = numero childern
    if not region.distribution or not isinstance(region.distribution, list) or len(region.distribution) != len(
        region.children or []
    ):
        logger.error(
            f"Regione Natura {region.label} di id:{region.id} non ha distribuzione di probabilità oppure: len(prob) != numero childern"
        )
        return False, None

    # devo avere la somma di distibuzione delle probabilità vicina a  1
    prob_sum = sum(region.distribution)
    if not math.isclose(prob_sum, 1.0, rel_tol=1e-9):
        logger.error(
            f"Regione Natura {region.label} di id:{region.id} non somma a 1 la sua probabilità: {prob_sum}"
        )
        return False, None

    # non devo avere impatti
    if region.impacts:
        logger.error(
            f"Regione Natura {region.label} di id:{region.id} ha impatti: {region.impacts}"
        )
        return False, None

    # duration?

    return True, expected_impact_length


def __choice_validator(region: RegionModel, expected_impact_length: int = None):
    logger.debug("Validatore Choice")
    # devo avere almeno 2 children
    if not region.children or len(region.children) < 2:
        logger.error(
            f"Regione Scelta {region.label} di id:{region.id} non ha alemeno 2 figli: {len(region.children or [])}"
        )
        return False, None

    # non devo avere una distribuzione di probabilità
    if region.distribution is not None:
        logger.error(f"Regione Scelta {region.label} di id:{region.id} non deve avere probabilità")

    # se ho la distribuzione di probabilità allora deve essere vicino a 1
    if region.distribution:
        prob_sum = sum(region.distribution)
        if not math.isclose(prob_sum, 1.0, rel_tol=1e-9):
            logger.error(
                f"Regione Scelta {region.label} di id:{region.id} la cui somma delle probabilità non corrisponde a 1: {prob_sum}"
            )
            return False, None

    # non devo avere impatti
    if region.impacts:
        logger.error(
            f"Regione Scelta {region.label} di id:{region.id} ha impatti: {region.impacts}"
        )
        return False, None

    # duration?

    return True, expected_impact_length

def __loop_validator(region: RegionModel, expected_impact_length: int = None):
    logger.debug("Validatore Loop")
    children = region.children
    if children is None or len(children) != 1:
        logger.error(
            f"Regione Loop {region.id} deve avere esattamente un figlio, trovato: {len(children or [])}"
        )
        return False, None

    if not isinstance(region.distribution, float) or region.distribution is None:
        logger.error(f"Regione Loop {region.id} deve avere una distribuzione di probabilità di tipo float")
        return False, None

    return True, expected_impact_length