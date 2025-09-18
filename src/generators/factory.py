# src/generators/factory.py
from typing import Dict, Any
from .base import IGenerator
from .replay_generator import ReplayGenerator
#from .statistical_generator import StatisticalGenerator

class GeneratorFactory:
    """Fábrica responsável apenas pela criação de Geradores."""
    def create_generator(self, config: Dict[str, Any]) -> IGenerator:
        generator_type = config.get('type')
        if generator_type == 'replay':
            return ReplayGenerator()
        elif generator_type == 'statistical':
            num_events = config.get('num_events_to_generate', 1000)
            #return StatisticalGenerator(num_events_to_generate=num_events)
        raise ValueError(f"Generator do tipo '{generator_type}' não é suportado.")