from types import N, P, T, M
from model.time_spin import TimeMarking


# Snapshot è la struttura del nodo dell'albero
class Snapshot:
    marking: TimeMarking
    probability: float
    impacts: list[float]
    exec_time: float

    def __init__(
        self,
        marking: TimeMarking,
        probability: float,
        impacts: list[float],
        time: float,
    ):
        self.marking = marking
        self.probability = probability
        self.impacts = impacts
        self.exec_time = time

    def get_marking(self):
        return self.marking

    def get_probability(self):
        return self.probability

    def get_impacts(self):
        return self.impacts

    def get_time(self):
        return self.exec_time
