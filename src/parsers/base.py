from abc import ABC, abstractmethod
from typing import List
from ..models.fei  import FEIEvent


class IParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> List[FEIEvent]:
        """
        Read a log file and convert it to a list of events in the FEI format.
        """
        pass