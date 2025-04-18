import pytest
from src.model.time_spin import TimeMarking
from pm4py.objects.petri_net.obj import Marking


@pytest.fixture
def marking():
    _marking = Marking({"a": 10, "b": 5, "c": 3})
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
        assert time_marking.marking == {"a": 10, "b": 5, "c": 3}
        assert time_marking.age == {"a": 1, "b": 2, "c": 0}
        assert time_marking.keys() == {"a", "b", "c"}

    def test_invalid_age_keys(self, time_marking):
        """Test per verificare che venga sollevato un errore se le chiavi di 'age' non sono valide"""
        invalid_age = {"a": 1, "b": 2, "d": 4}
        with pytest.raises(ValueError):
            TimeMarking(time_marking.marking, invalid_age)

    def test_getitem(self, time_marking):
        """Test per verificare l'accesso agli elementi tramite __getitem__"""
        assert time_marking["a"] == (10, 1)
        assert time_marking["b"] == (5, 2)
        with pytest.raises(KeyError):
            time_marking["d"]

    def test_contains(self, time_marking):
        """Test per verificare l'operatore __contains__"""
        assert "a" in time_marking
        assert "d" not in time_marking

    def test_eq(self, time_marking):
        """Test per verificare l'uguaglianza tra due oggetti TimeMarking"""
        # Crea un altro TimeMarking uguale
        marking = time_marking.marking
        other_time_marking = TimeMarking(marking, {"a": 1, "b": 2, "c": 0})

        # Verifica che i due oggetti siano uguali
        # self.assertEqual(self.time_marking, other_time_marking)
        assert time_marking == other_time_marking

        # Verifica che non siano più uguali se uno dei valori cambia
        # Nota che TimeMarking è immutabile, quindi non puoi modificarlo direttamente, ma dobbiamo testare
        # che non siano uguali se le chiavi o i valori cambiano.
        modified_age = {"a": 5, "b": 2, "c": 0}
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
