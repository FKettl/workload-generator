import re
import sys
from typing import List
from ...models.fei import FEIEvent
from ..base import IParser


class RedisParser(IParser):
    _LOG_LINE_REGEX = re.compile(r'^(\S+)\s+\[([^\]]+)\]\s+(.*)$')
    _ARGS_REGEX = re.compile(r'"([^"]*)"')

    def __init__(self, timestamp_granularity: int):
        self.timestamp_granularity = timestamp_granularity
        print(f"RedisParser initialized with timestamp granularity: {self.timestamp_granularity}")

    def _parse_line_to_fei(self, line: str) -> FEIEvent | None:
        match = self._LOG_LINE_REGEX.match(line.strip())
        if not match:
            return None

        try:
            timestamp_str, client_id, command_str = match.groups()
            timestamp = round(float(timestamp_str), self.timestamp_granularity)

            quoted_parts = self._ARGS_REGEX.findall(command_str)
            if not quoted_parts or len(quoted_parts) < 2:
                return None

            op_type = quoted_parts[0].upper()
            target = quoted_parts[1]
            additional_args = quoted_parts[2:]
            payload_size = sum(len(arg.encode('utf-8')) for arg in additional_args)
    
            return FEIEvent(
                timestamp=timestamp,
                client_id=client_id,
                op_type=op_type,
                target=target,
                tamanho_payload=payload_size,
                dados_adicionais={'raw_args': additional_args}
            )
        except (ValueError, IndexError):
            return None
            
    def parse(self, file_path: str) -> List[FEIEvent]:
        print(f"Using RedisParser to analyze '{file_path}'...")
        events = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                event = self._parse_line_to_fei(line)
                if event:
                    events.append(event)
                else:
                    print(f"[WARN] Line {line_num} ignored due to not matching expected format: {line.strip()}", file=sys.stderr)
        return events