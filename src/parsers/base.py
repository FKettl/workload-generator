# src/parsers/base.py
from abc import ABC, abstractmethod
from typing import List
from src.models.fei import FEIEvent

# [cite_start]Interface Strategy, conforme a Figura 8 do TCC [cite: 983]
class IParser(ABC):
    """
    Define o contrato comum que todos os parsers (estratégias) devem seguir,
    [cite_start]conforme a interface IParser do TCC[cite: 983, 984].
    """
    @abstractmethod
    def parse(self, file_path: str) -> List[FEIEvent]:
        """
        Lê um arquivo de log e o converte para uma lista de eventos no formato FEI.
        """
        pass