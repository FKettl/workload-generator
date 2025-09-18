# src/models/fei.py
from typing import TypedDict, List, Any, Dict

class FEIEvent(TypedDict):
    """
    Define a estrutura do Formato de Evento Intermediário (FEI), 
    conforme especificado na Seção 4.3 do TCC.
    """
    timestamp: float
    tipo_operacao: str
    client_id: str
    recurso_alvo: str
    tamanho_payload: int
    dados_adicionais: Dict[str, Any]