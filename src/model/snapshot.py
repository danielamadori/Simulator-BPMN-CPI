from model.time_spin import TimeMarking

'''
Secondo me si può spostare anche dentro extree
'''


# Snapshot è la struttura del nodo dell'albero
class Snapshot:
    marking: TimeMarking
    probability: float
    impacts: list[float]
    exec_time: float

    def __init__(self, marking: TimeMarking, probability: float, impacts: list[float], time: float):
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

    def __eq__(self, other):
        if not isinstance(other, Snapshot):
            return False

        if other.marking != self.marking:
            return False
        if other.impacts != self.impacts:
            return False
        if other.probability != self.probability:
            return False
        if other.exec_time != self.exec_time:
            return False

        return True
