from typing import Dict, Any, List, Optional
from .base import BaseApiClient
from app.models.types import Veiculo, AtualizarVeiculosPayload

# Constantes específicas do DETRAN
SCOPE_DETRAN_VEHICLES = 'detran_vehicles'
SOURCE_DETRAN = 'DETRAN'
SERVICE_CODE_MEUS_VEICULOS = 'meusVeiculos'
HEADER_AUTH = 'Authorization'

class DetranClient(BaseApiClient):
    """Cliente para APIs do DETRAN."""
    
    def _get_auth_header(self, token: str) -> Dict[str, str]:
        """Retorna headers com autenticação Bearer."""
        headers = self._get_basic_headers()
        headers[HEADER_AUTH] = f'Bearer {token}'
        return headers

    def get_vehicles(self, cpf: str) -> Dict[str, Any]:
        """Busca veículos registrados no DETRAN para um CPF."""
        system_token = self.auth_manager.get_system_token(scope=SCOPE_DETRAN_VEHICLES)
        
        if not system_token:
            return {
                "error": "Authentication Error",
                "message": "Token de sistema para DETRAN não obtido."
            }
        
        headers = self._get_auth_header(system_token)
        params = {'cpfAcessoCidadao': self._clean_cpf(cpf)}
        endpoint = f"{self.base_url}/api/portalinteligente/veiculo/v1/obter"
        
        return self._make_request("get", endpoint, headers=headers, params=params)

    def fetch_user_profile(self, user_id: str, 
                          user_token_override: Optional[str] = None) -> Dict[str, Any]:
        """Busca o perfil completo de um cidadão."""
        user_token = user_token_override or self.auth_manager.get_user_token(user_id)
        
        if not user_token:
            return {
                "error": "Authentication Error",
                "message": f"Token de usuário para DETRAN (user_id: {user_id}) não obtido."
            }
        
        headers = self._get_auth_header(user_token)
        endpoint = f"{self.base_url}/v1/profile"
        
        return self._make_request("get", endpoint, headers=headers)

    def atualizar_veiculos(self, user_id: str, veiculos: List[Veiculo], 
                          user_token_override: Optional[str] = None) -> Dict[str, Any]:
        """Atualiza a lista de veículos no perfil de um cidadão."""
        user_token = user_token_override or self.auth_manager.get_user_token(user_id)
        
        if not user_token:
            return {
                "error": "Authentication Error",
                "message": f"Token de usuário para DETRAN (user_id: {user_id}) não obtido."
            }
        
        headers = self._get_auth_header(user_token)
        
        payload: AtualizarVeiculosPayload = {
            "source": SOURCE_DETRAN,
            "serviceCodesData": [
                {
                    "serviceCode": SERVICE_CODE_MEUS_VEICULOS,
                    "data": {"veiculos": veiculos}
                }
            ]
        }
        
        endpoint = f"{self.base_url}/v1/profile/external-data"
        
        return self._make_request("patch", endpoint, headers=headers, json=payload)