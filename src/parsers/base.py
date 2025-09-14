# src/parsers/base.py
from abc import ABC, abstractmethod
from typing import List
from src.models.fei import FEIEvent

class IParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> List[FEIEvent]:
        """
        Lê um arquivo de log e o converte para uma lista de eventos no formato FEI.
        """
        pass