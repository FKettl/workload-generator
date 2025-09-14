# src/config_loader.py
import yaml
from typing import Dict, Any

def load_config(path: str = 'config.yaml') -> Dict[str, Any]:
    """
    Carrega e analisa um arquivo de configuração no formato YAML.
    """
    print(f"Carregando configurações de '{path}'...")
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config