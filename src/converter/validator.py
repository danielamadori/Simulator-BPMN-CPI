from model.region import RegionModel, RegionType


def region_validator(region: RegionModel):
    
    def explore(region : RegionModel, expected_impact_length: int = None):
        print(f"Esploro la Region: {region.id}")
        #controlli per tutti i tipi di regione
        if not region.id or not region.type:
            print("Id o tipo della regione è None o vuota")
            return False
        
        #controllo la regione in base al suo tipo
        if not __switch_case(region, expected_impact_length):
            return False
        
        # se ho dei children
        if region.children and len(region.children or []) > 0 :
            for child in region.children:
            #se il child o i children di child non sono validi
                if not explore(child, expected_impact_length):
                    return False
                
        return True
    return explore(region, expected_impact_length = None)
        
        



def __switch_case(region: RegionModel, expected_impact_length: int = None):
    #funzione che mappa una chiamata a funzione in base al tipo della region
    switch = {
        RegionType.SEQUENTIAL: __sequential_validator,
        RegionType.TASK: lambda r: __task_validator(r, expected_impact_length),
        RegionType.PARALLEL: __parallel_validator,
        RegionType.CHOICE: __choice_validator,
        RegionType.NATURE: __nature_validator,
    }

    validator_fn = switch.get(region.type)

    if not validator_fn:
        print(f"Tipo regione non supportato: {region.type}")
        return False

    return validator_fn(region)


def __sequential_validator(region : RegionModel):
    print("Validatore Sequenziale")
    #per essere sequenziale deve almeno avere 2 children 
    if not region.children or len(region.children) < 1:
        return False
    
    #non devo avere impatti
    if region.impacts:
        return False
    
    #non devo avere distribuzioni di probabilità
    if region.distribution:
        return False
    
    #durata???

    return True

def __task_validator(region: RegionModel, expected_impact_length: int = None):
    print("Validatore Task")
    # setto il valore degli impatti se già non c'era (primo task)
    if expected_impact_length is None:
        expected_impact_length = len(region.impacts)

    #controllo di lunghezza vettore impatti uguale per ogni task
    if not region.impacts or len(region.impacts) != expected_impact_length:
        print(f"Task {region.id} ha una lunghezza di impacts diversa ({len(region.impacts)} vs {expected_impact_length})")
        return False
    # gli impatti devono essere > 0
    for impact in region.impacts:
        if impact < 0:
            return False
        
    #La durata deve essere >= 0
    if region.duration is None or region.duration < 0:
        return False

    
    # un task non ha children 
    if region.children:
        return False
    
    # non deve avere distribuzione di probabilità
    if region.distribution:
        return False

    return True

def __parallel_validator(region : RegionModel):
    print("Validatore Parallelo")
    # devo avere almeno 2 children
    if not region.children or len(region.children) < 2:
        return False

    # non devo avere impatti
    if region.impacts:
        return False

    #non devo avere distribuzioni di probabilità
    if region.distribution:
        return False  

    #durata??  

    return True

def __nature_validator(region : RegionModel):
    print("Validatore Natura")
    # devo avere almeno 2 children
    if not region.children or len(region.children) < 2:
        return False
    
    # devo avere la distribuzione di probabilità e  len(prob) = numero childern
    if not region.distribution or len(region.distribution) != len(region.children or []):
        return False

    # non devo avere impatti
    if region.impacts:
        return False
    
    #duration?

    return True

def __choice_validator(region : RegionModel):
    print("Validatore Choice")
    # devo avere almeno 2 children
    if not region.children or len(region.children) < 2:
        return False
    
    # se ho la distribuzione di probabilità allora len(prob) = numero childern
    if region.distribution and len(region.distribution) != len(region.children or []):
        return False


    # non devo avere impatti
    if region.impacts:
        return False
    
    #duration?

    return True