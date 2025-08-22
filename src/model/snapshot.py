from copy import copy

from model.petri_net.time_spin import TimeMarking

'''
Secondo me si può spostare anche dentro extree
'''


# Snapshot è la struttura del nodo dell'albero
class Snapshot:
    __marking: TimeMarking
    __probability: float
    __impacts: list[float]
    __exec_time: float

    def __init__(self, marking: TimeMarking, probability: float, impacts: list[float], time: float):
        self.__marking = marking
        self.__probability = probability
        self.__impacts = impacts
        self.__exec_time = time

    @property
    def marking(self):
        return copy(self.__marking)

    @property
    def probability(self):
        return self.__probability

    @property
    def impacts(self):
        return copy(self.__impacts)

    @property
    def execution_time(self):
        return self.__exec_time

    def __eq__(self, other):
        if not isinstance(other, Snapshot):
            return False

        if other.__marking != self.__marking:
            return False
        if other.__impacts != self.__impacts:
            return False
        if other.__probability != self.__probability:
            return False
        if other.__exec_time != self.__exec_time:
            return False

        return True
