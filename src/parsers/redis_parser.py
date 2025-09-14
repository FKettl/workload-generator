# src/parsers/redis_parser.py
import re
from typing import List
from src.models.fei import FEIEvent
from src.parsers.base import IParser

class RedisParser(IParser):
    _ARGS_REGEX = re.compile(r'"([^"]*)"')

    def __init__(self, timestamp_granularity: int):
        """
        Inicializa o parser com a granularidade desejada para o timestamp.
        """
        self.timestamp_granularity = timestamp_granularity
        print(f"RedisMonitorParser inicializado com granularidade de timestamp: {self.timestamp_granularity}")

    def _parse_line_to_fei(self, line: str) -> FEIEvent | None:
        # ... (código interno da função)
        try:
            timestamp_str = line.strip().split(' ', 1)[0]
            timestamp_float = float(timestamp_str)
            
            # --- LÓGICA DA GRANULARIDADE APLICADA AQUI ---
            timestamp = round(timestamp_float, self.timestamp_granularity)
            
            # ... (resto da lógica para extrair op, alvo, etc.)
            # (O código abaixo está resumido para focar na mudança)
            rest_of_line = line.strip().split(' ', 1)[1]
            quoted_parts = self._ARGS_REGEX.findall(rest_of_line)
            tipo_operacao = quoted_parts[0].upper()
            recurso_alvo = quoted_parts[1]
            additional_args = quoted_parts[2:]
            payload_size = sum(len(arg.encode('utf-8')) for arg in additional_args)

            return FEIEvent(
                timestamp=timestamp,
                tipo_operacao=tipo_operacao,
                recurso_alvo=recurso_alvo,
                tamanho_payload=payload_size,
                dados_adicionais={'raw_args': additional_args}
            )
        except (ValueError, IndexError):
            return None
            
    def parse(self, file_path: str) -> List[FEIEvent]:
        # ... (código da função parse continua o mesmo)
        print(f"Usando o RedisMonitorParser para analisar '{file_path}'...")
        events = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                event = self._parse_line_to_fei(line)
                if event:
                    events.append(event)
        return events