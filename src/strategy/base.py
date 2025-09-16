#  Copyright (c) 2025.
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from model.types import ContextType, MarkingType, TransitionType


class StrategyProto(Protocol):

    def saturate(self, ctx: ContextType, marking: MarkingType):
        """Saturate the Petri net based on the current marking."""
        raise NotImplementedError

    def consume(self, ctx: ContextType, marking: MarkingType, choices: list[TransitionType] | None = None):
        """Consume the Petri net based on the current marking and choices."""
        raise NotImplementedError
