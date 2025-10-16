from typing import List
from ..interfaces import IGenerator
from ...models.fei import FEIEvent


class ReplayGenerator(IGenerator):
    """
    A simple pass-through strategy that returns the input event list unchanged.
    """

    def generate(self, events: List[FEIEvent]) -> List[FEIEvent]:
        """
        Returns the input list of events without modification.

        Args:
            events: The list of input FEIEvent objects.

        Returns:
            The same list of FEIEvent objects.
        """
        print(f"ReplayGenerator: Passing through {len(events)} events.")
        return events