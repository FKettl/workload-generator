# src/savers/json_saver.py
import json
from typing import List
from src.models.fei import FEIEvent
from src.savers.base import ISaver

class JsonSaver(ISaver):
    """
    Salva uma lista de eventos FEI em um arquivo no formato JSON.
    """
    def save(self, events: List[FEIEvent], output_path: str):
        print(f"Usando JsonSaver para salvar {len(events)} eventos em '{output_path}'...")
        with open(output_path, 'w', encoding='utf-8') as f:
            # O indent=4 formata o JSON para ser legível por humanos
            json.dump(events, f, indent=4)