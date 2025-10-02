import json
from typing import List
from ...models.fei import FEIEvent
from ..base import ISaver

class JsonSaver(ISaver):
    """
    Save all FEI events in a JSON format
    """
    def save(self, events: List[FEIEvent], output_path: str):
        print(f"Using JsonSaver to save {len(events)} events to '{output_path}'...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(events, f)