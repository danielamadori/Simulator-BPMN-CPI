from typing import List
from model.spin import DataMarking


class History:
    __backtrack: List[DataMarking] = property(fget=None, fset=None, fdel=None)
    __forward: List[DataMarking] = property(fget=None, fset=None, fdel=None)

    def __init__(self, initial_marking: DataMarking):
        self.__backtrack = [initial_marking]
        self.__forward = []

    def get_current_state(self) -> DataMarking:
        return self.__backtrack[len(self.__backtrack) - 1]

    def __can_backtrack(self) -> bool:
        return len(self.__backtrack) > 1

    def __can_forward(self) -> bool:
        return len(self.__forward) > 0

    def backtrack(self) -> DataMarking:
        if not self.__can_backtrack():
            return self.get_current_state()

        tmp = self.__backtrack.pop()
        self.__forward.append(tmp)

        return self.get_current_state()

    def forward(self) -> DataMarking:
        if not self.__can_forward():
            return self.get_current_state()

        tmp = self.__forward.pop()
        self.__backtrack.append(tmp)

        return self.get_current_state()

    def save(self, marking: DataMarking) -> None:
        self.__forward.clear()
        self.__backtrack.append(marking)
