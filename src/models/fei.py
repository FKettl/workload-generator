from typing import TypedDict, List, Any, Dict


class FEIEvent(TypedDict):
    """
    Define the structure of the FEI event.
    """
    timestamp: float
    op_type: str
    client_id: str
    target: str
    payload_size: int
    additional_args: Dict[str, Any]