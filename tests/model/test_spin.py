import unittest
from src.model.time_spin import TimeMarking
from pm4py.objects.petri_net.obj import Marking


class TestTimeMarking(unittest.TestCase):

    def setUp(self):
        # Setup iniziale: crea una Marking di esempio
        self.marking = Marking({"a": 10, "b": 5, "c": 3})
        self.age = {"a": 1, "b": 2}

        # Crea un'istanza di TimeMarking
        self.time_marking = TimeMarking(self.marking, self.age)

    def tearDown(self):
        """Metodo per eliminare le variabili o ripristinare lo stato dopo ogni test"""
        del self.marking
        del self.age
        del self.time_marking

    def test_initialization(self):
        """Test per verificare la corretta inizializzazione della classe"""
        self.assertEqual(self.time_marking.marking, {"a": 10, "b": 5, "c": 3})
        self.assertEqual(
            self.time_marking.age, {"a": 1, "b": 2, "c": 0}
        )  # "c" ha un'età di 0, perché non è stato passato.
        self.assertEqual(self.time_marking.keys(), {"a", "b", "c"})

    def test_invalid_age_keys(self):
        """Test per verificare che venga sollevato un errore se le chiavi di 'age' non sono valide"""
        invalid_age = {"a": 1, "b": 2, "d": 4}  # "d" non è una chiave valida
        with self.assertRaises(ValueError):
            TimeMarking(self.marking, invalid_age)

    def test_getitem(self):
        """Test per verificare l'accesso agli elementi tramite __getitem__"""
        self.assertEqual(
            self.time_marking["a"], (10, 1)
        )  # Dovrebbe restituire il marking e l'età per 'a'
        self.assertEqual(
            self.time_marking["b"], (5, 2)
        )  # Dovrebbe restituire il marking e l'età per 'b'
        with self.assertRaises(KeyError):
            self.time_marking["d"]  # Chiave 'd' non presente

    def test_contains(self):
        """Test per verificare l'operatore __contains__"""
        self.assertIn("a", self.time_marking)
        self.assertNotIn("d", self.time_marking)

    def test_eq(self):
        """Test per verificare l'uguaglianza tra due oggetti TimeMarking"""
        # Crea un altro TimeMarking uguale
        other_time_marking = TimeMarking(self.marking, {"a": 1, "b": 2, "c": 0})

        # Verifica che i due oggetti siano uguali
        self.assertEqual(self.time_marking, other_time_marking)

        # Verifica che non siano più uguali se uno dei valori cambia
        # Nota che TimeMarking è immutabile, quindi non puoi modificarlo direttamente, ma dobbiamo testare
        # che non siano uguali se le chiavi o i valori cambiano.
        modified_age = {"a": 5, "b": 2, "c": 0}  # Cambiamo l'età di 'a'
        modified_time_marking = TimeMarking(self.marking, modified_age)

        self.assertNotEqual(self.time_marking, modified_time_marking)

    def test_immutability(self):
        """Test per verificare che non si possono cambiare i valori di TimeMarking"""
        # Verifica che non sia possibile modificare le proprietà dell'oggetto immutabile
        copy_marking = self.time_marking.marking
        copy_marking["a"] = 15

        self.assertNotEqual(copy_marking, self.time_marking.marking)

        copy_age = self.time_marking.age
        copy_age["a"] = 15

        self.assertNotEqual(copy_age, self.time_marking.age)
