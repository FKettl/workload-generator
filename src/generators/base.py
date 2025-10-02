from abc import ABC, abstractmethod


class IGenerator(ABC):
    """
    Define the interface for the Generator strategy.
    """
    @abstractmethod
    def generate(self, input_fei_path: str, output_log_path: str):
        pass