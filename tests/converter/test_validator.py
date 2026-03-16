from converter.validator import region_validator
from model.region import RegionType
from tests.converter.region_factory import region_factory

"""
There is a regionFactory that creates valid regions; to avoid duplication, generate them from there and modify the fields of interest
"""

# VALIDATOR

"""
TASKS
"""


# INVALID: explore by id
def test_validator_valid():
    region = region_factory(RegionType.TASK)
    region.id = ""
    assert region_validator(region) is False


# VALID: task duration
def test_task_valid():
    region = region_factory(RegionType.TASK)
    region.duration = 5
    assert region_validator(region) is True


# INVALID: task duration
def test_task_invalid_duration():
    region = region_factory(RegionType.TASK)
    region.duration = -5
    assert region_validator(region) is False


# INVALID: different task impacts length
def test_task_invalid_impacts_length():
    parent = region_factory(RegionType.SEQUENTIAL)
    # by default the task has a 3-element impacts vector
    parent.children[1].impacts = [1, 2]
    assert region_validator(parent) is False


# VALID: matching task impacts length
def test_task_valid_impacts_length():
    region = region_factory(RegionType.SEQUENTIAL)
    assert region_validator(region) is True


# INVALID: impacts value < 0
def test_task_invalid_impacts_values():
    parent = region_factory(RegionType.SEQUENTIAL)
    parent.children[0].impacts = [0, 0, -1]
    assert region_validator(parent) is False


# INVALID: task with children
def test_task_invalid_has_children():
    parent = region_factory(RegionType.SEQUENTIAL)
    parent.children[0].children = region_factory(RegionType.TASK)
    assert region_validator(parent) is False


# INVALID: task with distribution
def test_task_invalid_with_distribution():
    parent = region_factory(RegionType.SEQUENTIAL)
    parent.children[0].distribution = [0.7, 0.2, 0.1]
    assert region_validator(parent) is False


"""
SEQUENTIAL
"""


# default sequential
def test_sequential_valid_with_children():
    region = region_factory(RegionType.SEQUENTIAL)
    assert region_validator(region) is True


# INVALID: sequential with fewer than 2 children
def test_sequential_invalid_with_children():
    parent = region_factory(RegionType.SEQUENTIAL)
    del parent.children[1]
    assert region_validator(parent) is False


# INVALID: sequential with impacts
def test_sequential_invalid_impacts():
    region = region_factory(RegionType.SEQUENTIAL)
    region.impacts = [1, 2, 3]
    assert region_validator(region) is False


# INVALID: sequential with probability distribution
def test_sequential_invalid_distribution():
    region = region_factory(RegionType.SEQUENTIAL)
    region.distribution = [0.2, 0.4, 0.4]
    assert region_validator(region) is False


"""
PARALLEL
"""


# default parallel
def test_parallel_valid_default():
    region = region_factory(RegionType.PARALLEL)
    assert region_validator(region) is True


# NOT valid parallel for children
def test_parallel_invalid_children():
    region = region_factory(RegionType.PARALLEL)
    del region.children[1]
    assert region_validator(region) is False


# NOT valid parallel for impacts
def test_parallel_invalid_distribution():
    region = region_factory(RegionType.PARALLEL)
    region.distribution = [1, 0, 0]
    assert region_validator(region) is False


# NOT valid parallel for duration
def test_parallel_invalid_duration():
    region = region_factory(RegionType.PARALLEL)
    region.duration = -3
    assert region_validator(region) is False


"""
CHOICE
"""


# default choice
def test_choice_valid_default():
    region = region_factory(RegionType.CHOICE)
    assert region_validator(region) is True


# NOT valid choice for children number
def test_choice_invalid_childern_number():
    region = region_factory(RegionType.CHOICE)
    del region.children[1]
    assert region_validator(region) is False


# valid choice for children and distribution match
def test_choice_valid_childern_match():
    region = region_factory(RegionType.CHOICE)
    region.distribution = [0.8, 0.2]
    assert region_validator(region) is True


# NOT valid choice for children and distribution match
def test_choice_invalid_childern_match():
    region = region_factory(RegionType.CHOICE)
    region.distribution = [0.8]
    assert region_validator(region) is False


# NOT valid choice for children and distribution sum >1
def test_choice_invalid_distribution_sum():
    region = region_factory(RegionType.CHOICE)
    region.distribution = [0.8, 0.3]
    assert region_validator(region) is False


# NOT valid choice for children and distribution sum <1
def test_choice_invalid_distribution_sum_():
    region = region_factory(RegionType.CHOICE)
    region.distribution = [0.6, 0.3]
    assert region_validator(region) is False


# NOT valid choice for impacts
def test_choice_invalid_impacts():
    region = region_factory(RegionType.CHOICE)
    region.impacts = [1, 2, 3]
    assert region_validator(region) is False


"""
NATURE
"""


# default nature
def test_nature_valid_default():
    region = region_factory(RegionType.NATURE)
    assert region_validator(region) is True


# NOT valid nature for children number
def test_nature_invalid_childern_number():
    region = region_factory(RegionType.NATURE)
    del region.children[1]
    assert region_validator(region) is False


# valid nature for children and distribution match
def test_nature_valid_childern_match():
    region = region_factory(RegionType.NATURE)
    region.distribution = [0.8, 0.2]
    assert region_validator(region) is True


# NOT valid nature for children and distribution match
def test_nature_invalid_childern_match():
    region = region_factory(RegionType.NATURE)
    region.distribution = [0.8]
    assert region_validator(region) is False


# NOT valid nature for children and distribution sum >1
def test_nature_invalid_distribution_sum():
    region = region_factory(RegionType.NATURE)
    region.distribution = [0.8, 0.3]
    assert region_validator(region) is False


# NOT valid nature for children and distribution sum <1
def test_nature_invalid_distribution_sum_():
    region = region_factory(RegionType.NATURE)
    region.distribution = [0.6, 0.3]
    assert region_validator(region) is False


# NOT valid nature for impacts
def test_nature_invalid_impacts():
    region = region_factory(RegionType.NATURE)
    region.impacts = [1, 2, 3]
    assert region_validator(region) is False
