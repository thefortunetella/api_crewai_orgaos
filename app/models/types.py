from typing import Dict, List, Optional, TypedDict

# --- Estruturas de Dados Tipadas (TypedDict) ---

class TokenResponse(TypedDict):
    access_token: str
    expires_in: int
    refresh_token: Optional[str]

class Veiculo(TypedDict):
    id: str
    plate: str
    model: str
    brandLogo: str

class ServiceCodeDataItem(TypedDict):
    serviceCode: str
    data: Dict[str, List[Veiculo]]

class AtualizarVeiculosPayload(TypedDict):
    source: str
    serviceCodesData: List[ServiceCodeDataItem]

class ReservaHorarioPayload(TypedDict):
    usuario: str
    servico: str
    data: str
    hora: str
    unidade: str
    nome_do_usuario: str

class SugestaoAgendamentoPayload(TypedDict):
    dataNascimento: Optional[str]
    servico: str
    cep: Optional[str]