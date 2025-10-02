from typing import Dict, Any
from .base import IGenerator


class GeneratorFactory:
    """
    Factory responsible for creating Generator instances.
    """
    def create_generator(self, config: Dict[str, Any]) -> IGenerator:
        generator_type = config.get('type')
        if generator_type == 'replay':
            from .replay.replay_generator import ReplayGenerator
            return ReplayGenerator()
        #elif generator_type == 'statistical':
            #num_events = config.get('num_events_to_generate', 1000)
            #return StatisticalGenerator(num_events_to_generate=num_events)
        raise ValueError(f"Generator of type '{generator_type}' is not supported.")