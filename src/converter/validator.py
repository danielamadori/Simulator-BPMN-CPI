from model.region import RegionModel, RegionType
import math


def region_validator(region: RegionModel):

    def explore(_r: RegionModel, expected_impact_length: int = None):
        # print(f"Esploro la Region: {_r.id}")
        # controlli per tutti i tipi di regione
        if not _r.id or not isinstance(_r.type, RegionType):
            print("Id o tipo della regione è None o vuota")
            return False, None

        if _r.duration is None or _r.duration < 0:
            return False, None

        # controllo la regione in base al suo tipo
        status, expected_impact_length = __switch_case(_r, expected_impact_length)

        # print(f"Expected_Value:{expected_impact_length}")

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
    }

    validator_fn = switch.get(region.type)

    if not validator_fn:
        print(f"Tipo regione non supportato: {region.type}")
        return False, None

    return validator_fn(region, expected_impact_length)


def __sequential_validator(region: RegionModel, expected_impact_length: int = None):
    # print("Validatore Sequenziale")
    # per essere sequenziale deve almeno avere 2 children
    if not region.children or len(region.children) < 2:
        return False, None

    # non devo avere impatti
    if region.impacts:
        return False, None

    # non devo avere distribuzioni di probabilità
    if region.distribution:
        return False, None

    # durata???

    return True, expected_impact_length


def __task_validator(region: RegionModel, expected_impact_length: int = None):
    # print("Validatore Task")
    # print(f"I meiei impatti sono: {region.impacts}")
    # print(f"expected_impact_length = {expected_impact_length}")

    if not region.impacts:
        return False, expected_impact_length

    for impact in region.impacts:
        if impact < 0:
            return False, expected_impact_length

    if expected_impact_length is None:
        expected_impact_length = len(region.impacts)
    elif len(region.impacts) != expected_impact_length:
        print(
            f"Task {region.id} ha una lunghezza di impacts diversa ({len(region.impacts)} vs {expected_impact_length})"
        )
        return False, expected_impact_length

    if region.children:
        return False, expected_impact_length

    if region.distribution:
        return False, expected_impact_length

    return True, expected_impact_length


def __parallel_validator(region: RegionModel, expected_impact_length: int = None):
    # print("Validatore Parallelo")
    # devo avere almeno 2 children
    if not region.children or len(region.children) < 2:
        return False, None

    # non devo avere impatti
    if region.impacts:
        return False, None

    # non devo avere distribuzioni di probabilità
    if region.distribution:
        return False, None

    # durata??

    return True, expected_impact_length


def __nature_validator(region: RegionModel, expected_impact_length: int = None):
    # print("Validatore Natura")
    # devo avere almeno 2 children
    if not region.children or len(region.children) < 2:
        return False, None

    # devo avere la distribuzione di probabilità e  len(prob) = numero childern
    if not region.distribution or len(region.distribution) != len(
        region.children or []
    ):
        return False, None

    # devo avere la somma di distibuzione delle probabilità vicina a  1
    prob_sum = sum(region.distribution)
    if not math.isclose(prob_sum, 1.0, rel_tol=1e-9):
        return False, None

    # non devo avere impatti
    if region.impacts:
        return False, None

    # duration?

    return True, expected_impact_length


def __choice_validator(region: RegionModel, expected_impact_length: int = None):
    # print("Validatore Choice")
    # devo avere almeno 2 children
    if not region.children or len(region.children) < 2:
        return False, None

    # se ho la distribuzione di probabilità allora len(prob) = numero childern
    if region.distribution and len(region.distribution) != len(region.children or []):
        return False, None

    # se ho la distribuzione di probabilità allora deve essere vicino a 1
    if region.distribution:
        prob_sum = sum(region.distribution)
        if not math.isclose(prob_sum, 1.0, rel_tol=1e-9):
            return False, None

    # non devo avere impatti
    if region.impacts:
        return False, None

    # duration?

    return True, expected_impact_length
