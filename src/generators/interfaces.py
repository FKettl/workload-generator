from abc import ABC, abstractmethod
from typing import List
from ..models.fei import FEIEvent


class IGenerator(ABC):
    """
    Interface for strategies that transform a list of FEI events into a new
    list of synthetic FEI events.
    """

    @abstractmethod
    def generate(self, events: List[FEIEvent]) -> List[FEIEvent]:
        """
        Takes a list of events and returns a new, synthetic list of events.

        Args:
            events: A list of input FEIEvent objects from the parsing stage.

        Returns:
            A new list of synthetically generated FEIEvent objects.
        """
        pass