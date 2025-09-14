# src/factories.py
from src.parsers.base import IParser
from src.parsers.redis_parser import RedisParser
from src.savers.base import ISaver
from src.savers.json_saver import JsonSaver
from src.generators.base import IGenerator
from src.generators.replay_generator import ReplayGenerator
from typing import Dict, Any

class ParserFactory:
    """Fábrica responsável apenas pela criação de Parsers."""
    def create_parser(self, config: Dict[str, Any]) -> IParser:
        parser_type = config.get('type')
        if parser_type == 'redis':
            # Passa a granularidade do config para o construtor do parser
            granularity = config.get('timestamp_granularity', 6) # Default de 6 se não especificado
            return RedisParser(timestamp_granularity=granularity)
        raise ValueError(f"Parser do tipo '{parser_type}' não é suportado.")

class SaverFactory:
    # ... (sem mudanças)
    def create_saver(self, saver_type: str) -> ISaver:
        if saver_type == 'json':
            return JsonSaver()
        raise ValueError(f"Saver do tipo '{saver_type}' não é suportado.")

class GeneratorFactory:
    # ... (sem mudanças)
    def create_generator(self, generator_type: str) -> IGenerator:
        if generator_type == 'replay':
            return ReplayGenerator()
        raise ValueError(f"Generator do tipo '{generator_type}' não é suportado.")