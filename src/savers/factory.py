# src/savers/factory.py
from typing import Dict, Any
from .base import ISaver
from .json_saver import JsonSaver

class SaverFactory:
    """Fábrica responsável apenas pela criação de Savers."""
    def create_saver(self, config: Dict[str, Any]) -> ISaver:
        saver_type = config.get('type')
        if saver_type == 'json':
            return JsonSaver()
        raise ValueError(f"Saver do tipo '{saver_type}' não é suportado.")