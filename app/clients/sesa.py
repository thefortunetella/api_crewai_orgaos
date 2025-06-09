from typing import Dict, Any, Optional
from .base import BaseApiClient
from app.models.types import SugestaoAgendamentoPayload, ReservaHorarioPayload

HEADER_AUTH = 'Authorization'

class SesaClient(BaseApiClient):
    """Cliente para APIs da SESA."""
    
    def _get_auth_headers(self, user_token: Optional[str] = None) -> Dict[str, str]:
        """Retorna headers com autenticação opcional."""
        headers = self._get_basic_headers()
        if user_token:
            headers[HEADER_AUTH] = f'Bearer {user_token}'
        return headers

    def get_municipios(self) -> Dict[str, Any]:
        """Lista todos os municípios disponíveis para agendamento."""
        endpoint = f"{self.base_url}/api/agendamento/municipios"
        return self._make_request("get", endpoint, headers=self._get_auth_headers())

    def get_servicos(self) -> Dict[str, Any]:
        """Lista todos os serviços disponíveis para agendamento."""
        endpoint = f"{self.base_url}/api/agendamento/servicos"
        return self._make_request("get", endpoint, headers=self._get_auth_headers())

    def get_unidades(self, municipio_id: str, servico_id: str) -> Dict[str, Any]:
        """Lista unidades de atendimento baseado no município e serviço."""
        params = {
            'municipio_id': municipio_id,
            'servico_id': servico_id
        }
        endpoint = f"{self.base_url}/api/agendamento/unidades"
        return self._make_request("get", endpoint, headers=self._get_auth_headers(), params=params)
    
    def get_horarios(self, unidade_id: str, data: str) -> Dict[str, Any]:
        """Consulta horários disponíveis para uma unidade em uma data."""
        params = {
            'unidade': unidade_id,
            'data': data
        }
        endpoint = f"{self.base_url}/api/agendamento/horarios-disponiveis"
        return self._make_request("get", endpoint, headers=self._get_auth_headers(), params=params)

    def get_sugestao_agendamento(self, payload: SugestaoAgendamentoPayload) -> Dict[str, Any]:
        """Obtém sugestões de agendamento."""
        endpoint = f"{self.base_url}/api/agendamento/sugestao-agendamento"
        return self._make_request("post", endpoint, headers=self._get_auth_headers(), json=payload)
    
    def reservar_horario(self, payload: ReservaHorarioPayload, user_id: str, 
                        user_token_override: Optional[str] = None) -> Dict[str, Any]:
        """Realiza uma reserva de horário."""
        user_token = user_token_override or self.auth_manager.get_user_token(user_id)
        
        if not user_token:
            return {
                "error": "Authentication Error",
                "message": "A reserva requer autenticação de usuário."
            }
        
        endpoint = f"{self.base_url}/api/agendamento/reservar"
        return self._make_request("post", endpoint, headers=self._get_auth_headers(user_token), json=payload)
    
    def check_agendamento_existente(self, servico_id: str, user_id: str, ativo: bool, 
                                   user_token_override: Optional[str] = None) -> Dict[str, Any]:
        """Verifica agendamentos existentes para um usuário."""
        user_token = user_token_override or self.auth_manager.get_user_token(user_id)
        
        if not user_token:
            return {
                "error": "Authentication Error",
                "message": "A verificação de agendamentos requer autenticação de usuário."
            }
        
        params = {
            'servico': servico_id,
            'ativo': str(ativo).lower()
        }
        endpoint = f"{self.base_url}/api/agendamento/meus-agendamentos"
        return self._make_request("get", endpoint, headers=self._get_auth_headers(user_token), params=params)

    def cancelar_agendamento(self, agendamento_id: int, user_id: str, 
                            user_token_override: Optional[str] = None) -> Dict[str, Any]:
        """Cancela um agendamento existente."""
        user_token = user_token_override or self.auth_manager.get_user_token(user_id)
        
        if not user_token:
            return {
                "error": "Authentication Error",
                "message": "O cancelamento de agendamento requer autenticação de usuário."
            }
        
        endpoint = f"{self.base_url}/api/agendamento/meus-agendamentos/{agendamento_id}/cancelar"
        return self._make_request("post", endpoint, headers=self._get_auth_headers(user_token))