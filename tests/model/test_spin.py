import pytest

from model.context import NetContext
from model.petri_net.time_spin import TimeMarking
from pm4py.objects.petri_net.obj import Marking

@pytest.fixture
def region_model():
    """Fixture per caricare il modello di regione"""
    with open("tests/input_data/bpmn_nature.json") as f:
        from model.region import RegionModel
        model = RegionModel.model_validate_json(f.read())
    return model

@pytest.fixture
def ctx(region_model):
    context = NetContext.from_region(region_model)
    return context

@pytest.fixture
def marking():
    _marking = Marking({"a": 10, "b": 5, "c": 3, "d": 0})
    yield _marking
    del _marking


@pytest.fixture
def time_marking(marking):
    age = {"a": 1, "b": 2}
    t_m = TimeMarking(marking, age)

    yield t_m

    del t_m
    del age


class TestTimeMarking:

    def test_initialization(self, time_marking):
        """Test per verificare la corretta inizializzazione della classe"""
        assert time_marking.marking == {"a": 10, "b": 5, "c": 3, "d": 0}
        assert time_marking.age == {"a": 1, "b": 2, "c": 0, "d": 0}
        assert time_marking.keys() == {"a", "b", "c", "d"}

    def test_invalid_age_keys(self, time_marking):
        """Test per verificare che venga sollevato un errore se le chiavi di 'age' non sono valide"""
        invalid_age = {"a": 1, "b": 2, "e": 4}
        with pytest.raises(ValueError):
            TimeMarking(time_marking.marking, invalid_age)

    def test_getitem(self, time_marking):
        """Test per verificare l'accesso agli elementi tramite __getitem__"""
        assert time_marking["a"] == (10, 1)
        assert time_marking["b"] == (5, 2)
        with pytest.raises(KeyError):
            time_marking["e"]

    def test_contains(self, ctx, time_marking):
        """Test per verificare l'operatore __contains__"""
        places = list(ctx.net.places)

        assert places[0].name in ctx.initial_marking
        assert places[0] in ctx.initial_marking
        assert "-489651" not in ctx.initial_marking

    def test_eq(self, time_marking):
        """Test per verificare l'uguaglianza tra due oggetti TimeMarking"""
        # Crea un altro TimeMarking uguale
        marking = time_marking.marking
        other_time_marking = TimeMarking(marking, {"a": 1, "b": 2, "c": 0, "d": 0})

        # Verifica che i due oggetti siano uguali
        # self.assertEqual(self.time_marking, other_time_marking)
        assert time_marking == other_time_marking

        # Verifica che non siano più uguali se uno dei valori cambia
        # Nota che TimeMarking è immutabile, quindi non puoi modificarlo direttamente, ma dobbiamo testare
        # che non siano uguali se le chiavi o i valori cambiano.
        modified_age = {"a": 5, "b": 2, "c": 0, "d": 0}
        modified_time_marking = TimeMarking(marking, modified_age)

        assert time_marking != modified_time_marking

    def test_immutability(self, time_marking):
        """Test per verificare che non si possono cambiare i valori di TimeMarking"""
        copy_marking = time_marking.marking
        copy_marking["a"] = 15

        assert copy_marking != time_marking.marking

        copy_age = time_marking.age
        copy_age["a"] = 15

        assert copy_age != time_marking.age

        copy_keys = time_marking.keys()
        copy_keys.add("dd")

        assert copy_keys != time_marking.keys()

    def test_add_time(self, time_marking):
        im = time_marking
        time_added = 1.0
        new_marking = im.add_time(time_added)

        tmp = im.age
        first_key_not_active = None
        for k in tmp:
            if im.marking[k] > 0:
                tmp[k] += time_added
            else:
                first_key_not_active = k
                tmp[k] = 0
        assert new_marking.age == tmp, "Age should be updated correctly after adding time"
        assert new_marking.age[first_key_not_active] == 0, "Age for inactive places should be set to 0"
