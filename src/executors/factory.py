# src/executors/factory.py
from typing import Dict, Any
from .base import IExecutor
from .redis_executor import RedisExecutor

class ExecutorFactory:
    """Fábrica responsável pela criação de Executores."""
    def create_executor(self, config: Dict[str, Any]) -> IExecutor:
        executor_type = config.get('type')
        if executor_type == 'redis':
            host = config.get('host', 'localhost')
            port = config.get('port', 6379)
            max_workers = config.get('max_workers', 1)
            return RedisExecutor(host=host, port=port, max_workers=max_workers)
        raise ValueError(f"Executor do tipo '{executor_type}' não é suportado.")