# src/generators/base.py
from abc import ABC, abstractmethod

class IGenerator(ABC):
    """
    Define o contrato para classes que geram um log final
    a partir de um arquivo de eventos FEI.
    """
    @abstractmethod
    def generate(self, input_fei_path: str, output_log_path: str):
        pass