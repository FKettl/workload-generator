from abc import ABC, abstractmethod
from typing import List
from ..models.fei import FEIEvent


class ISaver(ABC):
    """
    Interface for the Saver strategy.
    """
    @abstractmethod
    def save(self, events: List[FEIEvent], output_path: str):
        pass