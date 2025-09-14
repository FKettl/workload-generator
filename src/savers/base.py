# src/savers/base.py
from abc import ABC, abstractmethod
from typing import List
from src.models.fei import FEIEvent

class ISaver(ABC):
    """
    Define o contrato para classes que salvam eventos FEI em um arquivo.
    """
    @abstractmethod
    def save(self, events: List[FEIEvent], output_path: str):
        pass