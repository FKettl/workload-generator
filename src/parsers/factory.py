# src/parsers/factory.py
from typing import Dict, Any
from .base import IParser
from .redis_parser import RedisParser

class ParserFactory:
    """Fábrica responsável apenas pela criação de Parsers."""
    def create_parser(self, config: Dict[str, Any]) -> IParser:
        parser_type = config.get('type')
        if parser_type == 'redis':
            granularity = config.get('timestamp_granularity', 6)
            return RedisParser(timestamp_granularity=granularity)
        raise ValueError(f"Parser do tipo '{parser_type}' não é suportado.")