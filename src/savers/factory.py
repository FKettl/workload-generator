from typing import Dict, Any
from .base import ISaver


class SaverFactory:
    """
    Factory for creating Saver instances.
    """
    def create_saver(self, config: Dict[str, Any]) -> ISaver:
        saver_type = config.get('type')
        if saver_type == 'json':
            from .json.json_saver import JsonSaver
            return JsonSaver()
        raise ValueError(f"Saver type: '{saver_type}' is not supported.")