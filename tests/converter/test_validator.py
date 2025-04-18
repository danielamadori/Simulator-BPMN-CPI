from converter.validator import region_validator
from model.region import RegionModel, RegionType
from tests.converter.region_factory import region_factory

'''
Esiste una regionFactory che crea regioni valide, per evitare duplicazione generarle da li e modificare i campi di interesse
'''

#VALIDATOR

'''
TASKS
'''
# NOT validità explore per id 
def test_validator_valid():
    region = region_factory(RegionType.TASK)
    region.id =""
    assert region_validator(region) is False



#validità task per la durata
def test_task_valid():
    region = region_factory(RegionType.TASK)
    region.duration=5
    assert region_validator(region) is True

# NOT validità task per durata
def test_task_invalid_duration():
    region = region_factory(RegionType.TASK)
    region.duration= -5
    assert region_validator(region) is False

#NOT validità per lunghezza diversa degli impatti dei task
def test_task_invalid_impacts_length():
    parent = region_factory(RegionType.SEQUENTIAL)
    #di default il task ha come impatti un vettore di 3 elementi 
    parent.children[1].impacts = [1,2]
    assert region_validator(parent) is False

# validità per lunghezza uguale degli impatti dei task
def test_task_valid_impacts_length():
    region = region_factory(RegionType.SEQUENTIAL)
    assert region_validator(region) is True

# NOT validità per valore impatti < 0
def test_task_invalid_impacts_values():
    parent = region_factory(RegionType.SEQUENTIAL)
    parent.children[0].impacts = [0,0,-1]
    assert region_validator(parent) is False

#NOT validità per task con children
def test_task_invalid_has_children():
    parent = region_factory(RegionType.SEQUENTIAL)
    parent.children[0].children = region_factory(RegionType.TASK)
    assert region_validator(parent) is False

#NOT validità per task con distribuzione
def test_task_invalid_with_distribution():
    parent = region_factory(RegionType.SEQUENTIAL)
    parent.children[0].distribution = [0.7,0.2,0.1]
    assert region_validator(parent) is False

'''
SEQUENTIAL
'''

# default sequential
def test_sequential_valid_with_children():
    region = region_factory(RegionType.SEQUENTIAL)
    assert region_validator(region) is True 

#NOT validità per sequential con meno di 2 children
def test_sequential_invalid_with_children():
    parent = region_factory(RegionType.SEQUENTIAL)
    del parent.children[1]
    assert region_validator(parent) is False 

#NOT validità per sequential con impatti
def test_sequential_invalid_impacts():
    region = region_factory(RegionType.SEQUENTIAL)
    region.impacts = [1,2,3]
    assert region_validator(region) is False 

#NOT validità per sequential con distribuzione di probabilità
def test_sequential_invalid_distribution():
    region = region_factory(RegionType.SEQUENTIAL)
    region.distribution = [0.2,0.4,0.4]
    assert region_validator(region) is False 



'''
PARALLEL
'''

#default parallel
def test_parallel_valid_default():
    region = region_factory(RegionType.PARALLEL)
    assert region_validator(region) is True 

#NOT valid parallel for children
def test_parallel_invalid_children():
    region = region_factory(RegionType.PARALLEL)
    del region.children[1]
    assert region_validator(region) is False 

#NOT valid parallel for impacts
def test_parallel_invalid_distribution():
    region = region_factory(RegionType.PARALLEL)
    region.distribution = [1,0,0]
    assert region_validator(region) is False 

#NOT valid parallel for duration
def test_parallel_invalid_duration():
    region = region_factory(RegionType.PARALLEL)
    region.duration = -3
    assert region_validator(region) is False 


'''
CHOICE
'''

#default choice
def test_choice_valid_default():
    region = region_factory(RegionType.CHOICE)
    assert region_validator(region) is True

#NOT valid choice for children number
def test_choice_invalid_childern_number():
    region = region_factory(RegionType.CHOICE)
    del region.children[1]
    assert region_validator(region) is False

# valid choice for children and distribution match
def test_choice_valid_childern_match():
    region = region_factory(RegionType.CHOICE)
    region.distribution = [0.8,0.2]
    assert region_validator(region) is True

#NOT valid choice for children and distribution match
def test_choice_invalid_childern_match():
    region = region_factory(RegionType.CHOICE)
    region.distribution = [0.8]
    assert region_validator(region) is False

#NOT valid choice for children and distribution sum >1
def test_choice_invalid_distribution_sum():
    region = region_factory(RegionType.CHOICE)
    region.distribution = [0.8,0.3]
    assert region_validator(region) is False

#NOT valid choice for children and distribution sum <1
def test_choice_invalid_distribution_sum_():
    region = region_factory(RegionType.CHOICE)
    region.distribution = [0.6,0.3]
    assert region_validator(region) is False

#NOT valid choice for impacts
def test_choice_invalid_impacts():
    region = region_factory(RegionType.CHOICE)
    region.impacts = [1,2,3]
    assert region_validator(region) is False




'''
NATURE
'''

#default nature
def test_nature_valid_default():
    region = region_factory(RegionType.NATURE)
    assert region_validator(region) is True

#NOT valid nature for children number
def test_nature_invalid_childern_number():
    region = region_factory(RegionType.NATURE)
    del region.children[1]
    assert region_validator(region) is False

# valid nature for children and distribution match
def test_nature_valid_childern_match():
    region = region_factory(RegionType.NATURE)
    region.distribution = [0.8,0.2]
    assert region_validator(region) is True

#NOT valid nature for children and distribution match
def test_nature_invalid_childern_match():
    region = region_factory(RegionType.NATURE)
    region.distribution = [0.8]
    assert region_validator(region) is False

#NOT valid nature for children and distribution sum >1
def test_nature_invalid_distribution_sum():
    region = region_factory(RegionType.NATURE)
    region.distribution = [0.8,0.3]
    assert region_validator(region) is False

#NOT valid nature for children and distribution sum <1
def test_nature_invalid_distribution_sum_():
    region = region_factory(RegionType.NATURE)
    region.distribution = [0.6,0.3]
    assert region_validator(region) is False

#NOT valid nature for impacts
def test_nature_invalid_impacts():
    region = region_factory(RegionType.NATURE)
    region.impacts = [1,2,3]
    assert region_validator(region) is False