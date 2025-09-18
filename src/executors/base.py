# src/executors/base.py
from abc import ABC, abstractmethod

class IExecutor(ABC):
    """
    Define o contrato para classes que executam uma carga de trabalho
    a partir de um rastro sintético em formato FEI e coletam métricas.
    """
    @abstractmethod
    def execute(self, synthetic_trace_path: str) -> None:
        pass